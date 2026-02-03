# Complete Docker setup from scratch
import paramiko
import time

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
print("🐳 COMPLETE DOCKER INSTALLATION FROM SCRATCH")
print("=" * 60)

for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    print(f"\n{'='*50}")
    print(f"[{name}] ({ip})")
    print(f"{'='*50}")
    
    # 1. Kill any running apt processes
    print("1. Killing apt processes...")
    run_cmd(ip, "pkill -9 apt; pkill -9 dpkg; pkill -9 apt-get; sleep 2", timeout=30)
    run_cmd(ip, "rm -f /var/lib/dpkg/lock* /var/lib/apt/lists/lock /var/cache/apt/archives/lock", timeout=20)
    run_cmd(ip, "dpkg --configure -a", timeout=60)
    
    # 2. Remove old Docker completely
    print("2. Removing old Docker...")
    run_cmd(ip, "apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true", timeout=60)
    run_cmd(ip, "rm -rf /etc/apt/sources.list.d/docker.list /etc/apt/keyrings/docker.gpg", timeout=20)
    
    # 3. Update apt
    print("3. Updating apt...")
    out = run_cmd(ip, "apt-get update -y 2>&1 | tail -3", timeout=120)
    print(f"   {out.strip()[:100]}")
    
    # 4. Install prerequisites
    print("4. Installing prerequisites...")
    run_cmd(ip, "apt-get install -y ca-certificates curl gnupg lsb-release", timeout=120)
    
    # 5. Setup Docker GPG key
    print("5. Setting up Docker GPG key...")
    run_cmd(ip, "install -m 0755 -d /etc/apt/keyrings", timeout=20)
    run_cmd(ip, "curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /tmp/docker-gpg.key", timeout=60)
    run_cmd(ip, "gpg --dearmor -o /etc/apt/keyrings/docker.gpg < /tmp/docker-gpg.key", timeout=30)
    run_cmd(ip, "chmod a+r /etc/apt/keyrings/docker.gpg", timeout=20)
    
    # 6. Add Docker repository
    print("6. Adding Docker repository...")
    repo_cmd = '''
ARCH=$(dpkg --print-architecture)
CODENAME=$(. /etc/os-release && echo $VERSION_CODENAME)
echo "deb [arch=$ARCH signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $CODENAME stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
cat /etc/apt/sources.list.d/docker.list
'''
    out = run_cmd(ip, repo_cmd.replace('\n', ' '), timeout=30)
    print(f"   Repo: {out.strip()[-100:]}")
    
    # 7. Update apt with new repo
    print("7. Updating apt...")
    out = run_cmd(ip, "apt-get update -y 2>&1 | tail -5", timeout=120)
    if "Err" in out or "error" in out.lower():
        print(f"   ⚠️ {out[-200:]}")
    else:
        print(f"   OK")
    
    # 8. Install Docker
    print("8. Installing Docker CE...")
    out = run_cmd(ip, "DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>&1", timeout=900)
    
    # Check result
    if "Setting up docker-ce" in out or "is already the newest" in out:
        print("   Docker packages installed!")
    else:
        print(f"   Output: {out[-300:]}")
    
    # 9. Enable and start
    print("9. Starting Docker service...")
    run_cmd(ip, "systemctl enable docker", timeout=30)
    run_cmd(ip, "systemctl start docker", timeout=30)
    time.sleep(3)
    
    # 10. Verify
    print("10. Verifying Docker...")
    out = run_cmd(ip, "docker --version && docker ps", timeout=30)
    if "Docker version" in out:
        version_line = [l for l in out.split('\n') if 'Docker version' in l]
        print(f"   ✅ {version_line[0] if version_line else out[:50]}")
    else:
        print(f"   ⚠️ Docker not working: {out[-150:]}")

# Now setup MySQL on DB01
print("\n" + "=" * 60)
print("🐬 SETTING UP MYSQL ON DB01")
print("=" * 60)

run_cmd("10.68.2.11", "mkdir -p /home/mysql && chmod 755 /home/mysql", timeout=20)
run_cmd("10.68.2.11", "docker stop mysql-master 2>/dev/null; docker rm mysql-master 2>/dev/null; true", timeout=30)

print("Pulling MySQL image...")
out = run_cmd("10.68.2.11", "docker pull mysql:latest 2>&1 | tail -5", timeout=300)
print(f"   {out[-150:]}")

print("Starting MySQL container...")
mysql_cmd = "docker run -d --name mysql-master --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=Sgdt@2026 -v /home/mysql:/var/lib/mysql mysql:latest"
out = run_cmd("10.68.2.11", mysql_cmd, timeout=120)
print(f"   Container ID: {out[:20]}...")

print("Waiting for MySQL to initialize...")
time.sleep(20)

out = run_cmd("10.68.2.11", "docker ps --format 'table {{.Names}}\\t{{.Status}}' | grep mysql", timeout=30)
if "Up" in out:
    print(f"✅ MySQL running: {out.strip()}")
else:
    out2 = run_cmd("10.68.2.11", "docker logs mysql-master 2>&1 | tail -10", timeout=30)
    print(f"⚠️ MySQL logs: {out2[-200:]}")

# Setup backup cron on DB02
print("\n" + "=" * 60)
print("📦 SETTING UP BACKUP ON DB02")
print("=" * 60)

run_cmd("10.68.2.12", "apt-get install -y rsync sshpass", timeout=120)
run_cmd("10.68.2.12", "mkdir -p /home/mysql-backup /opt/scripts /var/log/mysql-backup", timeout=20)

# Create backup script properly
print("Creating backup script...")
script = '''#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="/var/log/mysql-backup/sync_$TIMESTAMP.log"
echo "[$TIMESTAMP] Starting backup..." >> $LOG
sshpass -p "vnpt@123" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" adminsgddt@10.68.2.11:/home/mysql/ /home/mysql-backup/ >> $LOG 2>&1
echo "[$TIMESTAMP] Done" >> $LOG
'''

# Use base64 to avoid escaping issues
import base64
encoded = base64.b64encode(script.encode()).decode()
run_cmd("10.68.2.12", f"echo {encoded} | base64 -d > /opt/scripts/mysql_backup_sync.sh", timeout=30)
run_cmd("10.68.2.12", "chmod +x /opt/scripts/mysql_backup_sync.sh", timeout=20)

# Setup cron
print("Setting up cron job...")
run_cmd("10.68.2.12", "(crontab -l 2>/dev/null | grep -v mysql_backup; echo '0 */6 * * * /opt/scripts/mysql_backup_sync.sh') | crontab -", timeout=30)

# Verify
out = run_cmd("10.68.2.12", "cat /opt/scripts/mysql_backup_sync.sh | head -3", timeout=20)
print(f"Script: {out.strip()[:80]}")

out = run_cmd("10.68.2.12", "crontab -l | grep mysql", timeout=20)
print(f"Cron: {out.strip()}")

client.close()

print("\n" + "=" * 60)
print("✅ INSTALLATION COMPLETE!")
print("=" * 60)
