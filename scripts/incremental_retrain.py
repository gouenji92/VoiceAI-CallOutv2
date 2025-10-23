"""
Simple incremental retrain script:
- loads `data/original_dataset.csv` and `data/feedback.csv` (if exists)
- appends feedback to dataset
- does a short fine-tune on classifier head (by freezing base if requested)
- saves updated model to `./models/phobert-intent-classifier`

This is intentionally minimal; for production you should add batching, checkpoints, and validation.
"""
import os
import pandas as pd
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
    AutoConfig,
)

ORIG = 'data/original_dataset.csv'
FEED = 'data/feedback.csv'
MODEL_DIR = './models/phobert-intent-classifier'

# Load data
orig = pd.read_csv(ORIG)
if os.path.exists(FEED):
    fb = pd.read_csv(FEED, names=['text','label'])
    if not fb.empty:
        print(f'Found {len(fb)} feedback rows, appending to dataset.')
        orig = pd.concat([orig, fb], ignore_index=True)
else:
    print('No feedback file found, using original dataset only.')

# Map labels
labels = orig['label'].unique().tolist()
label2id = {l:i for i,l in enumerate(labels)}
id2label = {i:l for l,i in label2id.items()}
orig['label_id'] = orig['label'].map(label2id)

# Tokenize
model_name = 'vinai/phobert-base'
tokenizer = AutoTokenizer.from_pretrained(model_name)
enc = tokenizer(orig['text'].tolist(), truncation=True, padding=True, max_length=128)

class SimpleDataset(torch.utils.data.Dataset):
    def __init__(self, enc, labels):
        self.enc = enc
        self.labels = labels
    def __len__(self):
        return len(self.labels)
    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k,v in self.enc.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

dataset = SimpleDataset(enc, orig['label_id'].tolist())

# Load model
config = AutoConfig.from_pretrained(model_name, num_labels=len(labels), id2label=id2label, label2id=label2id)
model = AutoModelForSequenceClassification.from_pretrained(model_name, config=config)

# Freeze base model parameters to do lightweight head-only fine-tune
for name, param in model.named_parameters():
    if 'classifier' not in name:
        param.requires_grad = False

# Trainer
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
args = TrainingArguments(
    output_dir=MODEL_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=8,
    learning_rate=1e-4,
    weight_decay=0.01,
    logging_dir='./logs',
    save_strategy='no'
)
trainer = Trainer(model=model, args=args, train_dataset=dataset, data_collator=data_collator)

print('Starting incremental training (head-only)')
trainer.train()

# Save model
os.makedirs(MODEL_DIR, exist_ok=True)
trainer.save_model(MODEL_DIR)
print('Incremental retrain finished and model saved.')
try:
    # Notify local API to reload the model
    import requests
    resp = requests.post('http://127.0.0.1:8000/api/feedback/reload')
    if resp.ok:
        print('Notified API to reload model successfully.')
    else:
        print('API reload notification returned:', resp.status_code, resp.text)
except Exception as e:
    print('Could not notify API to reload model:', e)
