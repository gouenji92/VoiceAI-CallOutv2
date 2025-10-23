"""
Quick Validation Script for Phase 1
Verifies model meets targets: >80% accuracy, >0.78 F1
"""

import json

# Load training config
config_path = "models/phobert-intent-v3/final/training_config.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

print("="*60)
print("PHASE 1 NLP ENHANCEMENT - VALIDATION REPORT")
print("="*60)

print(f"\nOverall Metrics:")
print(f"  Accuracy: {config['avg_accuracy']:.4f} (target: >0.80)")
print(f"  F1-Score: {config['avg_f1']:.4f} (target: >0.78)")

print(f"\nPer-Intent Performance (from Fold 1):")
report = config['fold_results'][0]['report']
for intent in ['dat_lich', 'hoi_thong_tin', 'unknown', 'cam_on', 'tam_biet']:
    print(f"  {intent}:")
    print(f"    Precision: {report[intent]['precision']:.4f}")
    print(f"    Recall: {report[intent]['recall']:.4f}")
    print(f"    F1-Score: {report[intent]['f1-score']:.4f}")

print(f"\nConfidence Thresholds:")
for intent, threshold in config['confidence_thresholds'].items():
    print(f"  {intent}: {threshold:.3f}")

print(f"\nDataset Info:")
print(f"  Total Samples: {config['dataset_size']}")
print(f"  Train: {config['train_size']}")
print(f"  Val: {config['val_size']}")
print(f"  Training Date: {config['training_date']}")

print("\n" + "="*60)
print("TARGET EVALUATION")
print("="*60)

accuracy_passed = config['avg_accuracy'] >= 0.80
f1_passed = config['avg_f1'] >= 0.78

print(f"Accuracy >= 0.80: {'✓ PASSED' if accuracy_passed else '✗ FAILED'}")
print(f"F1-Score >= 0.78: {'✓ PASSED' if f1_passed else '✗ FAILED'}")

if accuracy_passed and f1_passed:
    print("\n✓✓✓ PHASE 1 SUCCESSFULLY COMPLETED! ✓✓✓")
else:
    print("\n⚠ PHASE 1 TARGETS NOT FULLY MET")

print("="*60)
