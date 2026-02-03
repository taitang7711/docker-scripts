# Install Docker using convenience script
import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

def run_on_jumphost(cmd, timeout=600):
    """Run command on jump host"""
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode() + stderr.read().decode()

print("=" * 60)
print("🐳 INSTALLING DOCKER ON DB01 & DB02")
print("=" * 60)

# Use Docker convenience script - simpler and more reliable
for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    print(f"\n[{name}] Installing Docker using convenience script...")
    
    # SSH to server and run Docker install script
    install_cmd = f'''sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} "
        echo 'vnpt@123' | sudo -S bash -c '
            curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
            sh /tmp/get-docker.sh
            systemctl enable docker
            systemctl start docker
            usermod -aG docker adminsgddt
            docker --version
        '
    "'''
    
    out = run_on_jumphost(install_cmd, timeout=600)
    
    if "Docker version" in out:
        for line in out.split('\n'):
            if "Docker version" in line:
                print(f"[{name}] ✅ {line.strip()}")
    else:
        print(f"[{name}] Output: {out[-300:]}")

print("\n" + "=" * 60)
print("🐬 STARTING MYSQL ON DB01")
print("=" * 60)

mysql_cmd = '''sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@10.68.2.11 "
    echo 'vnpt@123' | sudo -S bash -c '
        mkdir -p /home/mysql
        docker stop mysql-master 2>/dev/null || true
        docker rm mysql-master 2>/dev/null || true
        docker run -d --name mysql-master --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=Sgdt@2026 -v /home/mysql:/var/lib/mysql mysql:latest
        sleep 15
        docker ps | grep mysql
    '
"'''

out = run_on_jumphost(mysql_cmd, timeout=300)
if "mysql-master" in out:
    print(f"[DB01] ✅ MySQL container running!")
    for line in out.split('\n'):
        if "mysql" in line.lower():
            print(f"   {line.strip()}")
else:
    print(f"[DB01] Output: {out[-200:]}")

print("\n" + "=" * 60)
print("📦 SETTING UP BACKUP ON DB02")
print("=" * 60)

backup_cmd = '''sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@10.68.2.12 "
    echo 'vnpt@123' | sudo -S bash -c '
        apt-get install -y rsync sshpass
        mkdir -p /home/mysql-backup /opt/scripts /var/log/mysql-backup
        
        # Create backup script
        cat > /opt/scripts/mysql_backup_sync.sh << \"BKSCRIPT\"
#!/bin/bash
TIMESTAMP=\\$(date +%Y%m%d_%H%M%S)
LOG=\"/var/log/mysql-backup/sync_\\$TIMESTAMP.log\"
echo \"[\\$TIMESTAMP] Starting backup...\" >> \\$LOG
sshpass -p \"vnpt@123\" rsync -avz --delete -e \"ssh -o StrictHostKeyChecking=no\" adminsgddt@10.68.2.11:/home/mysql/ /home/mysql-backup/ >> \\$LOG 2>&1
echo \"[\\$TIMESTAMP] Done\" >> \\$LOG
BKSCRIPT
        
        chmod +x /opt/scripts/mysql_backup_sync.sh
        (crontab -l 2>/dev/null | grep -v mysql_backup_sync; echo \"0 */6 * * * /opt/scripts/mysql_backup_sync.sh\") | crontab -
        crontab -l | grep mysql
        ls -la /opt/scripts/mysql_backup_sync.sh
    '
"'''

out = run_on_jumphost(backup_cmd, timeout=180)
if "mysql_backup_sync" in out:
    print(f"[DB02] ✅ Backup configured!")
    for line in out.split('\n'):
        if "mysql" in line.lower() or "/opt/scripts" in line:
            print(f"   {line.strip()}")
else:
    print(f"[DB02] Output: {out[-300:]}")

client.close()
print("\n✅ Done!")
