# -*- coding: utf-8 -*-
"""
Main Script - Tự động setup tất cả servers theo PLAN_SETUP.md
"""

import sys
import time
from datetime import datetime
from ssh_manager import SSHManager
from config import SERVERS, MYSQL_CONFIG, HOSTS_ENTRY


class ServerSetup:
    def __init__(self):
        self.ssh = SSHManager()
        self.results = {}
        
    def log(self, message, level="INFO"):
        """Log với timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    # ==================== PHASE 1: Common Update ====================
    def update_and_upgrade(self, server_name):
        """apt-get update && upgrade"""
        self.log(f"📦 Updating packages trên {server_name}...")
        
        commands = [
            "export DEBIAN_FRONTEND=noninteractive",
            "apt-get update -y",
            "apt-get upgrade -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'"
        ]
        
        output, error, code = self.ssh.execute_command(" && ".join(commands), sudo=True, timeout=600)
        
        if code == 0:
            self.log(f"✅ {server_name}: Update/Upgrade thành công!")
            return True
        else:
            self.log(f"❌ {server_name}: Lỗi update - {error}", "ERROR")
            return False
    
    # ==================== PHASE 2: /etc/hosts ====================
    def setup_hosts(self, server_name):
        """Thêm entry vào /etc/hosts"""
        self.log(f"📝 Cấu hình /etc/hosts trên {server_name}...")
        
        # Check if entry already exists
        check_cmd = f"grep -q 'gitlab.vnptkiengiang.vn' /etc/hosts && echo 'EXISTS' || echo 'NOT_EXISTS'"
        output, _, _ = self.ssh.execute_command(check_cmd)
        
        if "EXISTS" in output:
            self.log(f"✅ {server_name}: Entry đã tồn tại trong /etc/hosts")
            return True
        
        # Add entry
        add_cmd = f"echo '{HOSTS_ENTRY}' >> /etc/hosts"
        output, error, code = self.ssh.execute_command(add_cmd, sudo=True)
        
        if code == 0:
            self.log(f"✅ {server_name}: Đã thêm entry vào /etc/hosts")
            return True
        else:
            self.log(f"❌ {server_name}: Lỗi cấu hình hosts - {error}", "ERROR")
            return False
    
    # ==================== PHASE 3: NGINX (PROXY) ====================
    def install_nginx(self):
        """Cài đặt Nginx latest trên PROXY server"""
        self.log("🌐 Cài đặt Nginx trên PROXY...")
        
        script = '''
export DEBIAN_FRONTEND=noninteractive

# Install dependencies
apt-get install -y curl gnupg2 ca-certificates lsb-release ubuntu-keyring

# Import nginx signing key
curl -fsSL https://nginx.org/keys/nginx_signing.key | gpg --dearmor -o /usr/share/keyrings/nginx-archive-keyring.gpg

# Add nginx repo
echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] http://nginx.org/packages/ubuntu $(lsb_release -cs) nginx" > /etc/apt/sources.list.d/nginx.list

# Set preference for nginx packages
echo -e "Package: *\\nPin: origin nginx.org\\nPin: release o=nginx\\nPin-Priority: 900\\n" > /etc/apt/preferences.d/99nginx

# Install nginx
apt-get update -y
apt-get install -y nginx

# Enable and start
systemctl enable nginx
systemctl start nginx

# Verify
nginx -v
systemctl status nginx --no-pager
'''
        
        output, error, code = self.ssh.execute_command(script, sudo=True, timeout=300)
        
        if code == 0 and "nginx version" in output:
            self.log("✅ PROXY: Nginx đã cài đặt thành công!")
            return True
        else:
            self.log(f"❌ PROXY: Lỗi cài Nginx - {error}", "ERROR")
            return False
    
    # ==================== PHASE 4: Node.js (APP) ====================
    def install_nodejs(self, server_name):
        """Cài đặt NVM, Node.js 22.x, PM2"""
        self.log(f"📦 Cài đặt Node.js stack trên {server_name}...")
        
        script = '''
export DEBIAN_FRONTEND=noninteractive

# Install build essentials
apt-get install -y curl build-essential

# Install NVM
export HOME=/home/adminsgddt
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

# Install Node.js 22
nvm install 22
nvm alias default 22
nvm use 22

# Install PM2
npm install -g pm2

# Setup PM2 startup
pm2 startup systemd -u adminsgddt --hp /home/adminsgddt

# Verify
node -v
npm -v
pm2 -v

echo "NODE_SETUP_COMPLETE"
'''
        
        output, error, code = self.ssh.execute_command(script, sudo=True, timeout=600)
        
        if "NODE_SETUP_COMPLETE" in output:
            self.log(f"✅ {server_name}: Node.js stack đã cài đặt thành công!")
            return True
        else:
            self.log(f"❌ {server_name}: Lỗi cài Node.js - {error}", "ERROR")
            return False
    
    # ==================== PHASE 5: Docker (DB) ====================
    def install_docker(self, server_name):
        """Cài đặt Docker"""
        self.log(f"🐳 Cài đặt Docker trên {server_name}...")
        
        script = '''
export DEBIAN_FRONTEND=noninteractive

# Check if docker exists
if command -v docker &> /dev/null; then
    echo "Docker already installed"
    docker --version
    echo "DOCKER_READY"
    exit 0
fi

# Install prerequisites
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repo
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list

# Install Docker
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
systemctl enable docker
systemctl start docker

# Add user to docker group
usermod -aG docker adminsgddt

docker --version
echo "DOCKER_READY"
'''
        
        output, error, code = self.ssh.execute_command(script, sudo=True, timeout=600)
        
        if "DOCKER_READY" in output:
            self.log(f"✅ {server_name}: Docker đã cài đặt thành công!")
            return True
        else:
            self.log(f"❌ {server_name}: Lỗi cài Docker - {error}", "ERROR")
            return False
    
    # ==================== PHASE 6: MySQL Docker (DB01) ====================
    def setup_mysql_docker(self):
        """Chạy MySQL container trên DB01"""
        self.log("🐬 Setup MySQL Docker trên DB01...")
        
        mysql_pass = MYSQL_CONFIG['root_password']
        volume_path = MYSQL_CONFIG['volume_path']
        container_name = MYSQL_CONFIG['container_name']
        
        script = f'''
# Create volume directory
mkdir -p {volume_path}
chmod 755 {volume_path}
chown -R 999:999 {volume_path}

# Stop and remove existing container if exists
docker stop {container_name} 2>/dev/null || true
docker rm {container_name} 2>/dev/null || true

# Pull latest MySQL
docker pull mysql:latest

# Run MySQL container
docker run -d \\
  --name {container_name} \\
  --restart always \\
  -p 3306:3306 \\
  -e MYSQL_ROOT_PASSWORD={mysql_pass} \\
  -v {volume_path}:/var/lib/mysql \\
  mysql:latest

# Wait for MySQL to start
sleep 10

# Verify
docker ps | grep {container_name}
echo "MYSQL_READY"
'''
        
        output, error, code = self.ssh.execute_command(script, sudo=True, timeout=300)
        
        if "MYSQL_READY" in output:
            self.log("✅ DB01: MySQL Docker đã chạy thành công!")
            return True
        else:
            self.log(f"❌ DB01: Lỗi setup MySQL - {error}", "ERROR")
            return False
    
    # ==================== PHASE 7: Backup Sync (DB02) ====================
    def setup_backup_sync(self):
        """Setup backup sync job trên DB02"""
        self.log("📦 Setup Backup Sync trên DB02...")
        
        db01_ip = SERVERS['DB01']['ip']
        db01_pass = SERVERS['DB01']['password']
        
        script = f'''
# Install rsync and sshpass
apt-get install -y rsync sshpass

# Create backup directory
mkdir -p /home/mysql-backup
mkdir -p /opt/scripts
mkdir -p /var/log/mysql-backup

# Create backup script
cat > /opt/scripts/mysql_backup_sync.sh << 'SCRIPT'
#!/bin/bash
# MySQL Backup Sync Script
# Sync từ DB01 tới DB02

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/mysql-backup/sync_$TIMESTAMP.log"
DB01_IP="{db01_ip}"
DB01_USER="adminsgddt"
DB01_PASS="{db01_pass}"
SOURCE_PATH="/home/mysql"
DEST_PATH="/home/mysql-backup"

echo "[$TIMESTAMP] Starting backup sync from DB01..." >> $LOG_FILE

# Sync using rsync over SSH with sshpass
sshpass -p "$DB01_PASS" rsync -avz --delete \\
  -e "ssh -o StrictHostKeyChecking=no" \\
  $DB01_USER@$DB01_IP:$SOURCE_PATH/ \\
  $DEST_PATH/ >> $LOG_FILE 2>&1

if [ $? -eq 0 ]; then
    echo "[$TIMESTAMP] Backup sync completed successfully!" >> $LOG_FILE
else
    echo "[$TIMESTAMP] Backup sync failed!" >> $LOG_FILE
fi

# Cleanup old logs (keep last 30 days)
find /var/log/mysql-backup -name "sync_*.log" -mtime +30 -delete
SCRIPT

# Make executable
chmod +x /opt/scripts/mysql_backup_sync.sh

# Setup crontab - every 6 hours
(crontab -l 2>/dev/null | grep -v mysql_backup_sync; echo "0 */6 * * * /opt/scripts/mysql_backup_sync.sh") | crontab -

# Verify crontab
crontab -l

echo "BACKUP_SETUP_COMPLETE"
'''
        
        output, error, code = self.ssh.execute_command(script, sudo=True, timeout=300)
        
        if "BACKUP_SETUP_COMPLETE" in output:
            self.log("✅ DB02: Backup Sync đã setup thành công!")
            return True
        else:
            self.log(f"❌ DB02: Lỗi setup Backup - {error}", "ERROR")
            return False
    
    # ==================== MAIN EXECUTION ====================
    def run_all(self):
        """Chạy toàn bộ setup"""
        self.log("=" * 60)
        self.log("🚀 BẮT ĐẦU SETUP SERVERS SGDDT INFRASTRUCTURE")
        self.log("=" * 60)
        
        # Connect to Jump Host
        if not self.ssh.connect_jump_host():
            self.log("❌ Không thể kết nối Jump Host. Dừng setup.", "ERROR")
            return False
        
        # ========== PHASE 1 & 2: Update + Hosts cho tất cả servers ==========
        self.log("\n" + "=" * 40)
        self.log("📦 PHASE 1 & 2: Update packages & Configure /etc/hosts")
        self.log("=" * 40)
        
        for server_name in SERVERS:
            self.log(f"\n--- Processing {server_name} ---")
            if self.ssh.connect_target_server(server_name):
                self.update_and_upgrade(server_name)
                self.setup_hosts(server_name)
                self.ssh.close_target()
            else:
                self.log(f"❌ Không thể kết nối {server_name}", "ERROR")
        
        # ========== PHASE 3: NGINX cho PROXY ==========
        self.log("\n" + "=" * 40)
        self.log("🌐 PHASE 3: Cài đặt NGINX trên PROXY")
        self.log("=" * 40)
        
        if self.ssh.connect_target_server("PROXY"):
            self.install_nginx()
            self.ssh.close_target()
        
        # ========== PHASE 4: Node.js cho APP servers ==========
        self.log("\n" + "=" * 40)
        self.log("📦 PHASE 4: Cài đặt Node.js trên APP servers")
        self.log("=" * 40)
        
        for server_name in ["APP01", "APP02"]:
            if self.ssh.connect_target_server(server_name):
                self.install_nodejs(server_name)
                self.ssh.close_target()
        
        # ========== PHASE 5 & 6: Docker + MySQL cho DB01 ==========
        self.log("\n" + "=" * 40)
        self.log("🐳 PHASE 5 & 6: Docker + MySQL trên DB01")
        self.log("=" * 40)
        
        if self.ssh.connect_target_server("DB01"):
            self.install_docker("DB01")
            self.setup_mysql_docker()
            self.ssh.close_target()
        
        # ========== PHASE 7: Docker + Backup cho DB02 ==========
        self.log("\n" + "=" * 40)
        self.log("📦 PHASE 7: Docker + Backup Sync trên DB02")
        self.log("=" * 40)
        
        if self.ssh.connect_target_server("DB02"):
            self.install_docker("DB02")
            self.setup_backup_sync()
            self.ssh.close_target()
        
        # ========== DONE ==========
        self.ssh.close_all()
        
        self.log("\n" + "=" * 60)
        self.log("🎉 HOÀN THÀNH SETUP TẤT CẢ SERVERS!")
        self.log("=" * 60)
        
        return True


if __name__ == "__main__":
    setup = ServerSetup()
    setup.run_all()
