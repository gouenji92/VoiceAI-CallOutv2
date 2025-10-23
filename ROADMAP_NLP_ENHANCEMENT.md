# 🚀 ROADMAP: NLP / AI Service Enhancement

## 📋 Mục Tiêu

Nâng cấp hệ thống NLP/AI để đạt:
- ✅ **Intent Recognition Accuracy: >80%**
- ✅ **Sentiment Analysis Integration**
- ✅ **Context Management (Slot Filling)**
- ✅ **RAG (Retrieval-Augmented Generation)**
- ✅ **Logic Routing thông minh**

---

## 🎯 Hiện Trạng (Current State)

### ✅ Đã Có (Baseline)

```
app/services/
├── nlp_service.py          # PhoBERT intent classification
├── entity_extractor.py     # Regex-based entity extraction
├── dialog_manager.py       # Basic Agent HTTP client
└── model_manager.py        # Model loading/caching

agent/
├── http_agent.py          # Simple HTTP-based agent
└── skill.py               # Hardcoded dialog logic
```

**Accuracy hiện tại:**
- Intent: ~85% (PhoBERT với 5 intents cơ bản)
- Entity: ~70% (regex-based)
- Sentiment: ❌ Chưa có
- Context: ❌ Chưa có multi-turn
- RAG: ❌ Chưa có

---

## 🎯 Giai Đoạn 1: Nâng Cấp Intent Recognition (Week 1-2)

### 1.1. Tăng Dataset Quality

**File:** `data/intent_dataset_v2.csv`

```python
# Mở rộng từ 50 → 200+ samples
# Thêm augmentation data
# Balance classes (mỗi intent ≥40 samples)

intents = [
    'dat_lich',          # 40+ samples
    'hoi_thong_tin',     # 40+ samples
    'cam_on',            # 40+ samples
    'tam_biet',          # 40+ samples
    'unknown',           # 40+ samples
    'huy_lich',          # NEW: 40+ samples
    'doi_lich',          # NEW: 40+ samples
    'khieu_nai',         # NEW: 40+ samples
]
```

**Script:** `scripts/augment_intent_data.py`
```python
from nlpaug.augmenter.word import SynonymAug, BackTranslationAug

# Synonym replacement
aug_syn = SynonymAug(aug_src='wordnet', lang='vie')

# Back-translation (Vi → En → Vi)
aug_bt = BackTranslationAug(
    from_model_name='facebook/mbart-large-50-many-to-many-mmt',
    to_model_name='facebook/mbart-large-50-many-to-many-mmt'
)

# Paraphrase generation
# Output: data/intent_dataset_augmented.csv
```

### 1.2. Fine-tune PhoBERT Model

**File:** `train_intent_model_v3.py`

```python
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments
)
from sklearn.model_selection import StratifiedKFold

# K-Fold Cross Validation (5 folds)
kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for fold, (train_idx, val_idx) in enumerate(kfold.split(X, y)):
    print(f"Training Fold {fold+1}/5")
    
    # Hyperparameter tuning
    args = TrainingArguments(
        output_dir=f'./models/phobert-intent-fold{fold}',
        num_train_epochs=10,
        per_device_train_batch_size=16,
        learning_rate=2e-5,
        warmup_steps=500,
        weight_decay=0.01,
        eval_strategy='epoch',
        save_strategy='epoch',
        load_best_model_at_end=True,
        metric_for_best_model='f1',
    )
    
    trainer = Trainer(...)
    trainer.train()
    
    # Evaluate
    metrics = trainer.evaluate()
    print(f"Fold {fold+1} - F1: {metrics['eval_f1']:.4f}")

# Ensemble best 3 models
# Target: >80% accuracy, >0.78 F1-score
```

### 1.3. Confidence Threshold Tuning

**File:** `app/services/nlp_service.py` (Updated)

```python
class NLPService:
    CONFIDENCE_THRESHOLDS = {
        'dat_lich': 0.75,
        'hoi_thong_tin': 0.70,
        'huy_lich': 0.80,  # Cần chắc chắn hơn
        'doi_lich': 0.80,
        'default': 0.65
    }
    
    def classify_intent(self, text: str):
        result = self.model(text)[0]
        intent = result['label']
        confidence = result['score']
        
        threshold = self.CONFIDENCE_THRESHOLDS.get(
            intent, 
            self.CONFIDENCE_THRESHOLDS['default']
        )
        
        if confidence < threshold:
            return {'intent': 'unknown', 'confidence': confidence}
        
        return {'intent': intent, 'confidence': confidence}
```

---

## 🎯 Giai Đoạn 2: Thêm Sentiment Analysis (Week 2-3)

### 2.1. Train PhoBERT Sentiment Model

**File:** `train_sentiment_model.py`

```python
# Dataset: UIT-VSFC (Vietnamese Sentiment on Facebook Comments)
# Labels: positive, negative, neutral
# ~16k samples

from datasets import load_dataset

dataset = load_dataset('uitnlp/vietnamese_students_feedback')

model = AutoModelForSequenceClassification.from_pretrained(
    'vinai/phobert-base',
    num_labels=3  # positive, negative, neutral
)

# Train với same architecture như intent model
# Save to: models/phobert-sentiment/
```

### 2.2. Integrate Sentiment vào Pipeline

**File:** `app/services/nlp_service.py` (Updated)

```python
class NLPService:
    def __init__(self):
        self.intent_model = pipeline('text-classification', 
            model='./models/phobert-intent-classifier')
        self.sentiment_model = pipeline('text-classification',
            model='./models/phobert-sentiment')  # NEW
    
    def analyze_full(self, text: str):
        intent = self.classify_intent(text)
        sentiment = self.sentiment_model(text)[0]
        entities = extract_entities(text)
        
        return {
            'intent': intent['intent'],
            'confidence': intent['confidence'],
            'sentiment': sentiment['label'],  # positive/negative/neutral
            'sentiment_score': sentiment['score'],
            'entities': entities,
            'text': text
        }
```

### 2.3. Sentiment-based Response Adjustment

**File:** `agent/skill.py` (Updated)

```python
class CallbotSkill:
    def __call__(self, state):
        nlp = state.get('nlp_data', {})
        intent = nlp.get('intent')
        sentiment = nlp.get('sentiment')
        
        # Adjust response based on sentiment
        if sentiment == 'negative':
            if intent == 'khieu_nai':
                return self.handle_complaint(state)
            else:
                return self.empathize_and_resolve(state)
        
        elif sentiment == 'positive':
            return self.respond_positively(state)
        
        else:  # neutral
            return self.respond_normally(state)
    
    def empathize_and_resolve(self, state):
        return {
            'response': 'Tôi hiểu cảm giác của bạn. Để tôi giúp bạn giải quyết vấn đề này.',
            'action': 'escalate_to_human'
        }
```

---

## 🎯 Giai Đoạn 3: Context Management & Slot Filling (Week 3-4)

### 3.1. Implement Session State Management

**File:** `app/services/context_manager.py` (NEW)

```python
from typing import Dict, Any, List
from datetime import datetime, timedelta
import redis

class ContextManager:
    """Manage conversation context and slot filling"""
    
    def __init__(self):
        # Redis for session storage (1 hour TTL)
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def get_context(self, call_id: str) -> Dict[str, Any]:
        """Get conversation context"""
        key = f"context:{call_id}"
        data = self.redis.get(key)
        
        if data:
            return json.loads(data)
        
        return {
            'call_id': call_id,
            'slots': {},  # Filled slots
            'history': [],  # Conversation history
            'current_intent': None,
            'previous_intent': None,
            'slot_filling_state': None,
            'created_at': datetime.now().isoformat()
        }
    
    def update_context(self, call_id: str, updates: Dict[str, Any]):
        """Update context with new information"""
        context = self.get_context(call_id)
        
        # Merge updates
        context.update(updates)
        
        # Add to history
        if 'user_text' in updates:
            context['history'].append({
                'timestamp': datetime.now().isoformat(),
                'user': updates['user_text'],
                'bot': updates.get('bot_response', ''),
                'intent': updates.get('intent'),
                'entities': updates.get('entities', {})
            })
        
        # Save to Redis (1 hour TTL)
        key = f"context:{call_id}"
        self.redis.setex(key, 3600, json.dumps(context))
        
        return context
    
    def extract_and_fill_slots(self, context: Dict, nlp_data: Dict) -> Dict:
        """Extract entities and fill required slots"""
        intent = nlp_data.get('intent')
        entities = nlp_data.get('entities', {})
        
        # Define required slots for each intent
        REQUIRED_SLOTS = {
            'dat_lich': ['date', 'time'],
            'doi_lich': ['date', 'time', 'booking_id'],
            'huy_lich': ['booking_id'],
            'hoi_thong_tin': ['topic']
        }
        
        required = REQUIRED_SLOTS.get(intent, [])
        slots = context.get('slots', {})
        
        # Fill slots from entities
        for slot_name in required:
            if slot_name in entities and entities[slot_name]:
                slots[slot_name] = entities[slot_name]
        
        # Check if all required slots are filled
        missing_slots = [s for s in required if s not in slots or not slots[s]]
        
        return {
            'slots': slots,
            'missing_slots': missing_slots,
            'slot_filling_complete': len(missing_slots) == 0
        }
```

### 3.2. Slot Filling Dialog Flow

**File:** `agent/skill.py` (Updated with Context)

```python
class CallbotSkill:
    def __init__(self):
        self.context_manager = ContextManager()
        self.slot_prompts = {
            'date': 'Bạn muốn đặt lịch vào ngày nào?',
            'time': 'Bạn muốn đặt vào lúc mấy giờ?',
            'phone': 'Xin cho tôi biết số điện thoại của bạn?',
            'name': 'Tên của bạn là gì?',
            'booking_id': 'Mã đặt lịch của bạn là gì?'
        }
    
    def __call__(self, state):
        call_id = state.get('call_id')
        nlp_data = state.get('nlp_data', {})
        
        # Get context
        context = self.context_manager.get_context(call_id)
        
        # Extract and fill slots
        slot_info = self.context_manager.extract_and_fill_slots(context, nlp_data)
        
        context['slots'] = slot_info['slots']
        context['current_intent'] = nlp_data.get('intent')
        
        # If slot filling incomplete, ask for missing slot
        if not slot_info['slot_filling_complete']:
            missing_slot = slot_info['missing_slots'][0]
            prompt = self.slot_prompts.get(missing_slot, 'Xin bạn cung cấp thêm thông tin.')
            
            context['slot_filling_state'] = missing_slot
            self.context_manager.update_context(call_id, {
                'user_text': nlp_data.get('text'),
                'bot_response': prompt
            })
            
            return {
                'response': prompt,
                'action': 'ask_slot',
                'missing_slot': missing_slot
            }
        
        # All slots filled, execute intent
        return self.execute_intent(context, nlp_data)
```

---

## 🎯 Giai Đoạn 4: RAG Integration (Week 4-5)

### 4.1. Setup Vector Database

**File:** `docker-compose.yml` (Updated)

```yaml
version: '3.8'

services:
  # Existing services...
  
  qdrant:  # Vector database for RAG
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
```

### 4.2. Build Knowledge Base

**File:** `scripts/build_knowledge_base.py` (NEW)

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
import pandas as pd

# Initialize
client = QdrantClient(host='localhost', port=6333)
encoder = SentenceTransformer('keepitreal/vietnamese-sbert')  # Vietnamese embeddings

# Create collection
client.create_collection(
    collection_name='voiceai_knowledge',
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)

# Load knowledge data
df = pd.read_csv('data/knowledge_base.csv')
# Columns: id, question, answer, category, keywords

points = []
for idx, row in df.iterrows():
    # Create embedding
    text = f"{row['question']} {row['keywords']}"
    vector = encoder.encode(text).tolist()
    
    points.append(PointStruct(
        id=idx,
        vector=vector,
        payload={
            'question': row['question'],
            'answer': row['answer'],
            'category': row['category']
        }
    ))

# Upload to Qdrant
client.upsert(collection_name='voiceai_knowledge', points=points)
print(f"✅ Uploaded {len(points)} knowledge entries")
```

### 4.3. RAG Service

**File:** `app/services/rag_service.py` (NEW)

```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class RAGService:
    def __init__(self):
        self.client = QdrantClient(host='localhost', port=6333)
        self.encoder = SentenceTransformer('keepitreal/vietnamese-sbert')
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant documents from knowledge base"""
        
        # Encode query
        query_vector = self.encoder.encode(query).tolist()
        
        # Search in Qdrant
        results = self.client.search(
            collection_name='voiceai_knowledge',
            query_vector=query_vector,
            limit=top_k,
            score_threshold=0.7  # Only return relevant results
        )
        
        return [
            {
                'question': hit.payload['question'],
                'answer': hit.payload['answer'],
                'category': hit.payload['category'],
                'score': hit.score
            }
            for hit in results
        ]
    
    def generate_response(self, query: str, context: List[Dict]) -> str:
        """Generate response using retrieved context"""
        
        if not context:
            return "Xin lỗi, tôi không tìm thấy thông tin phù hợp. Bạn có thể nói rõ hơn không?"
        
        # Simple template-based generation
        # TODO: Replace with LLM (GPT, Llama, etc.) for better generation
        best_match = context[0]
        
        if best_match['score'] > 0.85:
            return best_match['answer']
        else:
            return f"Theo như tôi hiểu, {best_match['answer']}. Đúng không bạn?"
```

### 4.4. Integrate RAG vào Agent

**File:** `agent/skill.py` (Updated with RAG)

```python
class CallbotSkill:
    def __init__(self):
        self.rag_service = RAGService()  # NEW
    
    def handle_info_request(self, state):
        user_query = state.get('nlp_data', {}).get('text')
        
        # Retrieve relevant documents
        context = self.rag_service.retrieve(user_query, top_k=3)
        
        # Generate response
        response = self.rag_service.generate_response(user_query, context)
        
        return {
            'response': response,
            'action': 'provide_info',
            'sources': [c['question'] for c in context]  # For debugging
        }
```

---

## 🎯 Giai Đoạn 5: Advanced Routing Logic (Week 5-6)

### 5.1. Decision Tree Router

**File:** `app/services/router.py` (NEW)

```python
class SmartRouter:
    """Route conversations based on intent, sentiment, and context"""
    
    def route(self, nlp_data: Dict, context: Dict) -> str:
        intent = nlp_data.get('intent')
        sentiment = nlp_data.get('sentiment')
        confidence = nlp_data.get('confidence', 0)
        
        # Rule 1: Low confidence → Ask clarification
        if confidence < 0.65:
            return 'clarification'
        
        # Rule 2: Negative sentiment + complaint → Human escalation
        if sentiment == 'negative' and intent == 'khieu_nai':
            return 'human_agent'
        
        # Rule 3: Info request → RAG
        if intent == 'hoi_thong_tin':
            return 'rag_service'
        
        # Rule 4: Booking-related → Slot filling flow
        if intent in ['dat_lich', 'doi_lich', 'huy_lich']:
            return 'booking_flow'
        
        # Rule 5: Default → Agent
        return 'agent'
```

### 5.2. Update Dialog Manager

**File:** `app/services/dialog_manager.py` (Updated)

```python
class DialogManager:
    def __init__(self):
        self.router = SmartRouter()
        self.rag_service = RAGService()
        self.agent_client = HTTPAgentClient()
    
    def process(self, call_id: str, user_text: str) -> Dict:
        # NLP analysis
        nlp_data = nlp_service.analyze_full(user_text)
        
        # Get context
        context = context_manager.get_context(call_id)
        
        # Route to appropriate handler
        route = self.router.route(nlp_data, context)
        
        if route == 'rag_service':
            response = self.rag_service.generate_response(
                user_text, 
                self.rag_service.retrieve(user_text)
            )
        
        elif route == 'human_agent':
            response = "Để tôi chuyển bạn sang nhân viên hỗ trợ."
            # TODO: Integrate với hệ thống CRM/ticketing
        
        elif route == 'clarification':
            response = "Xin lỗi, tôi không hiểu rõ. Bạn có thể nói lại không?"
        
        else:  # Default agent
            response = self.agent_client.send_to_agent({
                'nlp_data': nlp_data,
                'context': context
            })
        
        # Update context
        context_manager.update_context(call_id, {
            'user_text': user_text,
            'bot_response': response['response'],
            'intent': nlp_data['intent']
        })
        
        return response
```

---

## 📊 Testing & Evaluation

### Test Suite

**File:** `tests/test_nlp_enhancement.py` (NEW)

```python
import pytest

class TestIntentClassification:
    def test_accuracy_threshold(self):
        """Intent accuracy should be >80%"""
        test_dataset = load_test_dataset()
        predictions = [nlp_service.classify_intent(text) for text in test_dataset['text']]
        accuracy = calculate_accuracy(predictions, test_dataset['labels'])
        
        assert accuracy > 0.80, f"Accuracy {accuracy:.2%} < 80%"
    
    def test_confidence_calibration(self):
        """Confidence scores should be calibrated"""
        # High confidence predictions should be correct
        high_conf_preds = [p for p in predictions if p['confidence'] > 0.8]
        high_conf_accuracy = calculate_accuracy(high_conf_preds)
        
        assert high_conf_accuracy > 0.90

class TestSentimentAnalysis:
    def test_sentiment_accuracy(self):
        """Sentiment accuracy should be >75%"""
        test_data = load_sentiment_test_data()
        # ... test logic

class TestSlotFilling:
    def test_multi_turn_booking(self):
        """Should fill all slots across multiple turns"""
        conversation = [
            "Tôi muốn đặt lịch",
            "Ngày mai",
            "9 giờ sáng",
            "0909123456"
        ]
        
        context = process_conversation(conversation)
        
        assert context['slots']['date'] is not None
        assert context['slots']['time'] is not None
        assert context['slots']['phone'] is not None

class TestRAG:
    def test_retrieval_relevance(self):
        """Retrieved documents should be relevant"""
        query = "Giá dịch vụ bao nhiêu?"
        results = rag_service.retrieve(query)
        
        assert len(results) > 0
        assert results[0]['score'] > 0.7
```

---

## 📈 Metrics & Monitoring

### Tracking Dashboard

**File:** `app/routers/analytics.py` (NEW)

```python
@router.get("/analytics/nlp_metrics")
async def get_nlp_metrics():
    """Get NLP performance metrics"""
    
    metrics = {
        'intent_accuracy': calculate_intent_accuracy_last_7_days(),
        'sentiment_accuracy': calculate_sentiment_accuracy(),
        'avg_confidence': calculate_avg_confidence(),
        'slot_filling_success_rate': calculate_slot_filling_rate(),
        'rag_hit_rate': calculate_rag_hit_rate(),
        'human_escalation_rate': calculate_escalation_rate()
    }
    
    return metrics
```

---

## 🎯 Success Criteria

### Phase 1: Intent Recognition
- ✅ Accuracy: >80%
- ✅ F1-score: >0.78
- ✅ Average confidence: >0.75
- ✅ 8 intents supported

### Phase 2: Sentiment Analysis
- ✅ Accuracy: >75%
- ✅ Integrated into response logic
- ✅ Negative sentiment escalation working

### Phase 3: Context Management
- ✅ Multi-turn conversations working
- ✅ Slot filling success rate: >85%
- ✅ Context retention: 1 hour

### Phase 4: RAG
- ✅ Knowledge base: 100+ entries
- ✅ Retrieval precision: >70%
- ✅ Response relevance: >75%

### Phase 5: Routing
- ✅ Smart routing implemented
- ✅ Human escalation rate: <10%
- ✅ Average resolution time: <5 turns

---

## 📚 Resources

### Documentation
- Deeppavlov: https://deeppavlov-agent.readthedocs.io/
- PhoBERT: https://github.com/VinAIResearch/PhoBERT
- Vietnamese SBERT: https://huggingface.co/keepitreal/vietnamese-sbert
- Qdrant: https://qdrant.tech/documentation/

### Datasets
- UIT-VSFC: Vietnamese sentiment
- PhoNER: Vietnamese NER
- ViHealthBERT: Healthcare domain

---

## 🚀 Next Steps (After Phase 5)

1. **LLM Integration** (GPT-4, Llama 3.1)
   - Replace template-based responses
   - Better contextual understanding

2. **Voice Integration**
   - Speech-to-Text (Whisper, Viettel STT)
   - Text-to-Speech (VBEE, Zalo TTS)

3. **Multi-language Support**
   - English + Vietnamese
   - Language detection

4. **Advanced Analytics**
   - Real-time dashboards
   - A/B testing framework

---

**Status:** 📋 **ROADMAP READY - Ready to Start Phase 1**
