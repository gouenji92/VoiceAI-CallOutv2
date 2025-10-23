# Quick Start: RL Threshold Tuning

## Chạy hệ thống

```powershell
# 1. Start API server
python -X utf8 -m uvicorn app.main:app --reload

# 2. Test một cuộc gọi đơn giản
curl -X POST http://localhost:8000/calls/webhook `
  -H "Content-Type: application/json" `
  -d '{
    "call_id": "test_001",
    "text": "Tôi muốn đặt lịch khám"
  }'

# 3. Gửi feedback (sau khi user xác nhận)
curl -X POST http://localhost:8000/feedback/rl-reward `
  -H "Content-Type: application/json" `
  -d '{
    "call_id": "test_001",
    "reward": 1.0,
    "notes": "User confirmed booking"
  }'

# 4. Xem stats
curl http://localhost:8000/feedback/rl-stats | python -m json.tool
```

## Demo workflow đầy đủ

```powershell
# Simulate 10 calls với feedback
for ($i=1; $i -le 10; $i++) {
    $call_id = "demo_call_$i"
    
    # Call API
    $response = Invoke-RestMethod `
        -Method Post `
        -Uri "http://localhost:8000/calls/webhook" `
        -Body (@{call_id=$call_id; text="Giờ làm việc của các bạn?"} | ConvertTo-Json) `
        -ContentType "application/json"
    
    # Simulate reward based on intent
    $reward = if ($response.intent -eq "hoi_gio_lam_viec") { 1.0 } else { -1.0 }
    
    # Send feedback
    Invoke-RestMethod `
        -Method Post `
        -Uri "http://localhost:8000/feedback/rl-reward" `
        -Body (@{call_id=$call_id; reward=$reward} | ConvertTo-Json) `
        -ContentType "application/json"
    
    Write-Host "Call $i completed: intent=$($response.intent), reward=$reward"
    Start-Sleep -Milliseconds 500
}
```

## Visualize results

```powershell
# Generate charts
python scripts/monitor_rl_tuner.py

# Charts được lưu vào models/
# - rl_threshold_visualization.png
# - rl_arm_performance_*.png
```

## Kiểm tra state file

```powershell
# Xem raw state
Get-Content models/rl_threshold_state.json | python -m json.tool

# Xem epsilon hiện tại
python -c "import json; print('Epsilon:', json.load(open('models/rl_threshold_state.json'))['epsilon'])"
```

## So sánh với static threshold

Để test hiệu quả RL, bật/tắt trong NLP service:

```python
# nlp_service.py, line ~155
result = process_nlp_tasks(
    text="...",
    call_id="...",
    use_rl_threshold=True  # False để dùng static threshold
)
```

Chạy benchmark:
```powershell
# A: RL enabled
python test_extended_intents.py > results_rl.txt

# B: RL disabled (edit nlp_service.py first)
python test_extended_intents.py > results_static.txt

# Compare
diff results_rl.txt results_static.txt
```
