# Kill apt locks and install Docker
import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

def run_cmd(ip, cmd, timeout=300):
    password = 'vnpt@123'
    full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    try:
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode()
        return out
    except:
        return ""

print("=" * 60)
print("🔓 KILLING APT LOCKS ON DB SERVERS")
print("=" * 60)

for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    print(f"\n[{name}] Killing apt processes...")
    
    # Kill all apt processes
    run_cmd(ip, "pkill -9 apt; pkill -9 dpkg; pkill -9 apt-get", timeout=30)
    time.sleep(2)
    
    # Remove lock files
    run_cmd(ip, "rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock /var/lib/apt/lists/lock", timeout=30)
    
    # Fix dpkg
    run_cmd(ip, "dpkg --configure -a", timeout=60)
    
    print(f"[{name}] Locks cleared!")

print("\n" + "=" * 60)
print("🐳 INSTALLING DOCKER")
print("=" * 60)

for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    print(f"\n[{name}] Installing Docker...")
    
    # Install Docker packages
    out = run_cmd(ip, "DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin", timeout=600)
    
    if "Setting up docker" in out or "docker-ce is already" in out:
        print(f"[{name}] Docker packages installed!")
    else:
        print(f"[{name}] Output: {out[-200:]}")
    
    # Start service
    run_cmd(ip, "systemctl enable docker", timeout=30)
    run_cmd(ip, "systemctl start docker", timeout=30)
    
    # Verify
    out = run_cmd(ip, "docker --version", timeout=30)
    if "Docker version" in out:
        print(f"[{name}] ✅ {out.strip()}")
    else:
        print(f"[{name}] ⚠️ Docker check: {out}")

# MySQL on DB01
print("\n" + "=" * 60)
print("🐬 MYSQL ON DB01")
print("=" * 60)

run_cmd("10.68.2.11", "mkdir -p /home/mysql", timeout=20)
run_cmd("10.68.2.11", "docker stop mysql-master || true; docker rm mysql-master || true", timeout=30)

print("Pulling and starting MySQL...")
out = run_cmd("10.68.2.11", "docker run -d --name mysql-master --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=Sgdt@2026 -v /home/mysql:/var/lib/mysql mysql:latest", timeout=180)

time.sleep(15)
out = run_cmd("10.68.2.11", "docker ps | grep mysql", timeout=30)
if "mysql-master" in out:
    print(f"✅ MySQL running: {out.strip()}")
else:
    print(f"⚠️ MySQL: {out}")

# Backup cron on DB02
print("\n" + "=" * 60)
print("📦 BACKUP CRON ON DB02")
print("=" * 60)

# Write proper backup script
backup_lines = [
    '#!/bin/bash',
    'TIMESTAMP=$(date +%Y%m%d_%H%M%S)',
    'LOG="/var/log/mysql-backup/sync_$TIMESTAMP.log"',
    'echo "[$TIMESTAMP] Starting..." >> $LOG',
    'sshpass -p "vnpt@123" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" adminsgddt@10.68.2.11:/home/mysql/ /home/mysql-backup/ >> $LOG 2>&1',
    'echo "[$TIMESTAMP] Done" >> $LOG'
]

# Clear and rewrite
run_cmd("10.68.2.12", "rm -f /opt/scripts/mysql_backup_sync.sh", timeout=20)
for line in backup_lines:
    escaped = line.replace('$', '\\$').replace('"', '\\"')
    run_cmd("10.68.2.12", f"echo \"{escaped}\" >> /opt/scripts/mysql_backup_sync.sh", timeout=20)

run_cmd("10.68.2.12", "chmod +x /opt/scripts/mysql_backup_sync.sh", timeout=20)

# Setup cron
run_cmd("10.68.2.12", "(crontab -l 2>/dev/null | grep -v mysql_backup; echo '0 */6 * * * /opt/scripts/mysql_backup_sync.sh') | crontab -", timeout=30)

# Verify
out = run_cmd("10.68.2.12", "crontab -l 2>/dev/null | grep mysql", timeout=20)
if "mysql_backup" in out:
    print(f"✅ Cron: {out.strip()}")
else:
    print(f"⚠️ Cron issue")

out = run_cmd("10.68.2.12", "head -3 /opt/scripts/mysql_backup_sync.sh", timeout=20)
print(f"Script content: {out.strip()[:100]}")

client.close()
print("\n✅ Done!")
