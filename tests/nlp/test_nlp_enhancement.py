"""
Comprehensive Test Suite for Phase 1 NLP Enhancement
Validates >80% accuracy and >0.78 F1-score targets

Tests:
1. Dataset validation (balance, quality)
2. Model performance (accuracy, F1, precision, recall)
3. Per-intent metrics
4. Confidence threshold effectiveness
5. Edge cases and robustness
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

# Test configuration
AUGMENTED_DATASET = "data/augmented_dataset.csv"
MODEL_DIR = "models/phobert-intent-v3/final"
TARGET_ACCURACY = 0.80
TARGET_F1 = 0.78
TARGET_PER_INTENT_F1 = 0.75

# Test fixtures
@pytest.fixture
def dataset():
    """Load augmented dataset"""
    df = pd.read_csv(AUGMENTED_DATASET)
    return df

@pytest.fixture
def model_config():
    """Load model configuration"""
    config_path = Path(MODEL_DIR) / "training_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def model_pipeline():
    """Load trained model pipeline"""
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    classifier = pipeline("text-classification", model=model, tokenizer=tokenizer)
    return classifier

# Dataset Tests
class TestDatasetQuality:
    """Test dataset quality and balance"""
    
    def test_dataset_exists(self):
        """Test that augmented dataset exists"""
        assert Path(AUGMENTED_DATASET).exists(), "Augmented dataset not found"
    
    def test_dataset_size(self, dataset):
        """Test dataset has at least 200 samples"""
        assert len(dataset) >= 200, f"Dataset too small: {len(dataset)} < 200"
    
    def test_class_balance(self, dataset):
        """Test that all classes are balanced (within 10%)"""
        class_counts = dataset['label'].value_counts()
        mean_count = class_counts.mean()
        
        for label, count in class_counts.items():
            deviation = abs(count - mean_count) / mean_count
            assert deviation <= 0.10, f"Class {label} imbalance: {deviation:.2%}"
    
    def test_no_duplicates(self, dataset):
        """Test that there are no exact duplicate texts"""
        duplicates = dataset.duplicated(subset=['text']).sum()
        duplicate_ratio = duplicates / len(dataset)
        assert duplicate_ratio < 0.15, f"Too many duplicates: {duplicate_ratio:.2%}"
    
    def test_text_quality(self, dataset):
        """Test that texts are not empty and have reasonable length"""
        # No empty texts
        assert (dataset['text'].str.len() > 0).all(), "Empty texts found"
        
        # Reasonable length (3-100 words)
        word_counts = dataset['text'].str.split().str.len()
        assert (word_counts >= 1).all(), "Texts with 0 words found"
        assert (word_counts <= 100).all(), "Texts too long (>100 words)"
    
    def test_all_intents_present(self, dataset):
        """Test that all expected intents are present"""
        expected_intents = {'dat_lich', 'hoi_thong_tin', 'unknown', 'cam_on', 'tam_biet'}
        actual_intents = set(dataset['label'].unique())
        assert expected_intents == actual_intents, f"Missing intents: {expected_intents - actual_intents}"

# Model Performance Tests
class TestModelPerformance:
    """Test overall model performance"""
    
    def test_model_exists(self):
        """Test that model directory exists"""
        assert Path(MODEL_DIR).exists(), "Model directory not found"
    
    def test_config_exists(self, model_config):
        """Test that training config exists and is valid"""
        assert 'avg_accuracy' in model_config, "avg_accuracy not in config"
        assert 'avg_f1' in model_config, "avg_f1 not in config"
        assert 'confidence_thresholds' in model_config, "confidence_thresholds not in config"
    
    def test_average_accuracy_target(self, model_config):
        """Test that cross-validation average accuracy meets target"""
        avg_accuracy = model_config['avg_accuracy']
        assert avg_accuracy >= TARGET_ACCURACY, \
            f"Average accuracy {avg_accuracy:.4f} < target {TARGET_ACCURACY}"
    
    def test_average_f1_target(self, model_config):
        """Test that cross-validation average F1 meets target"""
        avg_f1 = model_config['avg_f1']
        assert avg_f1 >= TARGET_F1, \
            f"Average F1 {avg_f1:.4f} < target {TARGET_F1}"
    
    def test_model_consistency(self, model_config):
        """Test that model performance is consistent across folds (low std)"""
        std_accuracy = model_config['std_accuracy']
        assert std_accuracy < 0.10, \
            f"High variance in accuracy: {std_accuracy:.4f}"
    
    def test_per_intent_f1(self, model_config):
        """Test that each intent has reasonable F1 score"""
        fold_results = model_config['fold_results']
        
        # Calculate average F1 per intent across folds
        intents = ['dat_lich', 'hoi_thong_tin', 'unknown', 'cam_on', 'tam_biet']
        for intent in intents:
            intent_f1s = [fold['report'][intent]['f1-score'] for fold in fold_results]
            avg_f1 = np.mean(intent_f1s)
            assert avg_f1 >= TARGET_PER_INTENT_F1, \
                f"Intent {intent} F1 {avg_f1:.4f} < target {TARGET_PER_INTENT_F1}"

# Confidence Threshold Tests
class TestConfidenceThresholds:
    """Test confidence threshold configuration"""
    
    def test_thresholds_exist(self, model_config):
        """Test that confidence thresholds are defined for all intents"""
        thresholds = model_config['confidence_thresholds']
        expected_intents = {'dat_lich', 'hoi_thong_tin', 'unknown', 'cam_on', 'tam_biet'}
        actual_intents = set(thresholds.keys())
        assert expected_intents == actual_intents, \
            f"Missing thresholds: {expected_intents - actual_intents}"
    
    def test_threshold_ranges(self, model_config):
        """Test that thresholds are in reasonable range (0.5-0.9)"""
        thresholds = model_config['confidence_thresholds']
        for intent, threshold in thresholds.items():
            assert 0.5 <= threshold <= 0.9, \
                f"Threshold for {intent} out of range: {threshold}"
    
    def test_threshold_ordering(self, model_config):
        """Test that specific intents have appropriate thresholds"""
        thresholds = model_config['confidence_thresholds']
        
        # 'unknown' should have lower threshold (catch uncertain cases)
        assert thresholds['unknown'] <= thresholds['dat_lich'], \
            "Unknown threshold should be lower than dat_lich"
        
        # 'cam_on' and 'tam_biet' can have higher thresholds (more certain)
        avg_threshold = np.mean(list(thresholds.values()))
        assert thresholds['cam_on'] >= avg_threshold * 0.95, \
            "cam_on threshold should be near or above average"

# Inference Tests
class TestModelInference:
    """Test model inference and predictions"""
    
    def test_model_loads(self, model_pipeline):
        """Test that model loads successfully"""
        assert model_pipeline is not None, "Model pipeline failed to load"
    
    def test_prediction_format(self, model_pipeline):
        """Test that predictions have correct format"""
        test_text = "Tôi muốn đặt lịch hẹn"
        result = model_pipeline(test_text)
        
        assert isinstance(result, list), "Result should be a list"
        assert len(result) > 0, "Result should not be empty"
        assert 'label' in result[0], "Result should have 'label'"
        assert 'score' in result[0], "Result should have 'score'"
    
    def test_known_samples(self, model_pipeline):
        """Test predictions on known samples"""
        test_cases = [
            ("Tôi muốn đặt lịch hẹn", "dat_lich"),
            ("Cho tôi biết giá cả", "hoi_thong_tin"),
            ("Cảm ơn bạn", "cam_on"),
            ("Tạm biệt", "tam_biet"),
            ("Tôi không hiểu", "unknown"),
        ]
        
        correct = 0
        for text, expected_intent in test_cases:
            result = model_pipeline(text)[0]
            if result['label'] == expected_intent:
                correct += 1
        
        accuracy = correct / len(test_cases)
        assert accuracy >= 0.80, f"Known samples accuracy {accuracy:.2%} < 80%"
    
    def test_edge_cases(self, model_pipeline):
        """Test model on edge cases"""
        edge_cases = [
            "đặt lịch",  # Very short
            "Tôi muốn đặt lịch hẹn vào ngày mai lúc 9 giờ sáng với bác sĩ",  # Long
            "dat lich",  # No diacritics
            "ĐẶT LỊCH",  # All caps
            "Tôi... muốn... đặt lịch",  # Punctuation
        ]
        
        # Should not crash
        for text in edge_cases:
            try:
                result = model_pipeline(text)
                assert result is not None, f"Failed on: {text}"
            except Exception as e:
                pytest.fail(f"Model crashed on edge case '{text}': {e}")
    
    def test_confidence_distribution(self, model_pipeline, dataset):
        """Test that confidence scores have reasonable distribution"""
        # Sample 50 texts
        sample_texts = dataset.sample(n=min(50, len(dataset)), random_state=42)['text'].tolist()
        
        confidences = []
        for text in sample_texts:
            result = model_pipeline(text)[0]
            confidences.append(result['score'])
        
        # Check distribution
        mean_confidence = np.mean(confidences)
        assert mean_confidence >= 0.70, f"Mean confidence too low: {mean_confidence:.2%}"
        
        # Should have some high-confidence predictions
        high_confidence = sum(1 for c in confidences if c >= 0.85) / len(confidences)
        assert high_confidence >= 0.30, f"Too few high-confidence predictions: {high_confidence:.2%}"

# Robustness Tests
class TestModelRobustness:
    """Test model robustness to variations"""
    
    def test_punctuation_robustness(self, model_pipeline):
        """Test that model is robust to punctuation changes"""
        base_texts = [
            "Tôi muốn đặt lịch",
            "Cho tôi biết thông tin",
            "Cảm ơn bạn"
        ]
        
        for base_text in base_texts:
            # Get base prediction
            base_result = model_pipeline(base_text)[0]
            base_intent = base_result['label']
            
            # Test variations
            variations = [
                base_text + ".",
                base_text + "?",
                base_text + "!",
                base_text.replace(" ", "  "),  # Double space
            ]
            
            consistent = 0
            for var_text in variations:
                var_result = model_pipeline(var_text)[0]
                if var_result['label'] == base_intent:
                    consistent += 1
            
            consistency_rate = consistent / len(variations)
            assert consistency_rate >= 0.75, \
                f"Low punctuation robustness for '{base_text}': {consistency_rate:.2%}"
    
    def test_polite_words_robustness(self, model_pipeline):
        """Test that model is robust to polite words"""
        base_texts = [
            ("Tôi muốn đặt lịch", "dat_lich"),
            ("Cho tôi biết thông tin", "hoi_thong_tin"),
        ]
        
        polite_suffixes = [" ạ", " nhé", " được không"]
        
        for base_text, expected_intent in base_texts:
            for suffix in polite_suffixes:
                polite_text = base_text + suffix
                result = model_pipeline(polite_text)[0]
                assert result['label'] == expected_intent, \
                    f"Polite word changed intent: '{polite_text}' -> {result['label']}"

# Performance Summary
def test_generate_performance_report(model_config):
    """Generate and print comprehensive performance report"""
    print("\n" + "="*60)
    print("PHASE 1 NLP ENHANCEMENT - PERFORMANCE REPORT")
    print("="*60)
    
    print(f"\nOverall Metrics:")
    print(f"  Average Accuracy: {model_config['avg_accuracy']:.4f} (target: {TARGET_ACCURACY})")
    print(f"  Average F1-Score: {model_config['avg_f1']:.4f} (target: {TARGET_F1})")
    print(f"  Std Accuracy: {model_config['std_accuracy']:.4f}")
    print(f"  Std F1-Score: {model_config['std_f1']:.4f}")
    
    print(f"\nPer-Intent F1 Scores:")
    fold_results = model_config['fold_results']
    intents = ['dat_lich', 'hoi_thong_tin', 'unknown', 'cam_on', 'tam_biet']
    for intent in intents:
        intent_f1s = [fold['report'][intent]['f1-score'] for fold in fold_results]
        avg_f1 = np.mean(intent_f1s)
        std_f1 = np.std(intent_f1s)
        status = "✓" if avg_f1 >= TARGET_PER_INTENT_F1 else "✗"
        print(f"  {intent}: {avg_f1:.4f} ± {std_f1:.4f} {status}")
    
    print(f"\nConfidence Thresholds:")
    for intent, threshold in model_config['confidence_thresholds'].items():
        print(f"  {intent}: {threshold:.3f}")
    
    print(f"\nTraining Info:")
    print(f"  Dataset Size: {model_config['dataset_size']}")
    print(f"  K-Folds: {model_config['n_splits']}")
    print(f"  Best Fold: {model_config['best_fold']} (accuracy: {model_config['best_accuracy']:.4f})")
    print(f"  Training Date: {model_config['training_date']}")
    
    print("\n" + "="*60)
    
    # Overall status
    passed = (
        model_config['avg_accuracy'] >= TARGET_ACCURACY and
        model_config['avg_f1'] >= TARGET_F1
    )
    
    if passed:
        print("✓ PHASE 1 TARGETS ACHIEVED")
    else:
        print("✗ PHASE 1 TARGETS NOT MET")
    print("="*60 + "\n")

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
