"""
Custom training loop for Vietnamese intent classification (Phase 1)
- Avoids Transformers Trainer/Accelerate to bypass env compatibility issues
- Uses standard PyTorch training loop
"""

import os
# Prevent transformers from importing TensorFlow/Flax/TorchVision optional deps
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TRANSFORMERS_NO_FLAX", "1")
os.environ.setdefault("TRANSFORMERS_NO_TORCHVISION", "1")

import json
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report

from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class IntentDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
    def __len__(self):
        return len(self.labels)
    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

@torch.no_grad()
def evaluate(model, dataloader, id2label: Dict[int, str]):
    model.eval()
    all_preds, all_labels = [], []
    for batch in dataloader:
        batch = {k: v.to(DEVICE) for k, v in batch.items()}
        outputs = model(**batch)
        logits = outputs.logits
        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.detach().cpu().numpy().tolist())
        all_labels.extend(batch['labels'].detach().cpu().numpy().tolist())

    acc = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average='weighted', zero_division=0)

    # Per-intent report
    report = classification_report(
        all_labels, all_preds,
        target_names=[id2label[i] for i in range(len(id2label))],
        output_dict=True, zero_division=0
    )
    return {
        'accuracy': acc,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'report': report
    }

@torch.no_grad()
def compute_confidence_thresholds(model, dataloader, id2label: Dict[int, str], percentile: int = 70):
    model.eval()
    all_max_probs = []
    all_preds = []
    all_labels = []

    for batch in dataloader:
        labels = batch['labels']
        batch = {k: v.to(DEVICE) for k, v in batch.items()}
        outputs = model(**batch)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        max_probs, preds = torch.max(probs, dim=-1)
        all_max_probs.extend(max_probs.detach().cpu().numpy().tolist())
        all_preds.extend(preds.detach().cpu().numpy().tolist())
        all_labels.extend(labels.numpy().tolist())

    all_max_probs = np.array(all_max_probs)
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    thresholds = {}
    for i, name in id2label.items():
        mask = (all_labels == i) & (all_preds == i)
        if mask.sum() > 0:
            thresholds[name] = float(np.percentile(all_max_probs[mask], percentile))
        else:
            thresholds[name] = 0.65
    return thresholds

def main():
    print("="*60)
    print("PHASE 1: INTENT CLASSIFICATION (Custom Loop)")
    print("="*60)

    # 1) Load data
    df = pd.read_csv('data/augmented_extended_dataset.csv')  # Use extended dataset with 11 intents
    labels = sorted(df['label'].unique().tolist())
    label2id = {l: i for i, l in enumerate(labels)}
    id2label = {i: l for l, i in label2id.items()}
    df['label_id'] = df['label'].map(label2id)

    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label_id'])
    print(f"Train: {len(train_df)} | Val: {len(val_df)}")

    # 2) Tokenizer & encodings
    model_name = 'vinai/phobert-base'
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    train_enc = tokenizer(train_df['text'].tolist(), truncation=True, padding=True, max_length=128)
    val_enc = tokenizer(val_df['text'].tolist(), truncation=True, padding=True, max_length=128)

    train_ds = IntentDataset(train_enc, train_df['label_id'].tolist())
    val_ds = IntentDataset(val_enc, val_df['label_id'].tolist())

    # Custom collate to avoid importing transformers.data (which pulls tensorflow)
    def collate_fn(examples):
        # Manual padding to avoid transformers' TF checks
        def to_list(x):
            return x.tolist() if isinstance(x, torch.Tensor) else x
        input_ids = [to_list(ex['input_ids']) for ex in examples]
        attention_mask = [to_list(ex['attention_mask']) for ex in examples]
        labels = [int(ex['labels']) if isinstance(ex['labels'], torch.Tensor) else ex['labels'] for ex in examples]

        max_len = max(len(x) for x in input_ids)
        pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0

        def pad_list(seq, pad_val):
            return seq + [pad_val] * (max_len - len(seq))

        batch = {
            'input_ids': torch.tensor([pad_list(x, pad_id) for x in input_ids], dtype=torch.long),
            'attention_mask': torch.tensor([pad_list(x, 0) for x in attention_mask], dtype=torch.long),
            'labels': torch.tensor(labels, dtype=torch.long)
        }
        if 'token_type_ids' in examples[0]:
            tti = [to_list(ex['token_type_ids']) for ex in examples]
            batch['token_type_ids'] = torch.tensor([pad_list(x, 0) for x in tti], dtype=torch.long)
        return batch

    train_loader = DataLoader(train_ds, batch_size=16, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_ds, batch_size=16, shuffle=False, collate_fn=collate_fn)

    # 3) Model, optimizer, scheduler
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id
    ).to(DEVICE)

    optimizer = AdamW(model.parameters(), lr=3e-5, weight_decay=0.01)
    num_epochs = 15  # Increased for 11 intents
    total_steps = num_epochs * len(train_loader)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(0.1 * total_steps),
        num_training_steps=total_steps
    )

    best_f1 = -1.0
    for epoch in range(1, num_epochs + 1):
        model.train()
        running_loss = 0.0
        for step, batch in enumerate(train_loader, 1):
            batch = {k: v.to(DEVICE) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            running_loss += loss.item()
            if step % 10 == 0:
                print(f"Epoch {epoch} Step {step}/{len(train_loader)} - Loss: {running_loss/step:.4f}")

        metrics = evaluate(model, val_loader, id2label)
        print(f"Epoch {epoch} - Val Acc: {metrics['accuracy']:.4f} | F1: {metrics['f1']:.4f}")
        if metrics['f1'] > best_f1:
            best_f1 = metrics['f1']
            best_state = {k: v.cpu() for k, v in model.state_dict().items()}

    # Load best state
    model.load_state_dict(best_state)

    # Final eval
    metrics = evaluate(model, val_loader, id2label)
    print("\nFinal Evaluation:")
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  F1-Score: {metrics['f1']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall: {metrics['recall']:.4f}")

    # Confidence thresholds
    thresholds = compute_confidence_thresholds(model, val_loader, id2label)
    print("\nConfidence Thresholds:")
    for intent, thr in thresholds.items():
        print(f"  {intent}: {thr:.3f}")

    # Save model (safetensors by default if available)
    output_dir = 'models/phobert-intent-v3/final'
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Save config
    config = {
        'model_name': model_name,
        'training_date': datetime.now().isoformat(),
        'dataset_size': int(len(df)),
        'train_size': int(len(train_df)),
        'val_size': int(len(val_df)),
        'label2id': label2id,
        'id2label': id2label,
        'avg_accuracy': float(metrics['accuracy']),
        'avg_f1': float(metrics['f1']),
        'std_accuracy': 0.0,
        'std_f1': 0.0,
        'confidence_thresholds': thresholds,
        'fold_results': [{
            'fold': 1,
            'accuracy': float(metrics['accuracy']),
            'f1': float(metrics['f1']),
            'report': metrics['report']
        }]
    }
    with open(os.path.join(output_dir, 'training_config.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\nModel saved to: {output_dir}")
    print("="*60)

if __name__ == '__main__':
    main()
