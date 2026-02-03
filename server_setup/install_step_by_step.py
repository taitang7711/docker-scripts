# Run commands one by one with proper sudo
import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

def run_cmd(ip, cmd, timeout=300):
    """Run a single command with sudo on remote server"""
    password = 'vnpt@123'
    full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    try:
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        code = stdout.channel.recv_exit_status()
        return out, err, code
    except Exception as e:
        return "", str(e), -1

print("=" * 60)
print("🐳 INSTALLING DOCKER ON DB SERVERS - STEP BY STEP")
print("=" * 60)

for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    print(f"\n[{name}] ({ip})")
    print("-" * 50)
    
    # Step 1: Clean old docker files
    print("  1. Cleaning old docker files...")
    run_cmd(ip, "rm -f /etc/apt/sources.list.d/docker.list /etc/apt/keyrings/docker.gpg", timeout=30)
    
    # Step 2: Update apt
    print("  2. Updating apt...")
    out, err, code = run_cmd(ip, "apt-get update -y 2>&1 | tail -5", timeout=120)
    print(f"     {out.strip()[:100]}")
    
    # Step 3: Install prerequisites  
    print("  3. Installing prerequisites...")
    out, err, code = run_cmd(ip, "apt-get install -y ca-certificates curl gnupg 2>&1 | tail -3", timeout=120)
    
    # Step 4: Setup keyring
    print("  4. Setting up Docker GPG key...")
    run_cmd(ip, "install -m 0755 -d /etc/apt/keyrings", timeout=30)
    run_cmd(ip, "curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /tmp/docker.gpg", timeout=60)
    run_cmd(ip, "cat /tmp/docker.gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg", timeout=30)
    run_cmd(ip, "chmod a+r /etc/apt/keyrings/docker.gpg", timeout=20)
    
    # Step 5: Get system info and add repo
    print("  5. Adding Docker repository...")
    out, _, _ = run_cmd(ip, ". /etc/os-release && echo $VERSION_CODENAME", timeout=20)
    codename = out.strip().split()[-1] if out and out.strip() else "noble"
    if not codename:
        codename = "noble"
    out, _, _ = run_cmd(ip, "dpkg --print-architecture", timeout=20)
    arch = out.strip().split()[-1] if out and out.strip() else "amd64"
    if not arch:
        arch = "amd64"
    print(f"     Detected: {codename} / {arch}")
    
    repo_line = f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu {codename} stable"
    run_cmd(ip, f"echo '{repo_line}' > /etc/apt/sources.list.d/docker.list", timeout=30)
    
    # Step 6: Update again
    print("  6. Updating apt with Docker repo...")
    out, err, code = run_cmd(ip, "apt-get update -y 2>&1 | tail -3", timeout=120)
    if code != 0:
        print(f"     Warning: {err[:100]}")
    
    # Step 7: Install Docker
    print("  7. Installing Docker (this may take a while)...")
    out, err, code = run_cmd(ip, "DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>&1 | tail -5", timeout=600)
    print(f"     {out.strip()[-200:]}")
    
    # Step 8: Enable and start
    print("  8. Starting Docker service...")
    run_cmd(ip, "systemctl enable docker", timeout=30)
    run_cmd(ip, "systemctl start docker", timeout=30)
    
    # Step 9: Verify
    print("  9. Verifying installation...")
    out, err, code = run_cmd(ip, "docker --version", timeout=30)
    if "Docker version" in out:
        print(f"  ✅ {out.strip()}")
    else:
        print(f"  ⚠️ Docker not found: {err[:100]}")

# Setup MySQL on DB01
print("\n" + "=" * 60)
print("🐬 STARTING MYSQL ON DB01")
print("=" * 60)

print("  Creating volume directory...")
run_cmd("10.68.2.11", "mkdir -p /home/mysql && chmod 755 /home/mysql", timeout=30)

print("  Stopping old container...")
run_cmd("10.68.2.11", "docker stop mysql-master 2>/dev/null || true", timeout=30)
run_cmd("10.68.2.11", "docker rm mysql-master 2>/dev/null || true", timeout=30)

print("  Pulling MySQL image...")
out, err, code = run_cmd("10.68.2.11", "docker pull mysql:latest 2>&1 | tail -3", timeout=300)
print(f"  {out.strip()[:100]}")

print("  Starting MySQL container...")
mysql_run = "docker run -d --name mysql-master --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=Sgdt@2026 -v /home/mysql:/var/lib/mysql mysql:latest"
out, err, code = run_cmd("10.68.2.11", mysql_run, timeout=120)

print("  Waiting for MySQL to start...")
time.sleep(15)

print("  Verifying MySQL...")
out, err, code = run_cmd("10.68.2.11", "docker ps --format '{{.Names}} {{.Status}}' | grep mysql", timeout=30)
if "mysql-master" in out and "Up" in out:
    print(f"  ✅ MySQL running: {out.strip()}")
else:
    print(f"  ⚠️ MySQL status: {out} {err}")

# Setup Backup on DB02
print("\n" + "=" * 60)
print("📦 SETTING UP BACKUP ON DB02")
print("=" * 60)

print("  Installing rsync and sshpass...")
run_cmd("10.68.2.12", "apt-get install -y rsync sshpass 2>&1 | tail -2", timeout=120)

print("  Creating directories...")
run_cmd("10.68.2.12", "mkdir -p /home/mysql-backup /opt/scripts /var/log/mysql-backup", timeout=30)

print("  Creating backup script...")
backup_script = '''#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="/var/log/mysql-backup/sync_$TIMESTAMP.log"
echo "[$TIMESTAMP] Starting backup..." >> $LOG
sshpass -p "vnpt@123" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" adminsgddt@10.68.2.11:/home/mysql/ /home/mysql-backup/ >> $LOG 2>&1
echo "[$TIMESTAMP] Done" >> $LOG'''

# Write script line by line
for line in backup_script.split('\n'):
    escaped = line.replace('"', '\\"').replace('$', '\\$')
    run_cmd("10.68.2.12", f"echo '{escaped}' >> /opt/scripts/mysql_backup_sync.sh.tmp", timeout=20)

run_cmd("10.68.2.12", "mv /opt/scripts/mysql_backup_sync.sh.tmp /opt/scripts/mysql_backup_sync.sh", timeout=20)
run_cmd("10.68.2.12", "chmod +x /opt/scripts/mysql_backup_sync.sh", timeout=20)

print("  Setting up cron job (every 6 hours)...")
cron_cmd = "(crontab -l 2>/dev/null | grep -v mysql_backup_sync; echo '0 */6 * * * /opt/scripts/mysql_backup_sync.sh') | crontab -"
run_cmd("10.68.2.12", cron_cmd, timeout=30)

print("  Verifying backup setup...")
out, _, _ = run_cmd("10.68.2.12", "ls -la /opt/scripts/mysql_backup_sync.sh", timeout=20)
print(f"  Script: {out.strip()}")

out, _, _ = run_cmd("10.68.2.12", "crontab -l | grep mysql", timeout=20)
if "mysql_backup" in out:
    print(f"  ✅ Cron: {out.strip()}")
else:
    print(f"  ⚠️ Cron not set")

client.close()

print("\n" + "=" * 60)
print("✅ INSTALLATION COMPLETED!")
print("=" * 60)
