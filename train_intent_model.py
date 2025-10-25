"""
Intent Model Training Script - PhoBERT Fine-tuning
Trains intent classification model on augmented Vietnamese dataset
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AdamW, get_linear_schedule_with_warmup
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from tqdm import tqdm

print("=" * 70)
print("INTENT MODEL TRAINING - AUGMENTED DATASET V2")
print("=" * 70)

# 1. Load dataset
print("\n[1] Loading augmented dataset v2...")
df = pd.read_csv('data/extended_dataset_v2.csv')
print(f"Total samples: {len(df)}")

# Weak intents check
weak_intents = ['yeu_cau_ho_tro', 'tu_choi', 'khieu_nai']
print("\n[*] Weak intents after augmentation:")
for intent in weak_intents:
    count = (df['label'] == intent).sum()
    print(f"  {intent}: {count} samples")

# 2. Label mapping
label_names = sorted(df['label'].unique())
label2id = {label: i for i, label in enumerate(label_names)}
id2label = {i: label for label, i in label2id.items()}
df['label_id'] = df['label'].map(label2id)

print(f"\n[2] Number of classes: {len(label_names)}")

# 3. Train/val split
from sklearn.model_selection import train_test_split
train_df, val_df = train_test_split(df, test_size=0.1, stratify=df['label_id'], random_state=42)
print(f"Train samples: {len(train_df)}")
print(f"Val samples: {len(val_df)}")

# 4. Load tokenizer and model
print("\n[3] Loading model and tokenizer...")
base_model_path = 'models/phobert-intent-v3/final'
tokenizer = AutoTokenizer.from_pretrained(base_model_path)
model = AutoModelForSequenceClassification.from_pretrained(
    base_model_path,
    num_labels=len(label_names),
    id2label=id2label,
    label2id=label2id
)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
print(f"Device: {device}")

# 5. Tokenize
print("\n[4] Tokenizing...")
def tokenize_batch(texts):
    return tokenizer(texts, truncation=True, padding=True, max_length=128, return_tensors='pt')

# Create dataloaders
batch_size = 16

class IntentDataset(torch.utils.data.Dataset):
    """PyTorch Dataset for intent classification training"""
    def __init__(self, texts, labels):
        self.texts = texts
        self.labels = labels
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        return self.texts[idx], self.labels[idx]

train_dataset = IntentDataset(train_df['text'].tolist(), train_df['label_id'].tolist())
val_dataset = IntentDataset(val_df['text'].tolist(), val_df['label_id'].tolist())

train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=32, shuffle=False)

# 6. Optimizer and scheduler
print("\n[5] Setting up optimizer...")
epochs = 5
optimizer = AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)
total_steps = len(train_loader) * epochs
scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=50, num_training_steps=total_steps)

# 7. Training loop
print("\n[6] Starting training...")
print("=" * 70)

best_val_acc = 0
output_dir = f"models/phobert-intent-v3-retrain-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(output_dir, exist_ok=True)

for epoch in range(epochs):
    # Training
    model.train()
    train_loss = 0
    train_preds = []
    train_labels = []
    
    pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
    for texts, labels in pbar:
        # Tokenize batch
        inputs = tokenize_batch(texts)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        # Ensure labels are a tensor on the correct device and keep a plain int list for metrics
        if isinstance(labels, torch.Tensor):
            labels_tensor = labels.to(device)
            labels_list = labels.detach().cpu().tolist()
        else:
            labels_tensor = torch.tensor(labels).to(device)
            labels_list = [int(l) for l in labels]
        
        # Forward
        outputs = model(**inputs, labels=labels_tensor)
        loss = outputs.loss
        
        # Backward
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        scheduler.step()
        
        # Track
        train_loss += loss.item()
        preds = outputs.logits.argmax(dim=-1).cpu().numpy()
        train_preds.extend(preds)
        train_labels.extend(labels_list)
        pbar.set_postfix({'loss': f'{loss.item():.4f}'})
    
    train_acc = accuracy_score(train_labels, train_preds)
    avg_train_loss = train_loss / len(train_loader)
    
    # Validation
    model.eval()
    val_preds = []
    val_labels = []
    val_loss = 0
    
    with torch.no_grad():
        for texts, labels in tqdm(val_loader, desc="Validation"):
            inputs = tokenize_batch(texts)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            # Ensure labels are a tensor on device and plain ints for metrics
            if isinstance(labels, torch.Tensor):
                labels_tensor = labels.to(device)
                labels_list = labels.detach().cpu().tolist()
            else:
                labels_tensor = torch.tensor(labels).to(device)
                labels_list = [int(l) for l in labels]
            
            outputs = model(**inputs, labels=labels_tensor)
            val_loss += outputs.loss.item()
            
            preds = outputs.logits.argmax(dim=-1).cpu().numpy()
            val_preds.extend(preds)
            val_labels.extend(labels_list)
    
    val_acc = accuracy_score(val_labels, val_preds)
    avg_val_loss = val_loss / len(val_loader)
    
    print(f"\nEpoch {epoch+1}:")
    print(f"  Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.4f}")
    print(f"  Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.4f}")
    
    # Save best model
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        final_dir = f"{output_dir}/final"
        os.makedirs(final_dir, exist_ok=True)
        model.save_pretrained(final_dir)
        tokenizer.save_pretrained(final_dir)
        print(f"  [*] Saved best model (val_acc={val_acc:.4f})")

print("\n" + "=" * 70)
print("[7] Final evaluation...")

# Classification report (only for labels present in validation set)
# Coerce potential tensor/np types to ints just in case
unique_labels_in_val = sorted({int(l) for l in val_labels})
unique_label_names = [id2label[int(i)] for i in unique_labels_in_val]
report = classification_report(
    val_labels,
    val_preds,
    labels=unique_labels_in_val,
    target_names=unique_label_names,
    digits=4,
    zero_division=0
)
print("\nClassification Report:")
print(report)

# Save report
final_dir = f"{output_dir}/final"
with open(f"{final_dir}/classification_report.txt", 'w', encoding='utf-8') as f:
    f.write(report)

# Weak intents performance
print("\n[*] Weak intents performance:")
for intent in weak_intents:
    intent_id = label2id[intent]
    mask = np.array(val_labels) == intent_id
    if mask.sum() > 0:
        intent_acc = (np.array(val_preds)[mask] == intent_id).mean()
        print(f"  {intent}: {intent_acc:.2%} accuracy ({mask.sum()} val samples)")

# Save config
config = {
    "dataset": "extended_dataset_v2.csv",
    "total_samples": len(df),
    "train_samples": len(train_df),
    "val_samples": len(val_df),
    "num_labels": len(label_names),
    "labels": label_names,
    "weak_intents_augmented": {intent: int((df['label'] == intent).sum()) for intent in weak_intents},
    "final_accuracy": float(best_val_acc),
    "training_date": datetime.now().isoformat(),
    "base_model": base_model_path,
    "output_dir": final_dir,
    "epochs": epochs,
    "learning_rate": 2e-5,
    "batch_size": batch_size
}

with open(f"{final_dir}/training_config.json", 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("\n[SUCCESS] TRAINING COMPLETED!")
print(f"[+] Model saved to: {final_dir}")
print(f"[*] Best validation accuracy: {best_val_acc:.2%}")
print("\n[INFO] Next steps:")
print("1. Test with: python test_retrained_model.py")
print("2. Update model_manager.py if results are good")
print("3. Deploy with RL monitoring")
print("=" * 70)
print("3. Deploy with RL monitoring")
print("=" * 70)
