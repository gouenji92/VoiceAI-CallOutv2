# Reinforcement Learning - Threshold Tuning System

## Tổng quan

Hệ thống RL tự động tối ưu ngưỡng (threshold) confidence cho mỗi intent bằng contextual epsilon-greedy bandit, giúp giảm "unknown" giả và cải thiện độ chính xác phân loại intent theo thời gian.

## Kiến trúc

### 1. RL Threshold Tuner (`app/services/rl_threshold_tuner.py`)
- **Thuật toán**: Contextual epsilon-greedy bandit với UCB1 exploration bonus
- **Arms**: 8 giá trị ngưỡng từ 0.80 đến 0.95 cho mỗi intent
- **Context**: raw_confidence, text_length, sentiment
- **State persistence**: JSON file (`models/rl_threshold_state.json`)
- **Epsilon decay**: 0.995 per update, min 0.05

### 2. Reward Signals
| Reward | Điều kiện | Ý nghĩa |
|--------|-----------|---------|
| +1.0   | User xác nhận hoặc tiến trình thành công | Intent chính xác |
| 0.0    | Cần làm rõ (clarification) | Không chắc chắn |
| -1.0   | User phủ định hoặc phải chuyển người | Intent sai hoặc chất lượng thấp |

### 3. Integration Points

**NLP Service** (`app/services/nlp_service.py`):
```python
# Adaptive threshold selection
tuner = get_tuner()
threshold = tuner.get_threshold(
    intent=raw_intent,
    raw_confidence=raw_confidence,
    context={'text_length': len(text)},
    call_id=call_id
)
```

**Agent** (`agent/skill.py`):
- Mỗi intent handler trả về `action_success`:
  - `True`: Thành công (reward +1)
  - `False`: Thất bại (reward -1)
  - `None`: Trung lập (reward 0)

**Feedback API** (`/feedback/rl-reward`):
```json
{
  "call_id": "xxx",
  "reward": 1.0,
  "final_intent": "dat_lich",
  "notes": "User confirmed booking"
}
```

## Sử dụng

### Khởi động hệ thống
```bash
# Start API với RL tuner enabled (mặc định)
python -X utf8 -m uvicorn app.main:app --reload
```

### Gửi feedback
```python
import requests

# Sau khi có kết quả cuộc gọi
response = requests.post(
    "http://localhost:8000/feedback/rl-reward",
    json={
        "call_id": "abc123",
        "reward": 1.0,  # Success
        "final_intent": None,
        "notes": "User proceeded with booking"
    }
)
```

### Monitoring
```bash
# Xem thống kê hiện tại
curl http://localhost:8000/feedback/rl-stats

# Visualize threshold evolution
python scripts/monitor_rl_tuner.py
```

### Testing
```bash
# Run end-to-end tests
python test_rl_tuner.py
```

## Database Schema

Bảng `rl_feedback` trong `sql/schema_complete.sql`:
```sql
CREATE TABLE IF NOT EXISTS rl_feedback (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id text NOT NULL,
    reward double precision NOT NULL,
    final_intent text,
    notes text,
    created_at timestamptz DEFAULT now()
);
```

## Workflow

1. **Prediction**: NLP service dùng RL tuner để chọn threshold động
2. **Execution**: Agent xử lý intent và trả về `action_success`
3. **Feedback**: Client/system gửi reward signal qua API
4. **Update**: Tuner cập nhật arm statistics và decay epsilon
5. **Persistence**: State được lưu định kỳ vào JSON

## Tham số điều chỉnh

Trong `app/services/rl_threshold_tuner.py`:
```python
RLThresholdTuner(
    intents=INTENT_LIST,
    min_threshold=0.80,      # Ngưỡng thấp nhất
    max_threshold=0.95,      # Ngưỡng cao nhất
    num_arms=8,              # Số lựa chọn threshold
    epsilon=0.15,            # Tỷ lệ explore ban đầu
    epsilon_decay=0.995,     # Tốc độ giảm exploration
    min_epsilon=0.05         # Explore tối thiểu
)
```

## Metrics & Monitoring

**Stats API** (`/feedback/rl-stats`):
- Best threshold per intent
- Average reward per intent
- Exploration/exploitation ratio
- Total pulls per arm

**Visualization** (`scripts/monitor_rl_tuner.py`):
- Threshold distribution heatmap
- Arm performance charts
- Reward trends over time
- Confidence intervals

## Best Practices

1. **Cold start**: Hệ thống cần ~50-100 feedback samples per intent để ổn định
2. **Reward consistency**: Đảm bảo reward signals phản ánh đúng chất lượng
3. **Monitoring**: Kiểm tra stats định kỳ để phát hiện drift
4. **Backup**: State file được lưu tự động, nên backup định kỳ
5. **A/B testing**: So sánh với static threshold trước khi deploy full

## Troubleshooting

**Epsilon quá cao**: Nếu epsilon > 0.2 sau nhiều calls, kiểm tra reward signals
**Threshold không đổi**: Xem logs để đảm bảo feedback đang được gửi đúng
**Performance giảm**: Có thể cần retrain model base hoặc thêm dữ liệu training

## Future Improvements

1. **Contextual features**: Thêm time-of-day, customer segment vào context
2. **Thompson Sampling**: Thay epsilon-greedy bằng Bayesian approach
3. **Multi-armed contextual**: Học cả intent+threshold jointly
4. **Online learning**: Fine-tune model weights dựa trên RL feedback
