# -*- coding: utf-8 -*-
"""
Setup All Servers - Skip PROXY, Skip Upgrade
"""

import paramiko
import time

def get_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)
    return client

def run_cmd(client, ip, cmd, timeout=120):
    """Run command with sudo"""
    password = 'vnpt@123'
    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    
    try:
        stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        code = stdout.channel.recv_exit_status()
        return output, error, code
    except Exception as e:
        return "", str(e), -1

SERVERS = {
    "APP01": "10.67.2.11",
    "APP02": "10.67.2.12",
    "DB01": "10.68.2.11",
    "DB02": "10.68.2.12",
}

HOSTS_ENTRY = "113.163.158.54 gitlab.vnptkiengiang.vn"

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SETUP SERVERS - SGDDT INFRASTRUCTURE")
    print("=" * 60)
    
    client = get_client()
    print("✅ Connected to Jump Host!\n")
    
    # ========== PHASE 2: /etc/hosts ==========
    print("=" * 60)
    print("📝 PHASE 2: Configure /etc/hosts")
    print("=" * 60)
    
    for name, ip in SERVERS.items():
        # Check if exists
        out, _, _ = run_cmd(client, ip, "grep -q gitlab.vnptkiengiang.vn /etc/hosts && echo EXISTS || echo NOT_EXISTS", timeout=30)
        
        if "EXISTS" in out:
            print(f"✅ {name}: Entry already exists")
        else:
            # Add entry
            out, err, code = run_cmd(client, ip, f"echo '{HOSTS_ENTRY}' >> /etc/hosts", timeout=30)
            if code == 0:
                print(f"✅ {name}: Added hosts entry")
            else:
                print(f"❌ {name}: Failed - {err[:100]}")
    
    # Verify
    print("\n📋 Verifying /etc/hosts:")
    for name, ip in SERVERS.items():
        out, _, _ = run_cmd(client, ip, "grep gitlab /etc/hosts", timeout=30)
        print(f"   {name}: {out.strip()}")
    
    # ========== PHASE 3: Node.js on APP servers ==========
    print("\n" + "=" * 60)
    print("📦 PHASE 3: Install Node.js (NVM + Node 22 + PM2) on APP servers")
    print("=" * 60)
    
    nodejs_script = '''
export DEBIAN_FRONTEND=noninteractive
export HOME=/home/adminsgddt

# Install curl if not exists
apt-get install -y curl build-essential

# Install NVM for user adminsgddt
su - adminsgddt -c "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash"

# Create script to install node
cat > /tmp/install_node.sh << 'EOF'
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install 22
nvm alias default 22
nvm use 22
npm install -g pm2
node -v
npm -v
pm2 -v
EOF

# Run as adminsgddt
su - adminsgddt -c "bash /tmp/install_node.sh"

echo "NODE_INSTALL_COMPLETE"
'''
    
    for name in ["APP01", "APP02"]:
        ip = SERVERS[name]
        print(f"\n🔧 Installing on {name} ({ip})...")
        
        out, err, code = run_cmd(client, ip, nodejs_script.replace("'", "'\"'\"'"), timeout=300)
        
        if "NODE_INSTALL_COMPLETE" in out:
            # Extract versions
            lines = out.split('\n')
            for line in lines[-10:]:
                if line.startswith('v') or 'pm2' in line.lower():
                    print(f"   {line.strip()}")
            print(f"✅ {name}: Node.js stack installed!")
        else:
            print(f"⚠️ {name}: Check output")
            print(out[-500:] if out else err[-300:])
    
    # ========== PHASE 4: Docker + MySQL on DB01 ==========
    print("\n" + "=" * 60)
    print("🐳 PHASE 4: Install Docker + MySQL on DB01")
    print("=" * 60)
    
    docker_script = '''
export DEBIAN_FRONTEND=noninteractive

# Check if docker exists
if command -v docker &> /dev/null; then
    echo "Docker already installed"
    docker --version
else
    # Install Docker
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    usermod -aG docker adminsgddt
fi

docker --version
echo "DOCKER_READY"
'''

    mysql_script = '''
# Create volume directory
mkdir -p /home/mysql
chmod 755 /home/mysql

# Stop and remove existing container
docker stop mysql-master 2>/dev/null || true
docker rm mysql-master 2>/dev/null || true

# Run MySQL container
docker run -d \
  --name mysql-master \
  --restart always \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=Sgdt@2026 \
  -v /home/mysql:/var/lib/mysql \
  mysql:latest

# Wait for startup
sleep 15

# Verify
docker ps | grep mysql-master
echo "MYSQL_READY"
'''
    
    ip = SERVERS["DB01"]
    print(f"\n🔧 Installing Docker on DB01 ({ip})...")
    out, err, code = run_cmd(client, ip, docker_script.replace("'", "'\"'\"'"), timeout=300)
    
    if "DOCKER_READY" in out:
        print(f"✅ DB01: Docker installed!")
        # Get version
        for line in out.split('\n'):
            if 'Docker version' in line:
                print(f"   {line.strip()}")
    else:
        print(f"⚠️ Output: {out[-300:]}")
    
    print(f"\n🐬 Starting MySQL container on DB01...")
    out, err, code = run_cmd(client, ip, mysql_script.replace("'", "'\"'\"'"), timeout=180)
    
    if "MYSQL_READY" in out:
        print(f"✅ DB01: MySQL container running!")
        for line in out.split('\n'):
            if 'mysql-master' in line:
                print(f"   {line.strip()}")
    else:
        print(f"⚠️ Output: {out[-300:]}")
    
    # ========== PHASE 5: Docker + Backup on DB02 ==========
    print("\n" + "=" * 60)
    print("📦 PHASE 5: Install Docker + Backup Sync on DB02")
    print("=" * 60)
    
    ip = SERVERS["DB02"]
    print(f"\n🔧 Installing Docker on DB02 ({ip})...")
    out, err, code = run_cmd(client, ip, docker_script.replace("'", "'\"'\"'"), timeout=300)
    
    if "DOCKER_READY" in out:
        print(f"✅ DB02: Docker installed!")
    else:
        print(f"⚠️ Output: {out[-300:]}")
    
    backup_script = '''
# Install rsync and sshpass
apt-get install -y rsync sshpass

# Create directories
mkdir -p /home/mysql-backup
mkdir -p /opt/scripts
mkdir -p /var/log/mysql-backup

# Create backup script
cat > /opt/scripts/mysql_backup_sync.sh << 'BACKUPSCRIPT'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/mysql-backup/sync_$TIMESTAMP.log"
DB01_IP="10.68.2.11"
DB01_USER="adminsgddt"
DB01_PASS="vnpt@123"
SOURCE_PATH="/home/mysql"
DEST_PATH="/home/mysql-backup"

echo "[$TIMESTAMP] Starting backup sync from DB01..." >> $LOG_FILE

sshpass -p "$DB01_PASS" rsync -avz --delete \
  -e "ssh -o StrictHostKeyChecking=no" \
  $DB01_USER@$DB01_IP:$SOURCE_PATH/ \
  $DEST_PATH/ >> $LOG_FILE 2>&1

if [ $? -eq 0 ]; then
    echo "[$TIMESTAMP] Backup sync completed!" >> $LOG_FILE
else
    echo "[$TIMESTAMP] Backup sync failed!" >> $LOG_FILE
fi

find /var/log/mysql-backup -name "sync_*.log" -mtime +30 -delete
BACKUPSCRIPT

chmod +x /opt/scripts/mysql_backup_sync.sh

# Setup crontab - every 6 hours
(crontab -l 2>/dev/null | grep -v mysql_backup_sync; echo "0 */6 * * * /opt/scripts/mysql_backup_sync.sh") | crontab -

# Show crontab
crontab -l

echo "BACKUP_SETUP_COMPLETE"
'''
    
    print(f"\n📦 Setting up backup sync on DB02...")
    out, err, code = run_cmd(client, ip, backup_script.replace("'", "'\"'\"'"), timeout=120)
    
    if "BACKUP_SETUP_COMPLETE" in out:
        print(f"✅ DB02: Backup sync configured!")
        # Show crontab
        for line in out.split('\n'):
            if 'mysql_backup' in line:
                print(f"   Crontab: {line.strip()}")
    else:
        print(f"⚠️ Output: {out[-300:]}")
    
    client.close()
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETED!")
    print("=" * 60)
    print("""
✅ Phase 2: /etc/hosts configured on all servers
✅ Phase 3: Node.js (NVM + Node 22 + PM2) on APP01, APP02
✅ Phase 4: Docker + MySQL on DB01
✅ Phase 5: Docker + Backup Sync on DB02

⚠️  SKIPPED:
- PROXY server (not accessible)
- apt-get upgrade (as requested)

📋 MySQL Credentials (DB01):
   Host: 10.68.2.11
   Port: 3306
   User: root
   Pass: Sgdt@2026

📋 Backup Schedule (DB02):
   Every 6 hours (0 */6 * * *)
   Script: /opt/scripts/mysql_backup_sync.sh
   Logs: /var/log/mysql-backup/
""")
