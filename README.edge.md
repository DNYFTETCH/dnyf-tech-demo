## ✅ Pre-Deployment
- [ ] Choose model based on RAM: `phi-3` (4GB), `deepseek-7b` (8GB), `llama-8b` (12GB+)
- [ ] Download GGUF model on desktop (faster), copy to edge device via USB/SCP
- [ ] Verify llama.cpp server builds on target hardware (`make -j4`)

## ✅ Deployment
- [ ] Run `setup-pi.sh` or equivalent for your OS
- [ ] Configure `.env` with edge-optimized settings
- [ ] Start llama.cpp server: `./llama-server -m model.gguf -p 1234`
- [ ] Start DNYF backend: `uvicorn backend.main:app --port 8000`
- [ ] Serve frontend via nginx or `python -m http.server 3000`

## ✅ Validation
- [ ] `curl http://localhost:8000/api/health` → `{"status":"ok"}`
- [ ] `curl http://localhost:1234/health` → LLM server ready
- [ ] Submit test task via UI or API
- [ ] Monitor RAM: `free -h` (keep <90% usage)
- [ ] Check logs: `tail -f logs/backend.log`

## ✅ Maintenance
- [ ] Rotate logs: `logrotate` config for `/home/pi/dnyf-tech/logs/*.log`
- [ ] Update models quarterly for better performance
- [ ] Monitor SD card health: `sudo smartctl -a /dev/mmcblk0`
- [ ] Backup workspace: `rsync -a ~/dnyf-tech/workspace/ /backup/location/`
