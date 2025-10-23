"""
Data Augmentation Script for Vietnamese Intent Dataset
Phase 1: Expand dataset from 50 to 200+ samples

Techniques:
1. Synonym Replacement (Vietnamese)
2. Paraphrasing
3. Add/Remove Punctuation
4. Add Polite Words
5. Word Order Variation
6. Back-Translation Simulation (rule-based)
"""

import pandas as pd
import random
import os
from typing import List, Tuple

# Vietnamese Synonym Dictionary
SYNONYM_DICT = {
    # Common verbs
    "muốn": ["cần", "định", "dự định", "có ý định"],
    "đặt": ["book", "hẹn", "đăng ký", "lên lịch"],
    "hỏi": ["xin", "tìm hiểu", "muốn biết"],
    "cho": ["giúp", "cung cấp", "đưa"],
    "biết": ["hiểu", "nắm", "rõ"],
    "có thể": ["được không", "có được không", "được chứ"],
    
    # Common nouns
    "lịch hẹn": ["cuộc hẹn", "lịch", "appointment"],
    "thông tin": ["chi tiết", "thông tin chi tiết", "info"],
    "dịch vụ": ["service", "sản phẩm"],
    "giá": ["chi phí", "phí", "tiền", "giá cả"],
    
    # Common adjectives
    "gấp": ["khẩn cấp", "nhanh", "sớm"],
    "tốt": ["tuyệt", "hay", "ổn"],
    
    # Questions
    "thế nào": ["ra sao", "như thế nào", "sao"],
    "bao nhiêu": ["mấy", "bao nhiêu tiền"],
}

# Polite words to add
POLITE_WORDS = ["ạ", "nhé", "ơi", "được không", "giúp tôi", "xin", "cho tôi"]

# Punctuation variations
PUNCTUATIONS = ["?", "!", ".", ","]

# Sentence templates for paraphrasing by intent
TEMPLATES = {
    "dat_lich": [
        "Tôi muốn {action} lịch hẹn",
        "Có thể {action} cho tôi một cuộc hẹn không",
        "{action} lịch giúp tôi",
        "Cho tôi {action} lịch",
        "Tôi cần {action} một cuộc hẹn",
        "Giúp tôi {action} lịch hẹn",
        "Xin {action} lịch",
        "Tôi có thể {action} lịch được không",
        "Làm ơn {action} lịch cho tôi",
        "{action} cuộc hẹn giúp tôi",
    ],
    "hoi_thong_tin": [
        "Cho tôi biết về {topic}",
        "Tôi muốn hỏi về {topic}",
        "Thông tin về {topic}",
        "{topic} như thế nào",
        "Giải thích cho tôi về {topic}",
        "Tôi cần tư vấn về {topic}",
        "Có thể cho tôi biết {topic} không",
        "Xin hỏi về {topic}",
        "Tôi muốn tìm hiểu {topic}",
        "{topic} ra sao",
    ],
    "cam_on": [
        "Cảm ơn {modifier}",
        "{modifier} cảm ơn",
        "Thanks {modifier}",
        "Cám ơn {modifier}",
        "{modifier} tốt quá",
        "{modifier} hay lắm",
    ],
    "tam_biet": [
        "Tạm biệt {modifier}",
        "{modifier} bye",
        "Hẹn gặp lại {modifier}",
        "Chào {modifier}",
        "Kết thúc {modifier}",
        "{modifier} tạm biệt",
    ],
    "unknown": [
        "Tôi không {verb}",
        "{verb} lại được không",
        "Tôi {verb} bối rối",
        "{verb} không rõ",
        "Tôi đang {verb}",
    ],
    "xac_nhan": [
        "{response} đúng vậy",
        "Tôi {response}",
        "{response} ạ",
        "Tôi {response} điều đó",
        "{response} với đề xuất",
    ],
    "tu_choi": [
        "{response}",
        "Tôi {response}",
        "{response} ạ",
        "Tôi {response} điều đó",
        "{response} nữa",
    ],
    "hoi_gio_lam_viec": [
        "Giờ làm việc {detail}",
        "{detail} mấy giờ",
        "Thời gian làm việc {detail}",
        "Lịch làm việc {detail}",
        "{detail} có làm việc không",
    ],
    "hoi_dia_chi": [
        "Địa chỉ {detail}",
        "{detail} ở đâu",
        "Cho tôi {detail}",
        "Tôi muốn biết {detail}",
        "{detail} gần nhất",
    ],
    "khieu_nai": [
        "Tôi {complaint}",
        "{complaint}",
        "Tôi muốn {complaint}",
        "{complaint} quá",
        "Tôi muốn gửi {complaint}",
    ],
    "yeu_cau_ho_tro": [
        "Tôi cần {support}",
        "{support} tôi",
        "Cần {support}",
        "Tôi cần sự {support}",
        "{support} khẩn cấp",
    ]
}

def synonym_replacement(text: str, n: int = 2) -> List[str]:
    """Replace n words with their synonyms"""
    words = text.split()
    augmented = []
    
    for _ in range(min(n, 3)):  # Generate up to 3 variations
        new_words = words.copy()
        changed = False
        
        for i, word in enumerate(words):
            if word in SYNONYM_DICT and random.random() > 0.5:
                synonyms = SYNONYM_DICT[word]
                new_words[i] = random.choice(synonyms)
                changed = True
        
        if changed:
            new_text = ' '.join(new_words)
            if new_text not in augmented and new_text != text:
                augmented.append(new_text)
    
    return augmented

def add_polite_words(text: str) -> List[str]:
    """Add polite words to the sentence"""
    augmented = []
    
    for word in POLITE_WORDS:
        if word not in text:
            # Add at the end
            new_text = f"{text} {word}"
            augmented.append(new_text)
            
            # Add at the beginning (for some words)
            if word in ["xin", "cho tôi", "giúp tôi"]:
                # Remove first word if it's "tôi" and add polite word
                words = text.split()
                if words[0].lower() == "tôi":
                    new_text = f"{word} {' '.join(words[1:])}"
                else:
                    new_text = f"{word} {text}"
                augmented.append(new_text)
    
    return augmented[:3]  # Limit to 3 variations

def punctuation_variation(text: str) -> List[str]:
    """Add/remove punctuation"""
    augmented = []
    
    # Remove punctuation
    no_punct = ''.join([c for c in text if c not in PUNCTUATIONS])
    if no_punct != text:
        augmented.append(no_punct)
    
    # Add different punctuation
    text_clean = text.rstrip(''.join(PUNCTUATIONS))
    for punct in PUNCTUATIONS:
        if not text.endswith(punct):
            augmented.append(text_clean + punct)
    
    return augmented[:2]  # Limit to 2 variations

def template_based_generation(intent: str, count: int = 5) -> List[str]:
    """Generate new samples using templates"""
    if intent not in TEMPLATES:
        return []
    
    templates = TEMPLATES[intent]
    generated = []
    
    # Define placeholders based on intent
    if intent == "dat_lich":
        actions = ["đặt", "book", "hẹn", "đăng ký", "lên lịch", "tạo"]
        for _ in range(count):
            template = random.choice(templates)
            action = random.choice(actions)
            generated.append(template.format(action=action))
    
    elif intent == "hoi_thong_tin":
        topics = ["dịch vụ", "sản phẩm", "giá cả", "lịch làm việc", "quy trình", 
                  "chi phí", "chính sách", "thông tin", "điều kiện", "thủ tục"]
        for _ in range(count):
            template = random.choice(templates)
            topic = random.choice(topics)
            generated.append(template.format(topic=topic))
    
    elif intent == "cam_on":
        modifiers = ["bạn", "nhiều", "bạn nhiều", "nha", "nhé", "ạ", "", "rất nhiều"]
        for _ in range(count):
            template = random.choice(templates)
            modifier = random.choice(modifiers)
            generated.append(template.format(modifier=modifier))
    
    elif intent == "tam_biet":
        modifiers = ["nhé", "nha", "bạn", "ạ", "", "bye"]
        for _ in range(count):
            template = random.choice(templates)
            modifier = random.choice(modifiers)
            generated.append(template.format(modifier=modifier))
    
    elif intent == "unknown":
        verbs = ["hiểu", "nghe rõ", "nắm được", "biết", "rõ", "nghe"]
        for _ in range(count):
            template = random.choice(templates)
            verb = random.choice(verbs)
            generated.append(template.format(verb=verb))
    
    elif intent == "xac_nhan":
        responses = ["đồng ý", "OK", "được", "chấp nhận", "xác nhận", "đúng"]
        for _ in range(count):
            template = random.choice(templates)
            response = random.choice(responses)
            generated.append(template.format(response=response))
    
    elif intent == "tu_choi":
        responses = ["không", "không muốn", "từ chối", "không đồng ý", "không cần", "thôi", "hủy bỏ"]
        for _ in range(count):
            template = random.choice(templates)
            response = random.choice(responses)
            generated.append(template.format(response=response))
    
    elif intent == "hoi_gio_lam_viec":
        details = ["thế nào", "của bạn", "cụ thể", "hôm nay", "thứ 7", "chủ nhật", "trong tuần"]
        for _ in range(count):
            template = random.choice(templates)
            detail = random.choice(details)
            generated.append(template.format(detail=detail))
    
    elif intent == "hoi_dia_chi":
        details = ["của bạn", "công ty", "cụ thể", "văn phòng", "chi nhánh", "cơ sở", "địa điểm"]
        for _ in range(count):
            template = random.choice(templates)
            detail = random.choice(details)
            generated.append(template.format(detail=detail))
    
    elif intent == "khieu_nai":
        complaints = ["không hài lòng", "muốn khiếu nại", "thất vọng", "bị lừa", 
                      "muốn phàn nàn", "muốn hoàn tiền", "khiếu nại"]
        for _ in range(count):
            template = random.choice(templates)
            complaint = random.choice(complaints)
            generated.append(template.format(complaint=complaint))
    
    elif intent == "yeu_cau_ho_tro":
        supports = ["hỗ trợ", "giúp đỡ", "trợ giúp", "hướng dẫn", "tư vấn", "giúp"]
        for _ in range(count):
            template = random.choice(templates)
            support = random.choice(supports)
            generated.append(template.format(support=support))
    
    return generated

def augment_dataset(input_csv: str, output_csv: str, target_per_class: int = 40):
    """
    Augment the entire dataset to reach target samples per class
    
    Args:
        input_csv: Path to original dataset
        output_csv: Path to save augmented dataset
        target_per_class: Target number of samples per class
    """
    # Load original data
    df = pd.read_csv(input_csv)
    print(f"Original dataset: {len(df)} samples")
    print(f"Class distribution:\n{df['label'].value_counts()}")
    
    # Store all augmented data
    augmented_data = []
    
    # Process each intent
    for label in df['label'].unique():
        label_df = df[df['label'] == label]
        original_texts = label_df['text'].tolist()
        
        print(f"\n=== Augmenting intent: {label} ===")
        print(f"Original samples: {len(original_texts)}")
        
        # Keep all original samples
        for text in original_texts:
            augmented_data.append({'text': text, 'label': label})
        
        # Calculate how many more we need
        needed = target_per_class - len(original_texts)
        print(f"Need to generate: {needed} more samples")
        
        if needed <= 0:
            continue
        
        # Generate augmented samples
        new_samples = set()
        
        # 1. Template-based generation (highest priority)
        template_samples = template_based_generation(label, count=needed // 2)
        new_samples.update(template_samples)
        print(f"Template-based: {len(template_samples)} samples")
        
        # 2. Synonym replacement
        for text in original_texts:
            if len(new_samples) >= needed:
                break
            synonyms = synonym_replacement(text, n=2)
            new_samples.update(synonyms[:2])
        print(f"After synonym replacement: {len(new_samples)} total")
        
        # 3. Polite words
        for text in original_texts:
            if len(new_samples) >= needed:
                break
            polite = add_polite_words(text)
            new_samples.update(polite[:2])
        print(f"After polite words: {len(new_samples)} total")
        
        # 4. Punctuation variations
        for text in original_texts:
            if len(new_samples) >= needed:
                break
            punct = punctuation_variation(text)
            new_samples.update(punct)
        print(f"After punctuation: {len(new_samples)} total")
        
        # 5. Combine techniques
        for text in original_texts:
            if len(new_samples) >= needed:
                break
            # Try synonym + polite word
            synonyms = synonym_replacement(text, n=1)
            for syn in synonyms:
                polite = add_polite_words(syn)
                new_samples.update(polite[:1])
        
        # Add generated samples to dataset
        new_samples_list = list(new_samples)[:needed]
        for text in new_samples_list:
            augmented_data.append({'text': text, 'label': label})
        
        print(f"Final count for {label}: {len(original_texts) + len(new_samples_list)}")
    
    # Create augmented dataframe
    augmented_df = pd.DataFrame(augmented_data)
    
    # Shuffle the dataset
    augmented_df = augmented_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Save to CSV
    augmented_df.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"\n=== AUGMENTATION COMPLETE ===")
    print(f"Total samples: {len(augmented_df)}")
    print(f"Class distribution:\n{augmented_df['label'].value_counts()}")
    print(f"Saved to: {output_csv}")
    
    return augmented_df

if __name__ == "__main__":
    # Paths
    input_file = "data/extended_dataset.csv"  # Use extended dataset with new intents
    output_file = "data/augmented_extended_dataset.csv"
    
    # Run augmentation
    augmented_df = augment_dataset(input_file, output_file, target_per_class=40)
    
    # Print some examples
    print("\n=== SAMPLE AUGMENTED DATA ===")
    for label in augmented_df['label'].unique():
        print(f"\n{label}:")
        samples = augmented_df[augmented_df['label'] == label]['text'].head(5).tolist()
        for i, sample in enumerate(samples, 1):
            print(f"  {i}. {sample}")
