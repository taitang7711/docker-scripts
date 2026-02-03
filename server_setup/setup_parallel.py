# -*- coding: utf-8 -*-
"""
Setup All Servers - MULTI-THREADED VERSION
Chạy song song tất cả các tasks
"""

import paramiko
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Config
JUMP_HOST = ('127.0.0.1', 2222, 'adminsgddt', 'vnpt@123')
HOSTS_ENTRY = "113.163.158.54 gitlab.vnptkiengiang.vn"

SERVERS = {
    "APP01": {"ip": "10.67.2.11", "role": "app"},
    "APP02": {"ip": "10.67.2.12", "role": "app"},
    "DB01": {"ip": "10.68.2.11", "role": "db_master"},
    "DB02": {"ip": "10.68.2.12", "role": "db_backup"},
}

# Lock for print
print_lock = threading.Lock()

def log(server, msg):
    with print_lock:
        print(f"[{server}] {msg}")

def get_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(JUMP_HOST[0], port=JUMP_HOST[1], username=JUMP_HOST[2], password=JUMP_HOST[3], timeout=60)
    return client

def run_cmd(client, ip, cmd, timeout=300):
    password = 'vnpt@123'
    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    try:
        stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
        output = stdout.read().decode('utf-8', errors='ignore')
        code = stdout.channel.recv_exit_status()
        return output, code
    except Exception as e:
        return str(e), -1

# ==================== SCRIPTS ====================

NODEJS_SCRIPT = '''
export DEBIAN_FRONTEND=noninteractive
export HOME=/home/adminsgddt
apt-get install -y curl build-essential
su - adminsgddt -c "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash"
cat > /tmp/install_node.sh << 'EOF'
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install 22
nvm alias default 22
npm install -g pm2
node -v && npm -v && pm2 -v
EOF
su - adminsgddt -c "bash /tmp/install_node.sh"
echo "NODE_COMPLETE"
'''

DOCKER_SCRIPT = '''
export DEBIAN_FRONTEND=noninteractive
if command -v docker &> /dev/null; then
    echo "Docker exists"
    docker --version
else
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
echo "DOCKER_COMPLETE"
'''

MYSQL_SCRIPT = '''
mkdir -p /home/mysql
chmod 755 /home/mysql
docker stop mysql-master 2>/dev/null || true
docker rm mysql-master 2>/dev/null || true
docker run -d --name mysql-master --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=Sgdt@2026 -v /home/mysql:/var/lib/mysql mysql:latest
sleep 10
docker ps | grep mysql
echo "MYSQL_COMPLETE"
'''

BACKUP_SCRIPT = '''
apt-get install -y rsync sshpass
mkdir -p /home/mysql-backup /opt/scripts /var/log/mysql-backup
cat > /opt/scripts/mysql_backup_sync.sh << 'BKSCRIPT'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="/var/log/mysql-backup/sync_$TIMESTAMP.log"
sshpass -p "vnpt@123" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" adminsgddt@10.68.2.11:/home/mysql/ /home/mysql-backup/ >> $LOG 2>&1
echo "[$TIMESTAMP] Done" >> $LOG
BKSCRIPT
chmod +x /opt/scripts/mysql_backup_sync.sh
(crontab -l 2>/dev/null | grep -v mysql_backup; echo "0 */6 * * * /opt/scripts/mysql_backup_sync.sh") | crontab -
crontab -l
echo "BACKUP_COMPLETE"
'''

# ==================== WORKER FUNCTIONS ====================

def setup_app_server(name, ip):
    """Setup APP server: hosts + nodejs"""
    log(name, "🚀 Starting setup...")
    client = get_client()
    
    # Hosts
    log(name, "📝 Configuring /etc/hosts...")
    out, _ = run_cmd(client, ip, f"grep -q gitlab.vnptkiengiang.vn /etc/hosts || echo '{HOSTS_ENTRY}' >> /etc/hosts", timeout=30)
    log(name, "✅ /etc/hosts done")
    
    # Node.js
    log(name, "📦 Installing NVM + Node.js 22 + PM2...")
    out, code = run_cmd(client, ip, NODEJS_SCRIPT.replace("'", "'\"'\"'"), timeout=600)
    
    if "NODE_COMPLETE" in out:
        log(name, "✅ Node.js stack installed!")
    else:
        log(name, f"⚠️ Node.js issue: {out[-200:]}")
    
    client.close()
    return f"{name}: OK"

def setup_db01(name, ip):
    """Setup DB01: hosts + docker + mysql"""
    log(name, "🚀 Starting setup...")
    client = get_client()
    
    # Hosts
    log(name, "📝 Configuring /etc/hosts...")
    run_cmd(client, ip, f"grep -q gitlab.vnptkiengiang.vn /etc/hosts || echo '{HOSTS_ENTRY}' >> /etc/hosts", timeout=30)
    log(name, "✅ /etc/hosts done")
    
    # Docker
    log(name, "🐳 Installing Docker...")
    out, code = run_cmd(client, ip, DOCKER_SCRIPT.replace("'", "'\"'\"'"), timeout=600)
    if "DOCKER_COMPLETE" in out:
        log(name, "✅ Docker installed!")
    else:
        log(name, f"⚠️ Docker issue: {out[-200:]}")
    
    # MySQL
    log(name, "🐬 Starting MySQL container...")
    out, code = run_cmd(client, ip, MYSQL_SCRIPT.replace("'", "'\"'\"'"), timeout=300)
    if "MYSQL_COMPLETE" in out:
        log(name, "✅ MySQL running!")
    else:
        log(name, f"⚠️ MySQL issue: {out[-200:]}")
    
    client.close()
    return f"{name}: OK"

def setup_db02(name, ip):
    """Setup DB02: hosts + docker + backup"""
    log(name, "🚀 Starting setup...")
    client = get_client()
    
    # Hosts
    log(name, "📝 Configuring /etc/hosts...")
    run_cmd(client, ip, f"grep -q gitlab.vnptkiengiang.vn /etc/hosts || echo '{HOSTS_ENTRY}' >> /etc/hosts", timeout=30)
    log(name, "✅ /etc/hosts done")
    
    # Docker
    log(name, "🐳 Installing Docker...")
    out, code = run_cmd(client, ip, DOCKER_SCRIPT.replace("'", "'\"'\"'"), timeout=600)
    if "DOCKER_COMPLETE" in out:
        log(name, "✅ Docker installed!")
    else:
        log(name, f"⚠️ Docker issue: {out[-200:]}")
    
    # Backup
    log(name, "📦 Setting up backup sync...")
    out, code = run_cmd(client, ip, BACKUP_SCRIPT.replace("'", "'\"'\"'"), timeout=180)
    if "BACKUP_COMPLETE" in out:
        log(name, "✅ Backup sync configured!")
    else:
        log(name, f"⚠️ Backup issue: {out[-200:]}")
    
    client.close()
    return f"{name}: OK"

# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MULTI-THREADED SERVER SETUP")
    print("=" * 60)
    print("Running ALL servers in PARALLEL!\n")
    
    start_time = time.time()
    
    # Run all in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(setup_app_server, "APP01", "10.67.2.11"): "APP01",
            executor.submit(setup_app_server, "APP02", "10.67.2.12"): "APP02",
            executor.submit(setup_db01, "DB01", "10.68.2.11"): "DB01",
            executor.submit(setup_db02, "DB02", "10.68.2.12"): "DB02",
        }
        
        results = []
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                log(name, f"❌ Error: {e}")
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETED!")
    print("=" * 60)
    print(f"⏱️  Total time: {elapsed:.1f} seconds")
    print(f"\n📋 Results:")
    for r in results:
        print(f"   ✅ {r}")
    
    print("""
📋 MySQL Credentials (DB01):
   Host: 10.68.2.11:3306
   User: root
   Pass: Sgdt@2026

📋 Backup (DB02):
   Schedule: Every 6 hours
   Script: /opt/scripts/mysql_backup_sync.sh
""")
