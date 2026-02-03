# 📋 PLAN SETUP SERVERS - SGDDT Infrastructure

> **Ngày tạo:** 02/02/2026  
> **Cập nhật:** 02/02/2026 - Execution completed  
> **Tổng số Server:** 5  
> **Jump Host:** 127.0.0.1:2222

---

## 🖥️ THÔNG TIN SERVER

| STT | Server | IP | Vai trò | Cài đặt | Status |
|-----|--------|-----|---------|---------|--------|
| 1 | PROXY | 192.168.71.2 | Reverse Proxy | Nginx (latest) | ⚠️ SSH unreachable |
| 2 | APP 01 | 10.68.2.5 | Application | NVM, Node.js 22.x, PM2 | ❌ Network unreachable |
| 3 | APP 02 | 10.68.2.6 | Application | NVM, Node.js 22.x, PM2 | ❌ Network unreachable |
| 4 | DB 01 | 10.68.2.11 | Database Master | Docker, MySQL Container | ✅ DONE |
| 5 | DB 02 | 10.68.2.12 | Database Backup | Backup Sync Job | ✅ DONE |

**Credentials chung:**
- User: `adminsgddt`
- Password: `vnpt@123`

**MySQL Credentials (DB 01):**
- User: `root`
- Password: `Sgdt@2026`

---

## ✅ CHECKLIST THỰC HIỆN

### Phase 1: Chuẩn bị môi trường (TẤT CẢ SERVER)

| ☐ | Task | Command | Ghi chú |
|---|------|---------|---------|
| ☐ | Update packages | `sudo apt-get update` | Tất cả 5 server |
| ☐ | Upgrade packages | `sudo apt-get upgrade -y` | Tất cả 5 server |
| ☐ | Cấu hình /etc/hosts | Thêm `113.163.158.54 gitlab.vnptkiengiang.vn` | Tất cả 5 server |

---

### Phase 2: PROXY Server (192.168.71.2)

| ☐ | Task | Chi tiết |
|---|------|----------|
| ☐ | Cài đặt nginx dependencies | `apt install curl gnupg2 ca-certificates lsb-release ubuntu-keyring` |
| ☐ | Thêm nginx signing key | Import nginx official GPG key |
| ☐ | Thêm nginx repository | Mainline hoặc Stable repository |
| ☐ | Cài đặt nginx | `apt install nginx` |
| ☐ | Enable nginx service | `systemctl enable nginx` |
| ☐ | Start nginx service | `systemctl start nginx` |
| ☐ | Verify nginx | `nginx -v` và `systemctl status nginx` |

---

### Phase 3: APP 01 & APP 02 (10.67.2.11, 10.67.2.12)

| ☐ | Task | Chi tiết |
|---|------|----------|
| ☐ | Cài đặt NVM | `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh \| bash` |
| ☐ | Load NVM | `source ~/.bashrc` |
| ☐ | Cài đặt Node.js 22.x | `nvm install 22` |
| ☐ | Set default Node | `nvm alias default 22` |
| ☐ | Cài đặt PM2 global | `npm install -g pm2` |
| ☐ | Setup PM2 startup | `pm2 startup` |
| ☐ | Verify versions | `node -v`, `npm -v`, `pm2 -v` |

---

### Phase 4: DB 01 - MySQL Docker (10.68.2.11)

| ☐ | Task | Chi tiết |
|---|------|----------|
| ☐ | Cài đặt Docker | Chạy script docker-scripts-v2.sh |
| ☐ | Tạo thư mục volume | `mkdir -p /home/mysql` |
| ☐ | Set permissions | `chmod 755 /home/mysql` |
| ☐ | Pull MySQL image | `docker pull mysql:latest` |
| ☐ | Chạy MySQL container | Xem command bên dưới |
| ☐ | Verify MySQL | `docker ps` và test connection |

**Docker Run Command:**
```bash
docker run -d \
  --name mysql-master \
  --restart always \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=Sgdt@2026 \
  -v /home/mysql:/var/lib/mysql \
  mysql:latest
```

---

### Phase 5: DB 02 - Backup Sync (10.68.2.12)

| ☐ | Task | Chi tiết |
|---|------|----------|
| ☐ | Cài đặt Docker | Chạy script docker-scripts-v2.sh |
| ☐ | Tạo thư mục backup | `mkdir -p /home/mysql-backup` |
| ☐ | Cài đặt rsync | `apt install rsync` |
| ☐ | Setup SSH key | Tạo key pair để rsync không cần password |
| ☐ | Tạo backup script | `/opt/scripts/mysql_backup_sync.sh` |
| ☐ | Setup crontab | Chạy định kỳ (mỗi giờ/mỗi ngày) |
| ☐ | Test sync | Chạy thử script backup |

---

## 📊 EXECUTION SUMMARY (02/02/2026)

### ✅ COMPLETED

| Server | Task | Status | Details |
|--------|------|--------|---------|
| DB01 | /etc/hosts | ✅ | `113.163.158.54 gitlab.vnptkiengiang.vn` |
| DB02 | /etc/hosts | ✅ | `113.163.158.54 gitlab.vnptkiengiang.vn` |
| DB01 | Docker | ✅ | Docker version 29.2.0 |
| DB02 | Docker | ✅ | Docker version 29.2.0 |
| DB01 | MySQL Container | ✅ | mysql-master running, MySQL 9.6.0, port 3306 |
| DB02 | Backup Script | ✅ | /opt/scripts/mysql_backup_sync.sh |
| DB02 | Cron Job | ✅ | `0 */6 * * *` (every 6 hours) |
| DB02 | Initial Backup | ✅ | Data synced from DB01:/home/mysql |

### ❌ NOT REACHABLE (Network Issue)

| Server | IP | Issue | Action Required |
|--------|-----|-------|-----------------|
| PROXY | 192.168.71.2 | SSH timeout | Check network routing from Jump Host |
| APP01 | 10.68.2.5 | Ping/SSH failed | Network unreachable - check firewall/routing |
| APP02 | 10.68.2.6 | Ping/SSH failed | Network unreachable - check firewall/routing |

### 📋 Manual Action Required

To complete setup for APP01 & APP02, either:
1. **Fix network** between Jump Host and APP servers (10.68.2.x subnet)
2. **SSH directly** to APP servers and run:
   ```bash
   # Install Node.js 22
   curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Install PM2
   sudo npm install -g pm2
   
   # Add hosts entry
   echo "113.163.158.54 gitlab.vnptkiengiang.vn" | sudo tee -a /etc/hosts
   
   # Verify
   node --version
   pm2 --version
   cat /etc/hosts | grep gitlab
   ```

---
1. Stop MySQL container trên DB01 (nếu cần)
2. Rsync `/home/mysql` từ DB01 → DB02
3. Restart MySQL container trên DB01
4. Log kết quả

---

## 📁 CẤU TRÚC FILE SẼ TẠO

```
server_setup/
├── main.py                    # Entry point chính
├── config.py                  # Cấu hình server & credentials
├── ssh_manager.py             # Quản lý SSH qua jump host (paramiko)
├── requirements.txt           # Dependencies Python
│
├── scripts/
│   ├── 01_common_update.sh    # apt update/upgrade cho tất cả
│   ├── 02_hosts_setup.sh      # Cấu hình /etc/hosts
│   ├── 03_nginx_install.sh    # Cài nginx cho PROXY
│   ├── 04_nodejs_install.sh   # Cài nvm, node, pm2 cho APP
│   ├── 05_docker_install.sh   # Cài Docker cho DB servers
│   ├── 06_mysql_docker.sh     # Chạy MySQL container (DB01)
│   └── 07_backup_sync.sh      # Backup job (DB02)
│
└── logs/
    └── setup_YYYYMMDD.log     # Log quá trình thực hiện
```

---

## 🔄 THỨ TỰ THỰC HIỆN

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: Update & Upgrade tất cả server                    │
│  ├── PROXY (192.168.71.2)                                   │
│  ├── APP 01 (10.67.2.11)                                    │
│  ├── APP 02 (10.67.2.12)                                    │
│  ├── DB 01 (10.68.2.11)                                     │
│  └── DB 02 (10.68.2.12)                                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: Cấu hình /etc/hosts (tất cả server)               │
│  → Thêm: 113.163.158.54 gitlab.vnptkiengiang.vn             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: Cài đặt theo vai trò                              │
│  ├── PROXY → Nginx (latest)                                 │
│  ├── APP 01, APP 02 → NVM + Node 22.x + PM2                 │
│  ├── DB 01 → Docker + MySQL Container                       │
│  └── DB 02 → Docker + Backup Sync Job                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: Verify & Test                                     │
│  ├── Test nginx: curl http://192.168.71.2                   │
│  ├── Test node: node -v trên APP servers                    │
│  ├── Test MySQL: mysql -h 10.68.2.11 -u root -p             │
│  └── Test Backup: Chạy thử sync job                         │
└─────────────────────────────────────────────────────────────┘
```

---

## ⏰ LỊCH BACKUP DỰ KIẾN (DB 02)

| Option | Crontab | Mô tả |
|--------|---------|-------|
| Mỗi giờ | `0 * * * *` | Backup mỗi giờ đúng |
| Mỗi 6 giờ | `0 */6 * * *` | Backup 4 lần/ngày |
| Mỗi ngày 2:00 AM | `0 2 * * *` | Backup lúc 2 giờ sáng |
| Mỗi tuần CN 3:00 AM | `0 3 * * 0` | Backup hàng tuần |

**Đề xuất:** Mỗi 6 giờ (`0 */6 * * *`) - cân bằng giữa độ fresh của data và tải server.

---

## ⚠️ LƯU Ý QUAN TRỌNG

1. **SSH Jump Host:** Tất cả kết nối đều phải qua `127.0.0.1:2222`
2. **Sudo required:** Hầu hết commands cần sudo
3. **Firewall:** Đảm bảo các port sau được mở:
   - PROXY: 80, 443
   - APP: 3000 (hoặc port app)
   - DB: 3306 (chỉ internal)
4. **Backup volume:** MySQL volume = `/home/mysql` (không phải /var/lib/mysql)
5. **Script Python:** Sử dụng `paramiko` thay vì `sshpass` để an toàn hơn

---

## 🚀 READY TO EXECUTE?

Sau khi confirm plan này, tôi sẽ tạo:
1. `server_setup/main.py` - Script chính
2. Các shell scripts trong `scripts/`
3. File `requirements.txt`

**Confirm để bắt đầu tạo code!**
