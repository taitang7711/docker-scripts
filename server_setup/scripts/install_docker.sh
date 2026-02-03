#!/bin/bash
# install_docker.sh - Run on Jump Host

set -e

PASSWORD="vnpt@123"

install_docker_on_server() {
    local IP=$1
    local NAME=$2
    
    echo "========================================"
    echo "Installing Docker on $NAME ($IP)"
    echo "========================================"
    
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no adminsgddt@$IP << 'REMOTESCRIPT'
echo 'vnpt@123' | sudo -S bash << 'SUDOSCRIPT'
set -e

# Clean up old docker files
rm -f /etc/apt/sources.list.d/docker.list
rm -f /etc/apt/keyrings/docker.gpg

# Update system
apt-get update -y

# Install prerequisites
apt-get install -y ca-certificates curl gnupg

# Setup Docker repository
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

# Get system info
CODENAME=$(. /etc/os-release && echo $VERSION_CODENAME)
ARCH=$(dpkg --print-architecture)

# Add Docker repository
echo "deb [arch=$ARCH signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $CODENAME stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Verify
docker --version
echo "DOCKER_INSTALLED_SUCCESSFULLY"
SUDOSCRIPT
REMOTESCRIPT
}

# Install on DB01
install_docker_on_server "10.68.2.11" "DB01"

# Install on DB02  
install_docker_on_server "10.68.2.12" "DB02"

echo "========================================"
echo "Starting MySQL on DB01"
echo "========================================"

sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no adminsgddt@10.68.2.11 << 'REMOTESCRIPT'
echo 'vnpt@123' | sudo -S bash << 'SUDOSCRIPT'
mkdir -p /home/mysql
chmod 755 /home/mysql
docker stop mysql-master 2>/dev/null || true
docker rm mysql-master 2>/dev/null || true
docker run -d \
  --name mysql-master \
  --restart always \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=Sgdt@2026 \
  -v /home/mysql:/var/lib/mysql \
  mysql:latest
sleep 15
docker ps | grep mysql
echo "MYSQL_STARTED_SUCCESSFULLY"
SUDOSCRIPT
REMOTESCRIPT

echo "========================================"
echo "Setting up Backup on DB02"
echo "========================================"

sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no adminsgddt@10.68.2.12 << 'REMOTESCRIPT'
echo 'vnpt@123' | sudo -S bash << 'SUDOSCRIPT'
apt-get install -y rsync sshpass
mkdir -p /home/mysql-backup /opt/scripts /var/log/mysql-backup

cat > /opt/scripts/mysql_backup_sync.sh << 'BACKUPSCRIPT'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="/var/log/mysql-backup/sync_$TIMESTAMP.log"
echo "[$TIMESTAMP] Starting backup..." >> $LOG
sshpass -p "vnpt@123" rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" adminsgddt@10.68.2.11:/home/mysql/ /home/mysql-backup/ >> $LOG 2>&1
echo "[$TIMESTAMP] Done" >> $LOG
BACKUPSCRIPT

chmod +x /opt/scripts/mysql_backup_sync.sh

# Setup cron
(crontab -l 2>/dev/null | grep -v mysql_backup_sync; echo "0 */6 * * * /opt/scripts/mysql_backup_sync.sh") | crontab -

echo "Crontab:"
crontab -l
echo "BACKUP_CONFIGURED_SUCCESSFULLY"
SUDOSCRIPT
REMOTESCRIPT

echo "========================================"
echo "DONE!"
echo "========================================"
