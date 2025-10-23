# file: train_intent_model.py
# (Lưu file này ở thư mục gốc VoiceAI/)

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
    EarlyStoppingCallback
)
from sklearn.metrics import accuracy_score
import pandas as pd
from sklearn.model_selection import train_test_split
import os

# --- 1. DỮ LIỆU (DATASET) ---
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
df = pd.DataFrame(data)

labels = df['label'].unique().tolist()
label2id = {label: i for i, label in enumerate(labels)}
id2label = {i: label for i, label in enumerate(labels)}
df['label'] = df['label'].map(label2id)

print(f"Cac intent tim thay: {label2id}")

# --- 2. Chuẩn bị DataLoader ---
# Data Augmentation
def augment_text(text):
    # Thêm hoặc xóa dấu câu
    augmented = []
    punctuations = ['?', '!', '.', ',']
    
    # Xóa dấu câu
    no_punct = ''.join([c for c in text if c not in punctuations])
    if no_punct != text:
        augmented.append(no_punct)
    
    # Thêm dấu câu
    if not text.endswith('?'):
        augmented.append(text + '?')
    if not text.endswith('!'):
        augmented.append(text + '!')
    
    # Thêm từ lịch sự
    polite_words = ['ạ', 'nhé', 'ơi']
    for word in polite_words:
        if word not in text:
            augmented.append(text + ' ' + word)
    
    return augmented

# Augment data
augmented_texts = []
augmented_labels = []
for text, label in zip(df['text'], df['label']):
    augmented_texts.append(text)
    augmented_labels.append(label)
    
    # Thêm các biến thể được augment
    for aug_text in augment_text(text):
        augmented_texts.append(aug_text)
        augmented_labels.append(label)

# Chia tập train/val với dữ liệu đã được augment
train_texts, val_texts, train_labels, val_labels = train_test_split(
    augmented_texts, augmented_labels, test_size=0.2, random_state=42, stratify=augmented_labels
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
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support
    
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    
    # Tính các metric
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='weighted')
    acc = accuracy_score(labels, preds)
    
    # Tính confusion matrix cho từng class
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
            f'{intent}_precision': precision_i,
            f'{intent}_recall': recall_i,
            f'{intent}_f1': f1_i
        })
    
    return results

try:
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id
    )
except Exception as e:
    print(f"Lỗi khi tải model: {str(e)}")
    raise

training_args = TrainingArguments(
    output_dir='./models/phobert-intent-classifier',
    num_train_epochs=20,                    # Tăng số epochs
    per_device_train_batch_size=16,         # Tăng batch size
    per_device_eval_batch_size=16,
    learning_rate=3e-5,                     # Tăng learning rate một chút
    weight_decay=0.01,
    warmup_ratio=0.1,                       # Thêm warmup
    save_strategy="epoch",                  # Lưu model mỗi epoch
    evaluation_strategy="epoch",            # Đánh giá mỗi epoch
    load_best_model_at_end=True,           # Tự động load model tốt nhất
    metric_for_best_model="accuracy",
    greater_is_better=True,
    logging_dir='./logs',                  # Thư mục log
    logging_steps=10                       # Log mỗi 10 bước
)

data_collator = DataCollatorWithPadding(tokenizer)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    data_collator=data_collator,
    compute_metrics=compute_metrics
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