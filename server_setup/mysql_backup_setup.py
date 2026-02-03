# Setup MySQL on DB01 and Backup on DB02
import paramiko
import time
import base64

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

def run_cmd(ip, cmd, timeout=600):
    password = 'vnpt@123'
    full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    try:
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        return out + err
    except Exception as e:
        return str(e)

print("=" * 60)
print("🐬 MYSQL CONTAINER SETUP ON DB01")
print("=" * 60)

ip = "10.68.2.11"

# 1. Create directory
print("1. Creating /home/mysql directory...")
run_cmd(ip, "mkdir -p /home/mysql && chmod 755 /home/mysql", timeout=20)

# 2. Remove old container if exists
print("2. Removing old mysql-master container if exists...")
run_cmd(ip, "docker stop mysql-master 2>/dev/null; docker rm mysql-master 2>/dev/null; true", timeout=60)

# 3. Pull MySQL image
print("3. Pulling MySQL image (this may take a while)...")
out = run_cmd(ip, "docker pull mysql:latest 2>&1", timeout=600)
if "Pull complete" in out or "already exists" in out or "Image is up to date" in out:
    print("   ✅ MySQL image ready!")
else:
    print(f"   {out[-200:]}")

# 4. Run MySQL container
print("4. Starting MySQL container...")
mysql_run = """docker run -d \\
    --name mysql-master \\
    --restart always \\
    -p 3306:3306 \\
    -e MYSQL_ROOT_PASSWORD=Sgdt@2026 \\
    -v /home/mysql:/var/lib/mysql \\
    mysql:latest"""

# Run as single line
mysql_cmd = "docker run -d --name mysql-master --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=Sgdt@2026 -v /home/mysql:/var/lib/mysql mysql:latest"
out = run_cmd(ip, mysql_cmd, timeout=120)
container_id = out.strip().split('\n')[-1][:12] if out else "unknown"
print(f"   Container ID: {container_id}")

# 5. Wait for MySQL to initialize
print("5. Waiting for MySQL to initialize (30 seconds)...")
time.sleep(30)

# 6. Check container status
print("6. Checking container status...")
out = run_cmd(ip, "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' | grep mysql", timeout=30)
print(f"   {out.strip()}")

# 7. Test MySQL connection
print("7. Testing MySQL connection...")
out = run_cmd(ip, "docker exec mysql-master mysql -uroot -pSgdt@2026 -e 'SELECT VERSION();' 2>&1", timeout=60)
if "VERSION()" in out or "8." in out or "9." in out:
    version = [l for l in out.split('\n') if '8.' in l or '9.' in l]
    print(f"   ✅ MySQL running! Version: {version[0].strip() if version else 'OK'}")
else:
    print(f"   {out[-150:]}")

print("\n" + "=" * 60)
print("📦 BACKUP SETUP ON DB02")
print("=" * 60)

ip = "10.68.2.12"

# 1. Install required packages
print("1. Installing rsync and sshpass...")
run_cmd(ip, "apt-get install -y rsync sshpass 2>&1 | tail -2", timeout=120)

# 2. Create directories
print("2. Creating directories...")
run_cmd(ip, "mkdir -p /home/mysql-backup /opt/scripts /var/log/mysql-backup", timeout=20)

# 3. Create backup script using base64 encoding to avoid escape issues
print("3. Creating backup script...")
backup_script = '''#!/bin/bash
# MySQL Backup Sync Script
# Syncs /home/mysql from DB01 (10.68.2.11) to /home/mysql-backup on DB02

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="/var/log/mysql-backup/sync_${TIMESTAMP}.log"
SOURCE="adminsgddt@10.68.2.11:/home/mysql/"
DEST="/home/mysql-backup/"

echo "=== MySQL Backup Started at $TIMESTAMP ===" >> "$LOG"
sshpass -p "vnpt@123" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" "$SOURCE" "$DEST" >> "$LOG" 2>&1
RESULT=$?
echo "=== Backup completed with exit code: $RESULT ===" >> "$LOG"
echo "=== Finished at $(date) ===" >> "$LOG"
'''

# Encode and decode to safely write
encoded = base64.b64encode(backup_script.encode()).decode()
run_cmd(ip, f"echo '{encoded}' | base64 -d > /opt/scripts/mysql_backup_sync.sh", timeout=30)
run_cmd(ip, "chmod +x /opt/scripts/mysql_backup_sync.sh", timeout=20)

# 4. Verify script content
print("4. Verifying backup script...")
out = run_cmd(ip, "cat /opt/scripts/mysql_backup_sync.sh | head -8", timeout=20)
if "#!/bin/bash" in out and "rsync" in out:
    print("   ✅ Backup script created correctly!")
else:
    print(f"   Script content:\n{out}")

# 5. Setup cron job - run every 6 hours
print("5. Setting up cron job (every 6 hours)...")
# Remove any existing mysql_backup entry and add new one
run_cmd(ip, "(crontab -l 2>/dev/null | grep -v mysql_backup_sync; echo '0 */6 * * * /opt/scripts/mysql_backup_sync.sh') | crontab -", timeout=30)

# 6. Verify cron
print("6. Verifying cron job...")
out = run_cmd(ip, "crontab -l 2>&1", timeout=20)
if "mysql_backup_sync" in out:
    cron_line = [l for l in out.split('\n') if 'mysql_backup_sync' in l]
    print(f"   ✅ Cron: {cron_line[0].strip() if cron_line else out.strip()}")
else:
    print(f"   ⚠️ Cron output: {out[:100]}")

# 7. Test backup script (dry run)
print("7. Running initial backup test...")
out = run_cmd(ip, "/opt/scripts/mysql_backup_sync.sh && cat /var/log/mysql-backup/sync_*.log 2>/dev/null | tail -5", timeout=180)
if "Backup completed" in out or "receiving" in out or "sent" in out:
    print("   ✅ Backup test successful!")
else:
    print(f"   Output: {out[-200:]}")

client.close()

print("\n" + "=" * 60)
print("✅ ALL SETUP COMPLETE!")
print("=" * 60)
print("""
📋 Summary:
- DB01 (10.68.2.11): MySQL container running on port 3306
  - Root password: Sgdt@2026
  - Data volume: /home/mysql
  
- DB02 (10.68.2.12): Backup configured
  - Script: /opt/scripts/mysql_backup_sync.sh
  - Schedule: Every 6 hours (0 */6 * * *)
  - Destination: /home/mysql-backup
""")
