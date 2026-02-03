# Fix remaining issues - run with proper sudo
import paramiko
from concurrent.futures import ThreadPoolExecutor
import time

def get_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=30)
    return client

def run_sudo(client, ip, cmd, timeout=300):
    password = 'vnpt@123'
    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    out = stdout.read().decode()
    return out

HOSTS_ENTRY = "113.163.158.54 gitlab.vnptkiengiang.vn"

SERVERS = [
    ("APP01", "10.67.2.11"),
    ("APP02", "10.67.2.12"),
    ("DB01", "10.68.2.11"),
    ("DB02", "10.68.2.12"),
]

def fix_server(name, ip):
    print(f"[{name}] Starting fix...")
    client = get_client()
    
    # 1. Fix /etc/hosts
    hosts_cmd = f"grep -q gitlab.vnptkiengiang.vn /etc/hosts || echo '{HOSTS_ENTRY}' >> /etc/hosts; grep gitlab /etc/hosts"
    out = run_sudo(client, ip, hosts_cmd, timeout=30)
    print(f"[{name}] /etc/hosts: {out.strip()}")
    
    # 2. If DB server, fix Docker
    if "DB" in name:
        # Check docker
        docker_check = run_sudo(client, ip, "docker --version 2>/dev/null || echo NOT_FOUND", timeout=30)
        
        if "NOT_FOUND" in docker_check:
            print(f"[{name}] Installing Docker...")
            docker_install = '''
            apt-get update -y
            apt-get install -y ca-certificates curl gnupg
            install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null || true
            chmod a+r /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
            apt-get update -y
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            systemctl enable docker
            systemctl start docker
            docker --version
            '''
            out = run_sudo(client, ip, docker_install.replace("'", "'\"'\"'"), timeout=600)
            print(f"[{name}] Docker installed: {out[-100:]}")
        else:
            print(f"[{name}] Docker: {docker_check.strip()}")
        
        # DB01: MySQL container
        if name == "DB01":
            mysql_check = run_sudo(client, ip, "docker ps | grep mysql-master || echo NOT_RUNNING", timeout=30)
            
            if "NOT_RUNNING" in mysql_check:
                print(f"[{name}] Starting MySQL container...")
                mysql_cmd = '''
                mkdir -p /home/mysql
                docker stop mysql-master 2>/dev/null || true
                docker rm mysql-master 2>/dev/null || true
                docker run -d --name mysql-master --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=Sgdt@2026 -v /home/mysql:/var/lib/mysql mysql:latest
                sleep 10
                docker ps | grep mysql
                '''
                out = run_sudo(client, ip, mysql_cmd.replace("'", "'\"'\"'"), timeout=180)
                print(f"[{name}] MySQL: {out[-150:]}")
            else:
                print(f"[{name}] MySQL running: {mysql_check.strip()}")
        
        # DB02: Backup cron
        if name == "DB02":
            cron_check = run_sudo(client, ip, "crontab -l 2>/dev/null | grep mysql_backup || echo NOT_FOUND", timeout=30)
            
            if "NOT_FOUND" in cron_check:
                print(f"[{name}] Setting up backup cron...")
                backup_cmd = '''
                apt-get install -y rsync sshpass
                mkdir -p /home/mysql-backup /opt/scripts /var/log/mysql-backup
                cat > /opt/scripts/mysql_backup_sync.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="/var/log/mysql-backup/sync_$TIMESTAMP.log"
sshpass -p "vnpt@123" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" adminsgddt@10.68.2.11:/home/mysql/ /home/mysql-backup/ >> $LOG 2>&1
echo "[$TIMESTAMP] Done" >> $LOG
EOF
                chmod +x /opt/scripts/mysql_backup_sync.sh
                (crontab -l 2>/dev/null | grep -v mysql_backup; echo "0 */6 * * * /opt/scripts/mysql_backup_sync.sh") | crontab -
                crontab -l | grep mysql
                '''
                out = run_sudo(client, ip, backup_cmd, timeout=120)
                print(f"[{name}] Backup cron: {out[-100:]}")
            else:
                print(f"[{name}] Backup cron: {cron_check.strip()}")
    
    client.close()
    return f"{name} done"

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 FIXING REMAINING ISSUES - PARALLEL")
    print("=" * 60)
    
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fix_server, name, ip) for name, ip in SERVERS]
        for f in futures:
            f.result()
    
    print(f"\n⏱️  Done in {time.time()-start:.1f}s")
