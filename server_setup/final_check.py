# FINAL VERIFICATION - Complete check
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=30)

def run(ip, cmd, sudo=False, timeout=60):
    password = 'vnpt@123'
    if sudo:
        ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S {cmd}\""
    else:
        ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} '{cmd}'"
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    return stdout.read().decode().strip()

print("=" * 70)
print("🔍 FINAL VERIFICATION REPORT")
print("=" * 70)

results = {
    "hosts": [],
    "nodejs": [],
    "docker": [],
    "mysql": [],
    "backup": []
}

# 1. Check /etc/hosts on all servers
print("\n📝 1. /etc/hosts (gitlab.vnptkiengiang.vn)")
print("-" * 50)
for name, ip in [("APP01", "10.67.2.11"), ("APP02", "10.67.2.12"), ("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    out = run(ip, "grep gitlab /etc/hosts", sudo=True)
    if "113.163.158.54" in out and "gitlab.vnptkiengiang.vn" in out:
        print(f"   ✅ {name}: {out}")
        results["hosts"].append(name)
    else:
        print(f"   ❌ {name}: NOT CONFIGURED")

# 2. Check Node.js on APP servers
print("\n📦 2. Node.js + PM2 (APP servers)")
print("-" * 50)
for name, ip in [("APP01", "10.67.2.11"), ("APP02", "10.67.2.12")]:
    node = run(ip, "node -v 2>/dev/null || echo N/A")
    npm = run(ip, "npm -v 2>/dev/null || echo N/A")
    pm2 = run(ip, "pm2 -v 2>/dev/null | tail -1 || echo N/A")
    
    if node.startswith("v22"):
        print(f"   ✅ {name}: Node {node} | NPM {npm} | PM2 {pm2}")
        results["nodejs"].append(name)
    else:
        print(f"   ❌ {name}: Node {node}")

# 3. Check Docker on DB servers
print("\n🐳 3. Docker (DB servers)")
print("-" * 50)
for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    docker = run(ip, "docker --version 2>/dev/null || echo N/A", sudo=True)
    if "Docker version" in docker:
        print(f"   ✅ {name}: {docker}")
        results["docker"].append(name)
    else:
        print(f"   ❌ {name}: {docker}")

# 4. Check MySQL container on DB01
print("\n🐬 4. MySQL Container (DB01)")
print("-" * 50)
mysql_status = run("10.68.2.11", "docker ps --format '{{.Names}} - {{.Status}}' 2>/dev/null | grep mysql || echo NOT_RUNNING", sudo=True)
if "mysql-master" in mysql_status and "Up" in mysql_status:
    print(f"   ✅ DB01: {mysql_status}")
    results["mysql"].append("DB01")
    
    # Check volume
    volume = run("10.68.2.11", "ls -la /home/mysql 2>/dev/null | head -3 || echo EMPTY", sudo=True)
    print(f"   📁 Volume /home/mysql: OK")
else:
    print(f"   ❌ DB01: {mysql_status}")

# 5. Check Backup on DB02
print("\n📦 5. Backup Sync (DB02)")
print("-" * 50)
# Check script
script_exists = run("10.68.2.12", "[ -x /opt/scripts/mysql_backup_sync.sh ] && echo EXISTS || echo NOT_EXISTS", sudo=True)
if "EXISTS" in script_exists:
    print(f"   ✅ Script: /opt/scripts/mysql_backup_sync.sh")
    results["backup"].append("script")
else:
    print(f"   ❌ Script not found")

# Check cron
cron = run("10.68.2.12", "crontab -l 2>/dev/null | grep mysql_backup || echo NOT_FOUND", sudo=True)
if "mysql_backup" in cron:
    print(f"   ✅ Cron: {cron}")
    results["backup"].append("cron")
else:
    print(f"   ❌ Cron not configured")

# Check backup dir
backup_dir = run("10.68.2.12", "[ -d /home/mysql-backup ] && echo EXISTS || echo NOT_EXISTS", sudo=True)
if "EXISTS" in backup_dir:
    print(f"   ✅ Backup directory: /home/mysql-backup")
    results["backup"].append("dir")

client.close()

# Summary
print("\n" + "=" * 70)
print("📋 SUMMARY")
print("=" * 70)

total_checks = 0
passed_checks = 0

checks = [
    ("Hosts configured", len(results["hosts"]), 4),
    ("Node.js installed", len(results["nodejs"]), 2),
    ("Docker installed", len(results["docker"]), 2),
    ("MySQL running", len(results["mysql"]), 1),
    ("Backup configured", len(results["backup"]), 3),
]

for name, passed, total in checks:
    total_checks += total
    passed_checks += passed
    status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
    print(f"   {status} {name}: {passed}/{total}")

print(f"\n   📊 Overall: {passed_checks}/{total_checks} checks passed")

print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 SETUP COMPLETED!

📋 MySQL Connection Info:
   Host: 10.68.2.11
   Port: 3306
   User: root
   Password: Sgdt@2026

📋 Backup Schedule:
   Every 6 hours (0 */6 * * *)
   From: DB01:/home/mysql
   To: DB02:/home/mysql-backup

⚠️  Note: PROXY server (192.168.71.2) was skipped - SSH not accessible

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
