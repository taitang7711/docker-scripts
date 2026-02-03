# Simple direct commands - no heredoc
import paramiko
from concurrent.futures import ThreadPoolExecutor
import time

PASSWORD = "vnpt@123"
HOSTS_ENTRY = "113.163.158.54 gitlab.vnptkiengiang.vn"

def get_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('127.0.0.1', port=2222, username='adminsgddt', password=PASSWORD, timeout=60)
    return client

def ssh_sudo(client, ip, cmd, timeout=120):
    """Simple sudo command via sshpass"""
    full_cmd = f"sshpass -p '{PASSWORD}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{PASSWORD}' | sudo -S {cmd}\""
    try:
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
        return stdout.read().decode().strip()
    except:
        return ""

def setup_hosts(client, name, ip):
    """Configure /etc/hosts"""
    # Check first
    check = ssh_sudo(client, ip, f"grep -c gitlab.vnptkiengiang.vn /etc/hosts || echo 0", timeout=20)
    if check and int(check.split()[-1]) > 0:
        print(f"[{name}] ✅ /etc/hosts already configured")
        return True
    
    # Add entry
    ssh_sudo(client, ip, f"bash -c 'echo \"{HOSTS_ENTRY}\" >> /etc/hosts'", timeout=20)
    
    # Verify
    verify = ssh_sudo(client, ip, "grep gitlab.vnptkiengiang.vn /etc/hosts", timeout=20)
    if HOSTS_ENTRY in verify:
        print(f"[{name}] ✅ /etc/hosts configured: {verify}")
        return True
    else:
        print(f"[{name}] ⚠️ /etc/hosts issue")
        return False

def setup_docker(client, name, ip):
    """Install Docker"""
    # Check if exists
    check = ssh_sudo(client, ip, "docker --version 2>/dev/null || echo NOT_FOUND", timeout=30)
    if "Docker version" in check:
        print(f"[{name}] ✅ Docker already installed: {check}")
        return True
    
    print(f"[{name}] 🐳 Installing Docker...")
    
    # Step by step installation
    ssh_sudo(client, ip, "apt-get update -y", timeout=120)
    ssh_sudo(client, ip, "apt-get install -y ca-certificates curl gnupg", timeout=120)
    ssh_sudo(client, ip, "install -m 0755 -d /etc/apt/keyrings", timeout=30)
    ssh_sudo(client, ip, "curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /tmp/docker.gpg", timeout=60)
    ssh_sudo(client, ip, "gpg --dearmor -o /etc/apt/keyrings/docker.gpg < /tmp/docker.gpg", timeout=30)
    ssh_sudo(client, ip, "chmod a+r /etc/apt/keyrings/docker.gpg", timeout=20)
    
    # Add repo
    codename = ssh_sudo(client, ip, ". /etc/os-release && echo $VERSION_CODENAME", timeout=20)
    arch = ssh_sudo(client, ip, "dpkg --print-architecture", timeout=20)
    repo = f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu {codename} stable"
    ssh_sudo(client, ip, f"bash -c 'echo \"{repo}\" > /etc/apt/sources.list.d/docker.list'", timeout=30)
    
    # Install
    ssh_sudo(client, ip, "apt-get update -y", timeout=120)
    ssh_sudo(client, ip, "apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin", timeout=300)
    ssh_sudo(client, ip, "systemctl enable docker && systemctl start docker", timeout=60)
    
    # Verify
    verify = ssh_sudo(client, ip, "docker --version", timeout=30)
    if "Docker version" in verify:
        print(f"[{name}] ✅ {verify}")
        return True
    else:
        print(f"[{name}] ⚠️ Docker install issue")
        return False

def setup_mysql(client, name, ip):
    """Setup MySQL container on DB01"""
    print(f"[{name}] 🐬 Setting up MySQL...")
    
    ssh_sudo(client, ip, "mkdir -p /home/mysql && chmod 755 /home/mysql", timeout=30)
    ssh_sudo(client, ip, "docker stop mysql-master 2>/dev/null || true", timeout=30)
    ssh_sudo(client, ip, "docker rm mysql-master 2>/dev/null || true", timeout=30)
    
    # Run container
    run_cmd = "docker run -d --name mysql-master --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=Sgdt@2026 -v /home/mysql:/var/lib/mysql mysql:latest"
    ssh_sudo(client, ip, run_cmd, timeout=120)
    
    time.sleep(10)
    
    # Verify
    verify = ssh_sudo(client, ip, "docker ps --format '{{.Names}} {{.Status}}' | grep mysql-master", timeout=30)
    if "mysql-master" in verify and "Up" in verify:
        print(f"[{name}] ✅ MySQL running: {verify}")
        return True
    else:
        print(f"[{name}] ⚠️ MySQL: {verify}")
        return False

def setup_backup(client, name, ip):
    """Setup backup on DB02"""
    print(f"[{name}] 📦 Setting up backup...")
    
    ssh_sudo(client, ip, "apt-get install -y rsync sshpass", timeout=120)
    ssh_sudo(client, ip, "mkdir -p /home/mysql-backup /opt/scripts /var/log/mysql-backup", timeout=30)
    
    # Create backup script
    script_content = '''#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="/var/log/mysql-backup/sync_$TIMESTAMP.log"
echo "[$TIMESTAMP] Starting backup..." >> $LOG
sshpass -p "vnpt@123" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" adminsgddt@10.68.2.11:/home/mysql/ /home/mysql-backup/ >> $LOG 2>&1
echo "[$TIMESTAMP] Done" >> $LOG
'''
    # Write script using echo
    for line in script_content.strip().split('\n'):
        escaped_line = line.replace('"', '\\"').replace('$', '\\$')
        ssh_sudo(client, ip, f"bash -c 'echo \"{escaped_line}\" >> /opt/scripts/mysql_backup_sync.sh.tmp'", timeout=30)
    
    ssh_sudo(client, ip, "mv /opt/scripts/mysql_backup_sync.sh.tmp /opt/scripts/mysql_backup_sync.sh", timeout=20)
    ssh_sudo(client, ip, "chmod +x /opt/scripts/mysql_backup_sync.sh", timeout=20)
    
    # Setup cron
    ssh_sudo(client, ip, "bash -c '(crontab -l 2>/dev/null | grep -v mysql_backup; echo \"0 */6 * * * /opt/scripts/mysql_backup_sync.sh\") | crontab -'", timeout=30)
    
    # Verify
    cron = ssh_sudo(client, ip, "crontab -l | grep mysql_backup", timeout=30)
    script_exists = ssh_sudo(client, ip, "ls -la /opt/scripts/mysql_backup_sync.sh", timeout=20)
    
    if "mysql_backup" in cron and "mysql_backup_sync.sh" in script_exists:
        print(f"[{name}] ✅ Backup configured")
        print(f"[{name}]    Cron: {cron}")
        return True
    else:
        print(f"[{name}] ⚠️ Backup issue")
        return False

def process_server(name, ip, role):
    """Process a single server"""
    print(f"\n{'='*50}")
    print(f"[{name}] ({ip}) - {role}")
    print(f"{'='*50}")
    
    client = get_client()
    results = []
    
    # All servers: /etc/hosts
    if setup_hosts(client, name, ip):
        results.append("hosts")
    
    # DB servers: Docker
    if role in ["db_master", "db_backup"]:
        if setup_docker(client, name, ip):
            results.append("docker")
        
        # DB01: MySQL
        if role == "db_master":
            if setup_mysql(client, name, ip):
                results.append("mysql")
        
        # DB02: Backup
        if role == "db_backup":
            if setup_backup(client, name, ip):
                results.append("backup")
    
    client.close()
    return name, results

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 SIMPLE FIX - SEQUENTIAL (more reliable)")
    print("=" * 60)
    
    servers = [
        ("APP01", "10.67.2.11", "app"),
        ("APP02", "10.67.2.12", "app"),
        ("DB01", "10.68.2.11", "db_master"),
        ("DB02", "10.68.2.12", "db_backup"),
    ]
    
    start = time.time()
    all_results = {}
    
    for name, ip, role in servers:
        name, results = process_server(name, ip, role)
        all_results[name] = results
    
    elapsed = time.time() - start
    
    print("\n" + "=" * 60)
    print("📋 FINAL SUMMARY")
    print("=" * 60)
    for name, results in all_results.items():
        status = "✅" if results else "⚠️"
        print(f"   {status} {name}: {', '.join(results)}")
    
    print(f"\n⏱️  Total time: {elapsed:.1f}s")
    
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MySQL Connection:
  Host: 10.68.2.11:3306
  User: root  
  Pass: Sgdt@2026

Backup Schedule (DB02):
  Every 6 hours
  Script: /opt/scripts/mysql_backup_sync.sh
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
