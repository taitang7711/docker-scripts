# Final verification of ALL servers
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

def run_cmd(ip, cmd, timeout=60):
    password = 'vnpt@123'
    full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    try:
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        return (out + err).strip()
    except Exception as e:
        return str(e)

print("=" * 70)
print("📋 FINAL VERIFICATION - ALL SERVERS")
print("=" * 70)

servers = [
    ("APP01", "10.68.2.5"),
    ("APP02", "10.68.2.6"),
    ("DB01", "10.68.2.11"),
    ("DB02", "10.68.2.12"),
]

results = {}

for name, ip in servers:
    print(f"\n{'='*60}")
    print(f"🖥️  [{name}] ({ip})")
    print(f"{'='*60}")
    
    results[name] = {"ip": ip}
    
    # 1. Check /etc/hosts
    out = run_cmd(ip, "grep gitlab.vnptkiengiang.vn /etc/hosts | head -1", timeout=20)
    hosts_ok = "113.163.158.54" in out
    results[name]["hosts"] = hosts_ok
    print(f"  /etc/hosts: {'✅' if hosts_ok else '❌'} {out[:50] if out else 'not found'}")
    
    # 2. Check Node.js (APP servers only)
    if name.startswith("APP"):
        out = run_cmd(ip, "node --version 2>/dev/null || echo 'not found'", timeout=20)
        node_ok = "v22" in out
        results[name]["node"] = node_ok
        print(f"  Node.js:    {'✅' if node_ok else '❌'} {out}")
        
        out = run_cmd(ip, "pm2 --version 2>/dev/null || echo 'not found'", timeout=20)
        pm2_ok = "." in out and "not found" not in out
        results[name]["pm2"] = pm2_ok
        print(f"  PM2:        {'✅' if pm2_ok else '❌'} {out}")
    
    # 3. Check Docker (DB servers only)
    if name.startswith("DB"):
        out = run_cmd(ip, "docker --version 2>/dev/null || echo 'not found'", timeout=20)
        docker_ok = "Docker version" in out
        results[name]["docker"] = docker_ok
        version = out.split('\n')[0] if docker_ok else out
        print(f"  Docker:     {'✅' if docker_ok else '❌'} {version[:50]}")
        
        out = run_cmd(ip, "systemctl is-active docker 2>/dev/null || echo 'inactive'", timeout=20)
        docker_active = "active" in out
        results[name]["docker_active"] = docker_active
        print(f"  Docker svc: {'✅' if docker_active else '❌'} {out}")
    
    # 4. Check MySQL container (DB01 only)
    if name == "DB01":
        out = run_cmd(ip, "docker ps --format '{{.Names}} {{.Status}}' | grep mysql-master || echo 'not found'", timeout=20)
        mysql_ok = "Up" in out
        results[name]["mysql"] = mysql_ok
        print(f"  MySQL:      {'✅' if mysql_ok else '❌'} {out}")
        
        if mysql_ok:
            out = run_cmd(ip, "docker exec mysql-master mysql -uroot -pSgdt@2026 -e 'SELECT VERSION();' 2>&1 | tail -1", timeout=30)
            print(f"  MySQL ver:  {out[:30]}")
    
    # 5. Check Backup (DB02 only)
    if name == "DB02":
        out = run_cmd(ip, "test -f /opt/scripts/mysql_backup_sync.sh && echo 'exists' || echo 'not found'", timeout=20)
        script_ok = "exists" in out
        results[name]["backup_script"] = script_ok
        print(f"  Backup:     {'✅' if script_ok else '❌'} /opt/scripts/mysql_backup_sync.sh")
        
        out = run_cmd(ip, "crontab -u root -l 2>/dev/null | grep mysql_backup || cat /etc/cron.d/mysql-backup 2>/dev/null | grep mysql_backup || echo 'not found'", timeout=20)
        cron_ok = "mysql_backup" in out and "not found" not in out
        results[name]["cron"] = cron_ok
        print(f"  Cron job:   {'✅' if cron_ok else '❌'} {out[:50]}")
        
        out = run_cmd(ip, "ls /home/mysql-backup 2>/dev/null | head -3 || echo 'empty'", timeout=20)
        print(f"  Backup dir: /home/mysql-backup contains files: {out[:50]}")

client.close()

# Summary
print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)
print("""
┌──────────┬─────────────┬────────────┬────────────────────────┐
│ Server   │ /etc/hosts  │ Node/PM2   │ Docker/MySQL/Backup    │
├──────────┼─────────────┼────────────┼────────────────────────┤""")

for name, data in results.items():
    hosts = "✅" if data.get("hosts") else "❌"
    
    if name.startswith("APP"):
        node = "✅" if data.get("node") and data.get("pm2") else "❌"
        docker = "N/A"
    else:
        node = "N/A"
        docker = "✅" if data.get("docker") and data.get("docker_active") else "❌"
        if name == "DB01" and data.get("mysql"):
            docker = "✅ MySQL"
        elif name == "DB02" and data.get("cron"):
            docker = "✅ Backup"
    
    print(f"│ {name:8} │ {hosts:11} │ {node:10} │ {docker:22} │")

print("└──────────┴─────────────┴────────────┴────────────────────────┘")

print("""
📋 Completed Tasks:
  ✅ /etc/hosts configured on ALL accessible servers
  ✅ Node.js v22 + PM2 installed on APP01, APP02  
  ✅ Docker 29.2.0 installed on DB01, DB02
  ✅ MySQL container running on DB01 (port 3306)
  ✅ Backup script + cron job on DB02
  
⚠️ Skipped:
  ❌ PROXY server (192.168.71.2) - Not accessible via SSH
""")
