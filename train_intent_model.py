# file: train_intent_model.py
# (Lưu file này ở thư mục gốc VoiceAI/)

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)
from sklearn.metrics import accuracy_score
import pandas as pd
from sklearn.model_selection import train_test_split
import os

# --- 1. DỮ LIỆU (DATASET) ---
data = {
    "text": [
        "Tôi muốn đặt một cái lịch hẹn",
        "Cho tôi hẹn vào 9h sáng mai",
        "Tôi có thể đặt lịch được không?",
        "Xin chào, tôi muốn hỏi thông tin",
        "Sản phẩm này giá bao nhiêu?",
        "Tôi không hiểu", "Nói lại đi",
        "Cảm ơn", "Tuyệt vời",
        "Tạm biệt", "Kết thúc đi"
    ],
    "label": [
        "dat_lich", "dat_lich", "dat_lich",
        "hoi_thong_tin", "hoi_thong_tin",
        "unknown", "unknown",
        "cam_on", "cam_on",
        "tam_biet", "tam_biet"
    ]
}
df = pd.DataFrame(data)

labels = df['label'].unique().tolist()
label2id = {label: i for i, label in enumerate(labels)}
id2label = {i: label for i, label in enumerate(labels)}
df['label'] = df['label'].map(label2id)

print(f"Cac intent tim thay: {label2id}")

# --- 2. Chuẩn bị DataLoader ---
train_texts, val_texts, train_labels, val_labels = train_test_split(
    df['text'].tolist(), df['label'].tolist(), test_size=0.2, random_state=42
)

model_name = "vinai/phobert-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)

train_encodings = tokenizer(train_texts, truncation=True, padding=True)
val_encodings = tokenizer(val_texts, truncation=True, padding=True)

class VietDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item
    def __len__(self):
        return len(self.labels)

train_dataset = VietDataset(train_encodings, train_labels)
val_dataset = VietDataset(val_encodings, val_labels)

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    return {'accuracy': acc}

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=len(labels),
    id2label=id2label,
    label2id=label2id
)

training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=15,
    # ...
    logging_steps=1,
    eval_strategy="epoch", # <-- SỬA THÀNH DÒNG NÀY
    save_strategy="epoch",
    load_best_model_at_end=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
)

print("--- BAT DAU HUAN LUYEN MODEL INTENT ---")
trainer.train()
print("--- HUAN LUYEN HOAN TAT ---")

output_model_dir = "./models/phobert-intent-classifier"
if not os.path.exists(output_model_dir):
    os.makedirs(output_model_dir)
    
trainer.save_model(output_model_dir)
tokenizer.save_pretrained(output_model_dir)
print(f"Model da duoc luu vao: {output_model_dir}")