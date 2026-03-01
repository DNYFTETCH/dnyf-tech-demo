# security/harden-pi.sh
#!/bin/bash
echo "🔒 Hardening DNYF TECH Edge Deployment"

# 1. Firewall: Only allow local access
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 127.0.0.1 to any port 8000  # Backend
sudo ufw allow from 127.0.0.1 to any port 1234  # LLM server
sudo ufw allow from 192.168.1.0/24 to any port 3000  # Frontend (adjust subnet)
sudo ufw enable

# 2. Non-root execution (already in Dockerfile.edge, but verify)
if [ "$(id -u)" -eq 0 ]; then
    echo "❌ Do not run DNYF as root. Use: sudo -u dnyf ..."
    exit 1
fi

# 3. File permissions
chmod 700 ~/dnyf-tech/workspace
chmod 600 ~/dnyf-tech/.env
find ~/dnyf-tech/logs -type f -exec chmod 600 {} \;

# 4. Disable unused services
sudo systemctl disable bluetooth avahi-daemon

# 5. Auto-updates for security patches
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades  # Enable auto-updates

# 6. Audit logging
sudo apt install -y auditd
sudo auditctl -w /home/pi/dnyf-tech/workspace -p wa -k dnyf_workspace

echo "✅ Hardening complete. Review: sudo auditctl -l"
