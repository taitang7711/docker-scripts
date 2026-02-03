# Fix ALL remaining issues
import paramiko
from concurrent.futures import ThreadPoolExecutor
import time

HOSTS_ENTRY = "113.163.158.54 gitlab.vnptkiengiang.vn"
PASSWORD = "vnpt@123"

def get_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('127.0.0.1', port=2222, username='adminsgddt', password=PASSWORD, timeout=60)
    return client

def run_sudo_script(client, ip, script, timeout=600):
    """Run a multi-line script with sudo"""
    # Create temp script and run
    escaped = script.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$')
    cmd = f'''sshpass -p '{PASSWORD}' ssh -tt -o StrictHostKeyChecking=no adminsgddt@{ip} << 'REMOTESCRIPT'
echo '{PASSWORD}' | sudo -S bash << 'SUDOSCRIPT'
{script}
SUDOSCRIPT
REMOTESCRIPT'''
    
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode() + stderr.read().decode()

def setup_server(name, ip, role):
    """Setup a single server"""
    results = []
    print(f"\n[{name}] 🚀 Starting setup...")
    client = get_client()
    
    # 1. Configure /etc/hosts
    print(f"[{name}] 📝 Configuring /etc/hosts...")
    hosts_script = f'''
grep -q "gitlab.vnptkiengiang.vn" /etc/hosts || echo "{HOSTS_ENTRY}" >> /etc/hosts
grep gitlab /etc/hosts
'''
    out = run_sudo_script(client, ip, hosts_script, timeout=30)
    if "gitlab.vnptkiengiang.vn" in out:
        print(f"[{name}] ✅ /etc/hosts configured")
        results.append("hosts")
    else:
        print(f"[{name}] ⚠️ /etc/hosts: {out[:100]}")
    
    # 2. If DB server - Docker + MySQL/Backup
    if role in ["db_master", "db_backup"]:
        # Install Docker
        print(f"[{name}] 🐳 Setting up Docker...")
        docker_script = '''
export DEBIAN_FRONTEND=noninteractive
if ! command -v docker &> /dev/null; then
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null || true
    chmod a+r /etc/apt/keyrings/docker.gpg 2>/dev/null || true
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    systemctl start docker
fi
docker --version
'''
        out = run_sudo_script(client, ip, docker_script, timeout=600)
        if "Docker version" in out:
            for line in out.split('\n'):
                if "Docker version" in line:
                    print(f"[{name}] ✅ {line.strip()}")
                    results.append("docker")
                    break
        else:
            print(f"[{name}] ⚠️ Docker output: {out[-200:]}")
        
        # DB01: MySQL
        if role == "db_master":
            print(f"[{name}] 🐬 Setting up MySQL...")
            mysql_script = '''
mkdir -p /home/mysql
chmod 755 /home/mysql
docker stop mysql-master 2>/dev/null || true
docker rm mysql-master 2>/dev/null || true
docker run -d --name mysql-master --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=Sgdt@2026 -v /home/mysql:/var/lib/mysql mysql:latest
sleep 10
docker ps | grep mysql-master
'''
            out = run_sudo_script(client, ip, mysql_script, timeout=180)
            if "mysql-master" in out:
                print(f"[{name}] ✅ MySQL container running")
                results.append("mysql")
            else:
                print(f"[{name}] ⚠️ MySQL: {out[-150:]}")
        
        # DB02: Backup
        if role == "db_backup":
            print(f"[{name}] 📦 Setting up Backup...")
            backup_script = '''
apt-get install -y rsync sshpass
mkdir -p /home/mysql-backup /opt/scripts /var/log/mysql-backup
cat > /opt/scripts/mysql_backup_sync.sh << 'BKEOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="/var/log/mysql-backup/sync_$TIMESTAMP.log"
echo "[$TIMESTAMP] Starting backup..." >> $LOG
sshpass -p "vnpt@123" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" adminsgddt@10.68.2.11:/home/mysql/ /home/mysql-backup/ >> $LOG 2>&1
echo "[$TIMESTAMP] Done" >> $LOG
BKEOF
chmod +x /opt/scripts/mysql_backup_sync.sh
(crontab -l 2>/dev/null | grep -v mysql_backup_sync; echo "0 */6 * * * /opt/scripts/mysql_backup_sync.sh") | crontab -
crontab -l | grep mysql
ls -la /opt/scripts/mysql_backup_sync.sh
'''
            out = run_sudo_script(client, ip, backup_script, timeout=120)
            if "mysql_backup_sync" in out:
                print(f"[{name}] ✅ Backup cron configured")
                results.append("backup")
            else:
                print(f"[{name}] ⚠️ Backup: {out[-150:]}")
    
    client.close()
    return name, results

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 COMPLETE FIX - PARALLEL EXECUTION")  
    print("=" * 60)
    
    servers = [
        ("APP01", "10.67.2.11", "app"),
        ("APP02", "10.67.2.12", "app"),
        ("DB01", "10.68.2.11", "db_master"),
        ("DB02", "10.68.2.12", "db_backup"),
    ]
    
    start = time.time()
    all_results = {}
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(setup_server, name, ip, role): name for name, ip, role in servers}
        for future in futures:
            name, results = future.result()
            all_results[name] = results
    
    elapsed = time.time() - start
    
    print("\n" + "=" * 60)
    print("📋 FINAL RESULTS")
    print("=" * 60)
    for name, results in all_results.items():
        status = "✅" if results else "⚠️"
        print(f"   {status} {name}: {', '.join(results) if results else 'partial'}")
    
    print(f"\n⏱️  Total time: {elapsed:.1f}s")
