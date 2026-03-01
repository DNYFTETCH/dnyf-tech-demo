# scripts/test-edge.sh
#!/bin/bash
echo "🧪 DNYF TECH Edge Validation Suite"

# 1. Health checks
echo -n "🔍 Backend health... "
curl -s http://localhost:8000/api/health | grep -q '"status":"ok"' && echo "✅" || echo "❌"

echo -n "🔍 LLM server health... "  
curl -s http://localhost:1234/health | grep -q '"status":"ok"' && echo "✅" || echo "❌"

# 2. Memory usage check
echo "📊 Memory usage:"
free -h | grep Mem

# 3. Simple task execution test
echo "🚀 Running smoke test task..."
TASK_ID=$(curl -s -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{"goal": "Create a hello_world.py file", "mock_mode": true}' \
  | jq -r .task_id)

# Poll for completion (max 60s)
for i in {1..30}; do
  STATUS=$(curl -s http://localhost:8000/api/task/$TASK_ID | jq -r .status)
  if [ "$STATUS" = "completed" ]; then
    echo "✅ Smoke test passed"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "❌ Smoke test failed"
    curl -s http://localhost:8000/api/task/$TASK_ID | jq
    exit 1
  fi
  sleep 2
done

# 4. Performance baseline
echo "⏱️ Performance baseline (model load + 1 inference):"
time curl -s -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1-distill-qwen-7b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }' > /dev/null

echo "🎉 Edge validation complete!"
