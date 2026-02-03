# Fix sources.list and install Docker properly
import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

def run_on_jumphost(cmd, timeout=600):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode() + stderr.read().decode()

print("=" * 60)
print("🔧 FIXING APT SOURCES & INSTALLING DOCKER")
print("=" * 60)

for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    print(f"\n[{name}] Fixing and installing Docker...")
    
    # Fix apt sources first
    fix_cmd = f'''sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} "
        echo 'vnpt@123' | sudo -S bash -c '
            # Remove broken docker list
            rm -f /etc/apt/sources.list.d/docker.list
            rm -f /etc/apt/keyrings/docker.gpg
            
            # Update apt
            apt-get update -y
            
            # Install prerequisites
            apt-get install -y ca-certificates curl gnupg
            
            # Setup Docker repo properly
            install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /tmp/docker.asc
            gpg --dearmor < /tmp/docker.asc > /etc/apt/keyrings/docker.gpg
            chmod a+r /etc/apt/keyrings/docker.gpg
            
            # Get codename
            CODENAME=$(. /etc/os-release && echo \\$VERSION_CODENAME)
            ARCH=$(dpkg --print-architecture)
            
            # Add repo
            echo "deb [arch=\\$ARCH signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \\$CODENAME stable" > /etc/apt/sources.list.d/docker.list
            
            # Install Docker
            apt-get update -y
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            
            # Enable and start
            systemctl enable docker
            systemctl start docker
            
            # Verify
            docker --version
        '
    "'''
    
    out = run_on_jumphost(fix_cmd, timeout=900)
    
    if "Docker version" in out:
        for line in out.split('\n'):
            if "Docker version" in line:
                print(f"[{name}] ✅ {line.strip()}")
                break
    else:
        print(f"[{name}] Last output: {out[-400:]}")

# Now setup MySQL on DB01
print("\n" + "=" * 60)
print("🐬 STARTING MYSQL CONTAINER ON DB01")
print("=" * 60)

mysql_cmd = '''sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@10.68.2.11 "
    echo 'vnpt@123' | sudo -S bash -c '
        mkdir -p /home/mysql
        chmod 755 /home/mysql
        docker stop mysql-master 2>/dev/null || true
        docker rm mysql-master 2>/dev/null || true
        docker pull mysql:latest
        docker run -d --name mysql-master --restart always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=Sgdt@2026 -v /home/mysql:/var/lib/mysql mysql:latest
        sleep 15
        docker ps --format \"table {{.Names}}\\t{{.Status}}\\t{{.Ports}}\"
    '
"'''

out = run_on_jumphost(mysql_cmd, timeout=300)
print(out[-500:])

# Setup cron for backup on DB02
print("\n" + "=" * 60)
print("📦 SETTING UP BACKUP CRON ON DB02")
print("=" * 60)

cron_cmd = '''sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@10.68.2.12 "
    echo 'vnpt@123' | sudo -S bash -c '
        (crontab -l 2>/dev/null | grep -v mysql_backup_sync; echo \"0 */6 * * * /opt/scripts/mysql_backup_sync.sh\") | crontab -
        echo \"Crontab configured:\"
        crontab -l | grep mysql
    '
"'''

out = run_on_jumphost(cron_cmd, timeout=60)
print(out)

client.close()
print("\n✅ Done!")
