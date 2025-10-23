"""
Quick Retrain Model V3 với Augmented Dataset V2
Dùng cho 3 intents yếu: yeu_cau_ho_tro, tu_choi, khieu_nai
"""

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

class IntentDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
    
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item
    
    def __len__(self):
        return len(self.labels)

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    return {'accuracy': acc}

print("=" * 70)
print("RETRAIN MODEL V3 - AUGMENTED DATASET V2")
print("=" * 70)

# 1. Load augmented dataset
print("\n[1] Loading augmented dataset v2...")
df = pd.read_csv('data/extended_dataset_v2.csv')
print(f"Total samples: {len(df)}")
print("\nSamples per intent:")
print(df['label'].value_counts().sort_index())

# Check weak intents improvement
weak_intents = ['yeu_cau_ho_tro', 'tu_choi', 'khieu_nai']
print("\n[*] Weak intents after augmentation:")
for intent in weak_intents:
    count = (df['label'] == intent).sum()
    print(f"  {intent}: {count} samples (+25 from baseline)")

# 2. Prepare label mapping
print("\n[2] Creating label mapping...")
labels = sorted(df['label'].unique())
label2id = {label: i for i, label in enumerate(labels)}
id2label = {i: label for label, i in label2id.items()}
print(f"Number of classes: {len(labels)}")
print(f"Labels: {labels}")

# Encode labels
df['label_id'] = df['label'].map(label2id)

# 3. Train/val split (90/10)
from sklearn.model_selection import train_test_split
train_df, val_df = train_test_split(
    df, 
    test_size=0.1, 
    stratify=df['label_id'],
    random_state=42
)
print(f"\nTrain samples: {len(train_df)}")
print(f"Val samples: {len(val_df)}")

# 4. Load tokenizer from existing v3 model
print("\n[3] Loading tokenizer from phobert-intent-v3/final...")
base_model_path = 'models/phobert-intent-v3/final'
tokenizer = AutoTokenizer.from_pretrained(base_model_path)

# Tokenize
print("[4] Tokenizing...")
train_encodings = tokenizer(
    train_df['text'].tolist(),
    truncation=True,
    padding=True,
    max_length=128,
    return_tensors='pt'
)
val_encodings = tokenizer(
    val_df['text'].tolist(),
    truncation=True,
    padding=True,
    max_length=128,
    return_tensors='pt'
)

train_dataset = IntentDataset(train_encodings, train_df['label_id'].tolist())
val_dataset = IntentDataset(val_encodings, val_df['label_id'].tolist())

# 5. Load base model and update config
print("[5] Loading base model...")
model = AutoModelForSequenceClassification.from_pretrained(
    base_model_path,
    num_labels=len(labels),
    id2label=id2label,
    label2id=label2id,
    ignore_mismatched_sizes=False  # Should match since same 11 intents
)

# 6. Training arguments (quick fine-tune)
output_dir = f"models/phobert-intent-v3-retrain-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
print(f"[6] Setting up training (output: {output_dir})...")

training_args = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=5,  # Quick retrain (base model already good)
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    warmup_steps=50,
    weight_decay=0.01,
    logging_dir=f"{output_dir}/logs",
    logging_steps=10,
    evaluation_strategy="epoch",  # Changed from eval_strategy
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    greater_is_better=True,
    save_total_limit=2,
    report_to="none",
    fp16=False,  # Disable FP16 to avoid accelerator issues
    learning_rate=2e-5,  # Lower LR for fine-tuning
    no_cuda=False,  # Use CUDA if available
)

# 7. Trainer
print("[7] Creating trainer...")
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
    # Removed data_collator and callbacks to avoid version issues
)

# 8. Train
print("\n" + "=" * 70)
print("TRAINING STARTED")
print("=" * 70)
trainer.train()

# 9. Evaluate
print("\n[8] Final evaluation on validation set...")
eval_results = trainer.evaluate()
print(f"Validation Accuracy: {eval_results['eval_accuracy']:.4f}")

# 10. Save final model
final_dir = "models/phobert-intent-v3-augmented/final"
print(f"\n[9] Saving final model to {final_dir}...")
model.save_pretrained(final_dir)
tokenizer.save_pretrained(final_dir)

# Save training config
config = {
    "dataset": "extended_dataset_v2.csv",
    "total_samples": len(df),
    "train_samples": len(train_df),
    "val_samples": len(val_df),
    "num_labels": len(labels),
    "labels": labels,
    "weak_intents_augmented": {
        intent: int((df['label'] == intent).sum()) 
        for intent in weak_intents
    },
    "final_accuracy": float(eval_results['eval_accuracy']),
    "training_date": datetime.now().isoformat(),
    "base_model": base_model_path,
    "output_dir": final_dir
}

with open(f"{final_dir}/training_config.json", 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

# 11. Detailed classification report
print("\n[10] Generating classification report...")
predictions = trainer.predict(val_dataset)
preds = predictions.predictions.argmax(-1)
labels_true = val_df['label_id'].tolist()

report = classification_report(
    labels_true,
    preds,
    target_names=labels,
    digits=4,
    zero_division=0
)
print("\nClassification Report:")
print(report)

# Save report
with open(f"{final_dir}/classification_report.txt", 'w', encoding='utf-8') as f:
    f.write(report)

# 12. Check weak intents performance
print("\n" + "=" * 70)
print("WEAK INTENTS PERFORMANCE CHECK")
print("=" * 70)
for intent in weak_intents:
    intent_id = label2id[intent]
    mask = np.array(labels_true) == intent_id
    if mask.sum() > 0:
        intent_acc = (np.array(preds)[mask] == intent_id).mean()
        print(f"{intent}: {intent_acc:.2%} accuracy ({mask.sum()} samples)")

print("\n[SUCCESS] TRAINING COMPLETED!")
print(f"[+] Model saved to: {final_dir}")
print(f"[*] Validation accuracy: {eval_results['eval_accuracy']:.2%}")
print("\n[INFO] Next steps:")
print("1. Update model_manager.py to use new model path")
print("2. Run test_nlp_fresh.py to verify improvements")
print("3. Monitor RL tuner with demo_rl.py")
