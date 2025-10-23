"""
Simplified Training Script - Phase 1
Train on augmented dataset with train/val split (no K-Fold due to compatibility issues)
"""

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
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
    """Compute comprehensive metrics"""
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average='weighted', zero_division=0
    )
    acc = accuracy_score(labels, preds)
    
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def compute_confidence_thresholds(trainer, eval_dataset, id2label, percentile=70):
    """Compute optimal confidence threshold for each intent"""
    predictions = trainer.predict(eval_dataset)
    logits = predictions.predictions
    probs = torch.nn.functional.softmax(torch.tensor(logits), dim=-1).numpy()
    labels = predictions.label_ids
    pred_classes = logits.argmax(-1)
    
    max_probs = probs.max(axis=-1)
    
    thresholds = {}
    for intent_id, intent_name in id2label.items():
        correct_mask = (labels == intent_id) & (pred_classes == intent_id)
        if correct_mask.sum() > 0:
            correct_probs = max_probs[correct_mask]
            threshold = np.percentile(correct_probs, percentile)
        else:
            threshold = 0.65
        
        thresholds[intent_name] = float(threshold)
    
    return thresholds

def main():
    print("="*60)
    print("PHASE 1: INTENT CLASSIFICATION TRAINING")
    print("="*60)
    
    # Load augmented dataset
    data_path = "data/augmented_dataset.csv"
    df = pd.read_csv(data_path)
    print(f"\nDataset: {len(df)} samples")
    print(f"Class distribution:\n{df['label'].value_counts()}\n")
    
    # Prepare labels
    labels = sorted(df['label'].unique().tolist())
    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for i, label in enumerate(labels)}
    df['label_id'] = df['label'].map(label2id)
    
    # Split dataset (80% train, 20% val)
    train_df, val_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df['label_id']
    )
    
    print(f"Train: {len(train_df)} samples")
    print(f"Val: {len(val_df)} samples\n")
    
    # Load tokenizer
    model_name = "vinai/phobert-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Tokenize
    train_encodings = tokenizer(
        train_df['text'].tolist(),
        truncation=True,
        padding=True,
        max_length=128
    )
    val_encodings = tokenizer(
        val_df['text'].tolist(),
        truncation=True,
        padding=True,
        max_length=128
    )
    
    # Create datasets
    train_dataset = IntentDataset(train_encodings, train_df['label_id'].tolist())
    val_dataset = IntentDataset(val_encodings, val_df['label_id'].tolist())
    
    # Load model
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id
    )
    
    # Training arguments
    output_dir = "./models/phobert-intent-v3"
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=20,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        learning_rate=3e-5,
        weight_decay=0.01,
        warmup_ratio=0.1,
        save_strategy="epoch",
        evaluation_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        greater_is_better=True,
        logging_steps=10,
        save_total_limit=2,
    )
    
    # Data collator
    data_collator = DataCollatorWithPadding(tokenizer)
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    
    # Train
    print("Training...")
    trainer.train()
    
    # Evaluate
    print("\nEvaluating...")
    eval_results = trainer.evaluate()
    
    print(f"\nFinal Results:")
    print(f"  Accuracy: {eval_results['eval_accuracy']:.4f}")
    print(f"  F1-Score: {eval_results['eval_f1']:.4f}")
    print(f"  Precision: {eval_results['eval_precision']:.4f}")
    print(f"  Recall: {eval_results['eval_recall']:.4f}")
    
    # Get detailed predictions
    predictions = trainer.predict(val_dataset)
    y_true = predictions.label_ids
    y_pred = predictions.predictions.argmax(-1)
    
    # Classification report
    print("\nPer-Intent Performance:")
    report = classification_report(
        y_true, y_pred,
        target_names=[id2label[i] for i in range(len(labels))],
        output_dict=True,
        zero_division=0
    )
    
    for intent in labels:
        print(f"  {intent}:")
        print(f"    Precision: {report[intent]['precision']:.4f}")
        print(f"    Recall: {report[intent]['recall']:.4f}")
        print(f"    F1-Score: {report[intent]['f1-score']:.4f}")
    
    # Compute confidence thresholds
    print("\nComputing confidence thresholds...")
    thresholds = compute_confidence_thresholds(trainer, val_dataset, id2label)
    
    print("Confidence Thresholds:")
    for intent, threshold in thresholds.items():
        print(f"  {intent}: {threshold:.3f}")
    
    # Save model
    final_output_dir = f"{output_dir}/final"
    os.makedirs(final_output_dir, exist_ok=True)
    
    trainer.save_model(final_output_dir)
    tokenizer.save_pretrained(final_output_dir)
    
    # Save configuration
    config = {
        'model_name': model_name,
        'training_date': datetime.now().isoformat(),
        'dataset_size': len(df),
        'train_size': len(train_df),
        'val_size': len(val_df),
        'label2id': label2id,
        'id2label': id2label,
        'avg_accuracy': float(eval_results['eval_accuracy']),
        'avg_f1': float(eval_results['eval_f1']),
        'std_accuracy': 0.0,  # Single run, no std
        'std_f1': 0.0,
        'confidence_thresholds': thresholds,
        'fold_results': [{'fold': 1, 'accuracy': eval_results['eval_accuracy'], 'f1': eval_results['eval_f1'], 'report': report}]
    }
    
    config_path = f"{final_output_dir}/training_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\nModel saved to: {final_output_dir}")
    print(f"Configuration saved to: {config_path}")
    
    # Check if targets met
    print("\n" + "="*60)
    print("PHASE 1 TARGET EVALUATION")
    print("="*60)
    print(f"Accuracy: {eval_results['eval_accuracy']:.4f} (target: >0.80)")
    print(f"F1-Score: {eval_results['eval_f1']:.4f} (target: >0.78)")
    
    accuracy_passed = eval_results['eval_accuracy'] > 0.80
    f1_passed = eval_results['eval_f1'] > 0.78
    
    if accuracy_passed and f1_passed:
        print("\n✓ PHASE 1 TARGETS ACHIEVED!")
    else:
        print("\n⚠ PHASE 1 TARGETS NOT FULLY MET")
        if not accuracy_passed:
            print(f"  - Accuracy below target ({eval_results['eval_accuracy']:.4f} < 0.80)")
        if not f1_passed:
            print(f"  - F1-Score below target ({eval_results['eval_f1']:.4f} < 0.78)")
    
    print("="*60)

if __name__ == "__main__":
    main()
