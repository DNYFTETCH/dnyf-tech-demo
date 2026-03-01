# deploy-edge.sh
#!/bin/bash
# One-command deploy for Raspberry Pi / Ubuntu Server

set -e
TARGET_HOST="${1:-pi@192.168.1.100}"  # Default to common Pi IP

echo "🚀 Deploying DNYF TECH to $TARGET_HOST"

# 1. Sync code (exclude large models)
rsync -avz --exclude='models/*.gguf' --exclude='*.pyc' --exclude='__pycache__' \
  ./ $TARGET_HOST:~/dnyf-tech/

# 2. Remote setup & start
ssh $TARGET_HOST << 'EOF'
  cd ~/dnyf-tech
  bash setup-pi.sh
  # Start services (in production, use systemd)
  # llama.cpp server in background
  nohup ./llama.cpp/llama-server -m ~/models/phi-3-medium-4k-instruct.Q4_K_M.gguf \
    -p 1234 --ctx-size 4096 > logs/llama.log 2>&1 &
  # DNYF backend
  source venv/bin/activate
  nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
  echo "✅ Services started. Check logs/ and visit http://$(hostname -I | awk '{print $1}'):3000"
EOF

echo "🌐 Access DNYF TECH at: http://$(echo $TARGET_HOST | cut -d@ -f2):3000"
