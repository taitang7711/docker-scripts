# ============================================================
# FINAL SETUP SUMMARY
# ============================================================
# Date: 02/02/2026
# Jump Host: 127.0.0.1:2222
# ============================================================

## ✅ COMPLETED SUCCESSFULLY

### DB01 (10.68.2.11) - Database Master
- [x] /etc/hosts: 113.163.158.54 gitlab.vnptkiengiang.vn
- [x] Docker: v29.2.0 (active)
- [x] MySQL Container: mysql-master
  - Image: mysql:latest (v9.6.0)
  - Port: 3306
  - Root Password: Sgdt@2026
  - Volume: /home/mysql -> /var/lib/mysql

### DB02 (10.68.2.12) - Database Backup
- [x] /etc/hosts: 113.163.158.54 gitlab.vnptkiengiang.vn
- [x] Docker: v29.2.0 (active)
- [x] Backup Script: /opt/scripts/mysql_backup_sync.sh
- [x] Cron Job: 0 */6 * * * (every 6 hours)
- [x] Backup Directory: /home/mysql-backup
- [x] Initial sync completed

## ❌ NOT ACCESSIBLE (Network Issues)

### PROXY (192.168.71.2)
- Status: SSH timeout from Jump Host
- Ping: OK but SSH connection refused/timeout
- Action: Check firewall rules, verify SSH service

### APP01 (10.68.2.5) & APP02 (10.68.2.6)
- Status: Network unreachable from Jump Host
- Ping: FAILED
- SSH: Connection timeout
- Action: Check network routing between Jump Host and 10.68.2.x subnet

## 📝 MANUAL INSTALLATION COMMANDS

For APP servers (when network is fixed or via direct access):

```bash
# Update
sudo apt-get update

# Install Node.js 22 via NodeSource
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally  
sudo npm install -g pm2

# Setup PM2 startup
pm2 startup
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $(whoami) --hp $(echo $HOME)

# Add hosts entry
echo "113.163.158.54 gitlab.vnptkiengiang.vn" | sudo tee -a /etc/hosts

# Verify installation
node --version   # Should show v22.x.x
npm --version    # Should show 10.x.x
pm2 --version    # Should show 6.x.x
cat /etc/hosts | grep gitlab
```

For PROXY server:

```bash
# Update
sudo apt-get update

# Install nginx
sudo apt-get install -y nginx

# Enable and start
sudo systemctl enable nginx
sudo systemctl start nginx

# Add hosts entry
echo "113.163.158.54 gitlab.vnptkiengiang.vn" | sudo tee -a /etc/hosts

# Verify
nginx -v
sudo systemctl status nginx
```

## 🔧 TROUBLESHOOTING

### Network Issues
1. Check if Jump Host can ping APP servers: `ping 10.68.2.5`
2. Check routing: `ip route show`
3. Check firewall: `sudo iptables -L -n`
4. Verify SSH service on target: `sudo systemctl status ssh`

### MySQL Issues
```bash
# On DB01, check MySQL container
sudo docker ps
sudo docker logs mysql-master

# Connect to MySQL
sudo docker exec -it mysql-master mysql -uroot -pSgdt@2026

# Check replication status
SHOW MASTER STATUS;
```

### Backup Issues
```bash
# On DB02, manually run backup
sudo /opt/scripts/mysql_backup_sync.sh

# Check logs
ls -la /var/log/mysql-backup/
cat /var/log/mysql-backup/sync_*.log

# Check cron
sudo crontab -u root -l
cat /etc/cron.d/mysql-backup
```
