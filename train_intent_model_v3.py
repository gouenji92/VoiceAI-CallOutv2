"""
Train Intent Model V3 with K-Fold Cross-Validation
Phase 1: Enhanced training with validation and metrics tracking

Features:
- K-Fold Cross-Validation (k=5)
- Per-intent confidence thresholds
- Comprehensive metrics tracking
- Confusion matrix visualization
- Model comparison and selection
"""

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
    EarlyStoppingCallback
)
from sklearn.metrics import (
    accuracy_score, 
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)
from sklearn.model_selection import StratifiedKFold
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
    """Compute comprehensive metrics"""
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    
    # Overall metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average='weighted', zero_division=0
    )
    acc = accuracy_score(labels, preds)
    
    # Per-class metrics
    precision_per_class, recall_per_class, f1_per_class, support = precision_recall_fscore_support(
        labels, preds, average=None, zero_division=0
    )
    
    results = {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }
    
    return results

def compute_confidence_thresholds(trainer, eval_dataset, id2label, percentile=75):
    """
    Compute optimal confidence threshold for each intent
    Using percentile of correct predictions
    """
    predictions = trainer.predict(eval_dataset)
    logits = predictions.predictions
    probs = torch.nn.functional.softmax(torch.tensor(logits), dim=-1).numpy()
    labels = predictions.label_ids
    pred_classes = logits.argmax(-1)
    
    # Get max probability for each prediction
    max_probs = probs.max(axis=-1)
    
    # Calculate threshold per class
    thresholds = {}
    for intent_id, intent_name in id2label.items():
        # Get correct predictions for this intent
        correct_mask = (labels == intent_id) & (pred_classes == intent_id)
        if correct_mask.sum() > 0:
            correct_probs = max_probs[correct_mask]
            threshold = np.percentile(correct_probs, percentile)
        else:
            threshold = 0.65  # Default fallback
        
        thresholds[intent_name] = float(threshold)
    
    return thresholds

def train_with_kfold(data_path, model_name="vinai/phobert-base", n_splits=5, output_dir="./models/phobert-intent-v3"):
    """
    Train model with K-Fold Cross-Validation
    """
    print(f"=== TRAINING WITH {n_splits}-FOLD CROSS-VALIDATION ===\n")
    
    # Load data
    df = pd.read_csv(data_path)
    print(f"Loaded dataset: {len(df)} samples")
    print(f"Class distribution:\n{df['label'].value_counts()}\n")
    
    # Prepare labels
    labels = df['label'].unique().tolist()
    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for i, label in enumerate(labels)}
    df['label_id'] = df['label'].map(label2id)
    
    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # K-Fold Cross-Validation
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    fold_results = []
    fold_models = []
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(df['text'], df['label_id']), 1):
        print(f"\n{'='*60}")
        print(f"FOLD {fold}/{n_splits}")
        print(f"{'='*60}")
        
        # Split data
        train_df = df.iloc[train_idx]
        val_df = df.iloc[val_idx]
        
        print(f"Train: {len(train_df)} samples, Val: {len(val_df)} samples")
        
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
        
        # Initialize model
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=len(labels),
            id2label=id2label,
            label2id=label2id
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=f'{output_dir}/fold_{fold}',
            num_train_epochs=15,
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
            # Removed fp16 to avoid accelerate compatibility issues
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
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
        )
        
        # Train
        print("\nTraining...")
        trainer.train()
        
        # Evaluate
        print("\nEvaluating...")
        eval_results = trainer.evaluate()
        
        # Get detailed predictions for confusion matrix
        predictions = trainer.predict(val_dataset)
        y_true = predictions.label_ids
        y_pred = predictions.predictions.argmax(-1)
        
        # Classification report
        report = classification_report(
            y_true, y_pred,
            target_names=[id2label[i] for i in range(len(labels))],
            output_dict=True,
            zero_division=0
        )
        
        # Compute confidence thresholds
        thresholds = compute_confidence_thresholds(trainer, val_dataset, id2label)
        
        # Store results
        fold_result = {
            'fold': fold,
            'accuracy': eval_results['eval_accuracy'],
            'f1': eval_results['eval_f1'],
            'precision': eval_results['eval_precision'],
            'recall': eval_results['eval_recall'],
            'report': report,
            'thresholds': thresholds,
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
        }
        fold_results.append(fold_result)
        fold_models.append((trainer, eval_results['eval_accuracy']))
        
        # Print results
        print(f"\nFold {fold} Results:")
        print(f"  Accuracy: {eval_results['eval_accuracy']:.4f}")
        print(f"  F1-Score: {eval_results['eval_f1']:.4f}")
        print(f"  Precision: {eval_results['eval_precision']:.4f}")
        print(f"  Recall: {eval_results['eval_recall']:.4f}")
        print(f"\nPer-Intent Thresholds:")
        for intent, threshold in thresholds.items():
            print(f"  {intent}: {threshold:.3f}")
    
    # Aggregate results
    print(f"\n{'='*60}")
    print(f"CROSS-VALIDATION RESULTS")
    print(f"{'='*60}")
    
    avg_accuracy = np.mean([r['accuracy'] for r in fold_results])
    std_accuracy = np.std([r['accuracy'] for r in fold_results])
    avg_f1 = np.mean([r['f1'] for r in fold_results])
    std_f1 = np.std([r['f1'] for r in fold_results])
    
    print(f"\nOverall Performance:")
    print(f"  Accuracy: {avg_accuracy:.4f} ± {std_accuracy:.4f}")
    print(f"  F1-Score: {avg_f1:.4f} ± {std_f1:.4f}")
    
    # Per-intent statistics
    print(f"\nPer-Intent Performance:")
    for intent in labels:
        intent_f1s = [r['report'][intent]['f1-score'] for r in fold_results]
        intent_precisions = [r['report'][intent]['precision'] for r in fold_results]
        intent_recalls = [r['report'][intent]['recall'] for r in fold_results]
        
        print(f"  {intent}:")
        print(f"    Precision: {np.mean(intent_precisions):.4f} ± {np.std(intent_precisions):.4f}")
        print(f"    Recall: {np.mean(intent_recalls):.4f} ± {np.std(intent_recalls):.4f}")
        print(f"    F1-Score: {np.mean(intent_f1s):.4f} ± {np.std(intent_f1s):.4f}")
    
    # Average confidence thresholds
    print(f"\nAverage Confidence Thresholds:")
    avg_thresholds = {}
    for intent in labels:
        intent_thresholds = [r['thresholds'][intent] for r in fold_results]
        avg_thresholds[intent] = float(np.mean(intent_thresholds))
        print(f"  {intent}: {avg_thresholds[intent]:.3f}")
    
    # Select best model
    best_fold_idx = max(range(len(fold_models)), key=lambda i: fold_models[i][1])
    best_trainer, best_accuracy = fold_models[best_fold_idx]
    
    print(f"\nBest Model: Fold {best_fold_idx + 1} (Accuracy: {best_accuracy:.4f})")
    
    # Save best model
    final_output_dir = f"{output_dir}/final"
    os.makedirs(final_output_dir, exist_ok=True)
    
    best_trainer.save_model(final_output_dir)
    tokenizer.save_pretrained(final_output_dir)
    
    # Save configuration
    config = {
        'model_name': model_name,
        'n_splits': n_splits,
        'training_date': datetime.now().isoformat(),
        'dataset_size': len(df),
        'label2id': label2id,
        'id2label': id2label,
        'avg_accuracy': float(avg_accuracy),
        'std_accuracy': float(std_accuracy),
        'avg_f1': float(avg_f1),
        'std_f1': float(std_f1),
        'best_fold': best_fold_idx + 1,
        'best_accuracy': float(best_accuracy),
        'confidence_thresholds': avg_thresholds,
        'fold_results': fold_results
    }
    
    config_path = f"{final_output_dir}/training_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\nModel saved to: {final_output_dir}")
    print(f"Configuration saved to: {config_path}")
    
    return config

if __name__ == "__main__":
    # Use augmented dataset
    data_path = "data/augmented_dataset.csv"
    
    # Train with K-Fold
    config = train_with_kfold(
        data_path=data_path,
        model_name="vinai/phobert-base",
        n_splits=5,
        output_dir="./models/phobert-intent-v3"
    )
    
    print("\n=== TRAINING COMPLETE ===")
    print(f"Average Accuracy: {config['avg_accuracy']:.4f}")
    print(f"Target: >0.80 {'✓ PASSED' if config['avg_accuracy'] > 0.80 else '✗ FAILED'}")
    print(f"Average F1-Score: {config['avg_f1']:.4f}")
    print(f"Target: >0.78 {'✓ PASSED' if config['avg_f1'] > 0.78 else '✗ FAILED'}")
