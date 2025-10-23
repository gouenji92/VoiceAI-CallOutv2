import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    AutoConfig,
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
import os

# --- 1. DỮ LIỆU ---
data = {
    "text": [
        # Đặt lịch
        "Tôi muốn đặt một cái lịch hẹn",
        "Cho tôi hẹn vào 9h sáng mai",
        "Tôi có thể đặt lịch được không?",
        "Đặt lịch hẹn khám bệnh",
        "Tôi muốn đặt cuộc hẹn",
        "Xin đặt lịch vào thứ 2 tuần sau",
        "Có thể giúp tôi đặt lịch không?",
        "Tôi cần một cuộc hẹn gấp",
        "Book lịch giúp tôi nhé",
        "Đăng ký lịch hẹn",
        
        # Hỏi thông tin
        "Xin chào, tôi muốn hỏi thông tin",
        "Sản phẩm này giá bao nhiêu?",
        "Cho tôi biết thêm chi tiết",
        "Tôi muốn tìm hiểu về dịch vụ",
        "Giải thích giúp tôi về vấn đề này",
        "Có thể cho tôi biết thêm không?",
        "Tôi cần tư vấn",
        "Thông tin về lịch làm việc",
        "Quy trình đăng ký thế nào?",
        "Chi phí dịch vụ ra sao?",
        
        # Unknown
        "Tôi không hiểu", 
        "Nói lại đi",
        "Không rõ lắm",
        "Bạn nói gì tôi không nghe rõ",
        "Lặp lại được không?",
        "Hả?",
        "Tôi bị lạc đề rồi",
        "Không biết phải làm sao",
        "Tôi đang bối rối quá",
        "Cái này là sao?",
        
        # Cảm ơn
        "Cảm ơn", 
        "Tuyệt vời",
        "Cảm ơn bạn nhiều",
        "Rất hữu ích",
        "Tốt quá",
        "Cám ơn sự giúp đỡ",
        "Thank you",
        "Hay quá",
        "Giỏi lắm",
        "Cảm ơn nhé",
        
        # Tạm biệt
        "Tạm biệt", 
        "Kết thúc đi",
        "Hẹn gặp lại",
        "Chào tạm biệt",
        "Goodbye",
        "Tôi phải đi đây",
        "Kết thúc cuộc gọi",
        "Bye bye",
        "Hẹn gặp sau",
        "Chào nhé"
    ],
    "label": [
        # Đặt lịch - 10 mẫu
        "dat_lich", "dat_lich", "dat_lich", "dat_lich", "dat_lich",
        "dat_lich", "dat_lich", "dat_lich", "dat_lich", "dat_lich",
        
        # Hỏi thông tin - 10 mẫu
        "hoi_thong_tin", "hoi_thong_tin", "hoi_thong_tin", "hoi_thong_tin", "hoi_thong_tin",
        "hoi_thong_tin", "hoi_thong_tin", "hoi_thong_tin", "hoi_thong_tin", "hoi_thong_tin",
        
        # Unknown - 10 mẫu
        "unknown", "unknown", "unknown", "unknown", "unknown",
        "unknown", "unknown", "unknown", "unknown", "unknown",
        
        # Cảm ơn - 10 mẫu
        "cam_on", "cam_on", "cam_on", "cam_on", "cam_on",
        "cam_on", "cam_on", "cam_on", "cam_on", "cam_on",
        
        # Tạm biệt - 10 mẫu
        "tam_biet", "tam_biet", "tam_biet", "tam_biet", "tam_biet",
        "tam_biet", "tam_biet", "tam_biet", "tam_biet", "tam_biet"
    ]
}

# Chuyển đổi dữ liệu thành DataFrame
df = pd.DataFrame(data)

# Mapping labels to IDs
labels = df['label'].unique().tolist()
label2id = {label: i for i, label in enumerate(labels)}
id2label = {i: label for i, label in enumerate(labels)}

print(f"Các intent tìm thấy: {label2id}")

# Chuyển đổi labels thành số
df['label'] = df['label'].map(label2id)

# Chia tập train/val TRƯỚC khi augment để tránh leakage
raw_texts = df['text'].tolist()
raw_labels = df['label'].tolist()

train_texts, val_texts, train_labels, val_labels = train_test_split(
    raw_texts,
    raw_labels,
    test_size=0.2,
    random_state=42,
    stratify=raw_labels,
)

# Data augmentation chỉ áp dụng cho train set
def augment_text(text):
    augmented = []
    if not text.endswith(('?', '!', '.')):
        augmented.extend([text + '?', text + '!', text + '.'])
    polite_words = ['ạ', 'nhé', 'ơi']
    for word in polite_words:
        if word not in text:
            augmented.append(text + ' ' + word)
    # --- lightweight paraphrase augmentations ---
    # 1) synonym swap (small map)
    syn_map = {
        'đặt': ['book', 'đăng ký', 'sắp xếp'],
        'hẹn': ['lịch', 'gặp'],
        'xin chào': ['chào', 'hello'],
        'thông tin': ['chi tiết', 'mô tả'],
        'giá': ['chi phí', 'phí']
    }
    words = text.split()
    for i, w in enumerate(words):
        key = w.lower().strip('.,?!')
        if key in syn_map:
            for rep in syn_map[key]:
                new_words = words.copy()
                new_words[i] = rep
                augmented.append(' '.join(new_words))

    # 2) template rewrite (move polite word to front)
    if any(p in text for p in ['ạ', 'nhé', 'ơi']):
        pass
    else:
        augmented.append('Vui lòng ' + text)

    # 3) short/long variants (add/remove phrase)
    if len(text.split()) > 3:
        augmented.append(' '.join(text.split()[:3]))
    else:
        augmented.append(text + ' thêm thông tin')

    # return unique augmented
    return list(dict.fromkeys(augmented))

aug_texts = []
aug_labels = []
for t, l in zip(train_texts, train_labels):
    aug_texts.append(t)
    aug_labels.append(l)
    for a in augment_text(t):
        aug_texts.append(a)
        aug_labels.append(l)

# Gán lại train set đã augment
train_texts, train_labels = aug_texts, aug_labels

# Tokenize dữ liệu
model_name = "vinai/phobert-base"
# Tokenizer with explicit max_length to avoid variable-length leakage and truncation warnings
tokenizer = AutoTokenizer.from_pretrained(model_name)
MAX_LEN = 128

train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=MAX_LEN)
val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=MAX_LEN)

# Dataset class
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

# Tạo datasets
train_dataset = VietDataset(train_encodings, train_labels)
val_dataset = VietDataset(val_encodings, val_labels)

# Hàm tính metrics
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average='weighted'
    )
    acc = accuracy_score(labels, preds)
    
    # Tính metrics cho từng intent
    results = {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }
    
    # Tính metrics cho từng intent
    for i, intent in id2label.items():
        precision_i, recall_i, f1_i, _ = precision_recall_fscore_support(
            labels == i, preds == i, average='binary'
        )
        results.update({
            f'{intent}_f1': f1_i
        })
    
    return results

# Khởi tạo model với cấu hình tăng dropout cho regularization
config = AutoConfig.from_pretrained(model_name, num_labels=len(labels), id2label=id2label, label2id=label2id)
# tăng dropout nếu trường hợp overfitting
if not hasattr(config, 'classifier_dropout'):
    # phobert/roberta-style
    config.classifier_dropout = 0.2
config.hidden_dropout_prob = getattr(config, 'hidden_dropout_prob', 0.1)

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    config=config
)

# Data collator
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# Training arguments (hơi thận trọng để tránh overfitting)
args = TrainingArguments(
    output_dir='./models/phobert-intent-classifier',
    num_train_epochs=6,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    learning_rate=2e-5,
    weight_decay=0.01,
    logging_dir='./logs',
    eval_strategy='epoch',
    save_strategy='epoch',
    load_best_model_at_end=True,
    metric_for_best_model='accuracy',
    save_total_limit=2,
)

# Trainer with EarlyStopping
trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    data_collator=data_collator,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
)

print("--- BẮT ĐẦU HUẤN LUYỆN MODEL INTENT ---")
trainer.train()
print("--- HUẤN LUYỆN HOÀN TẤT ---")

# Lưu model
output_model_dir = "./models/phobert-intent-classifier"
if not os.path.exists(output_model_dir):
    os.makedirs(output_model_dir)
    
trainer.save_model(output_model_dir)
tokenizer.save_pretrained(output_model_dir)

print(f"Model đã được lưu vào: {output_model_dir}")

# Đánh giá kết quả
print("\n--- KẾT QUẢ ĐÁNH GIÁ ---")
eval_results = trainer.evaluate()
for metric, value in eval_results.items():
    if metric.endswith('_f1'):
        intent = metric.replace('_f1', '')
        print(f"F1-score cho intent '{intent}': {value:.4f}")
print(f"Độ chính xác tổng thể: {eval_results['eval_accuracy']:.4f}")
print(f"F1-score tổng thể: {eval_results['eval_f1']:.4f}")