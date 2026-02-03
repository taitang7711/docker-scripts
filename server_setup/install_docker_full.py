# Debug and fix Docker installation
import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=30)

def run_sudo(ip, cmd, timeout=600):
    password = 'vnpt@123'
    ssh_cmd = f"sshpass -p '{password}' ssh -t -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    return out + err

print("=" * 60)
print("🐳 INSTALLING DOCKER ON DB01 & DB02")
print("=" * 60)

docker_script = """
export DEBIAN_FRONTEND=noninteractive

# Remove old docker if exists
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Install prerequisites
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker GPG key
mkdir -p /etc/apt/keyrings
rm -f /etc/apt/keyrings/docker.gpg
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repo
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list

# Install Docker
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
systemctl enable docker
systemctl start docker

# Verify
docker --version
echo "DOCKER_INSTALL_COMPLETE"
"""

for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    print(f"\n[{name}] Installing Docker...")
    out = run_sudo(ip, docker_script.replace("'", "'\"'\"'"), timeout=600)
    
    if "DOCKER_INSTALL_COMPLETE" in out:
        # Get version line
        for line in out.split('\n'):
            if "Docker version" in line:
                print(f"[{name}] ✅ {line.strip()}")
                break
    else:
        print(f"[{name}] Output (last 500 chars):")
        print(out[-500:])

print("\n" + "=" * 60)
print("🐬 STARTING MYSQL ON DB01")
print("=" * 60)

mysql_script = """
mkdir -p /home/mysql
chmod 755 /home/mysql

# Stop/remove existing
docker stop mysql-master 2>/dev/null || true
docker rm mysql-master 2>/dev/null || true

# Pull and run
docker pull mysql:latest
docker run -d \\
  --name mysql-master \\
  --restart always \\
  -p 3306:3306 \\
  -e MYSQL_ROOT_PASSWORD=Sgdt@2026 \\
  -v /home/mysql:/var/lib/mysql \\
  mysql:latest

sleep 15
docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}" | grep mysql
echo "MYSQL_COMPLETE"
"""

out = run_sudo("10.68.2.11", mysql_script.replace("'", "'\"'\"'"), timeout=300)
if "MYSQL_COMPLETE" in out:
    for line in out.split('\n'):
        if "mysql" in line.lower():
            print(f"[DB01] ✅ {line.strip()}")
else:
    print(f"[DB01] Output: {out[-400:]}")

print("\n" + "=" * 60)
print("📦 SETTING UP BACKUP CRON ON DB02")
print("=" * 60)

backup_script = """
apt-get install -y rsync sshpass

mkdir -p /home/mysql-backup
mkdir -p /opt/scripts
mkdir -p /var/log/mysql-backup

cat > /opt/scripts/mysql_backup_sync.sh << 'ENDSCRIPT'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="/var/log/mysql-backup/sync_$TIMESTAMP.log"
echo "[$TIMESTAMP] Starting backup..." >> $LOG
sshpass -p "vnpt@123" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" adminsgddt@10.68.2.11:/home/mysql/ /home/mysql-backup/ >> $LOG 2>&1
echo "[$TIMESTAMP] Completed" >> $LOG
ENDSCRIPT

chmod +x /opt/scripts/mysql_backup_sync.sh

# Setup cron
(crontab -l 2>/dev/null | grep -v mysql_backup_sync; echo "0 */6 * * * /opt/scripts/mysql_backup_sync.sh") | crontab -

# Verify
ls -la /opt/scripts/mysql_backup_sync.sh
crontab -l | grep mysql
echo "BACKUP_COMPLETE"
"""

out = run_sudo("10.68.2.12", backup_script, timeout=120)
if "BACKUP_COMPLETE" in out:
    print("[DB02] ✅ Backup cron configured!")
    for line in out.split('\n'):
        if "mysql" in line.lower() or "/opt/scripts" in line:
            print(f"   {line.strip()}")
else:
    print(f"[DB02] Output: {out[-300:]}")

client.close()
print("\n✅ Done!")
