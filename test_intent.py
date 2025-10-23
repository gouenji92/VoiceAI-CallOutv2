from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Load model và tokenizer
model_path = "./models/phobert-intent-classifier"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# Tạo pipeline
classifier = pipeline("text-classification", model=model, tokenizer=tokenizer)

# Các câu test
test_sentences = [
    "cho tôi đặt lịch vào ngày mai",
    "tôi muốn biết thêm thông tin",
    "xin lỗi tôi không nghe rõ",
    "cảm ơn bạn rất nhiều",
    "tạm biệt và hẹn gặp lại",
    "tôi có thể đặt lịch khám không?",
    "giá cả như thế nào vậy?",
    "bạn nói lại được không?",
    "rất hữu ích, cảm ơn nhiều",
    "chào tạm biệt nhé"
]

print("--- KẾT QUẢ NHẬN DẠNG INTENT ---")
for sentence in test_sentences:
    result = classifier(sentence)[0]
    print(f"\nCâu: '{sentence}'")
    print(f"Intent: {result['label']} (độ tin cậy: {result['score']:.4f})")