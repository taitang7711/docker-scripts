# Fix crontab properly using base64 encoding
import paramiko
import base64

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

def run_cmd(ip, cmd, timeout=120):
    password = 'vnpt@123'
    full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    try:
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        return out + err
    except Exception as e:
        return str(e)

print("=" * 60)
print("⏰ FIXING CRON JOB ON DB02 (Using base64)")
print("=" * 60)

ip = "10.68.2.12"

# Cron file content for /etc/cron.d/
cron_content = """# MySQL Backup Cron Job
# Runs every 6 hours
0 */6 * * * root /opt/scripts/mysql_backup_sync.sh
"""

# Root crontab content
root_crontab = "0 */6 * * * /opt/scripts/mysql_backup_sync.sh\n"

# Encode
cron_b64 = base64.b64encode(cron_content.encode()).decode()
root_b64 = base64.b64encode(root_crontab.encode()).decode()

# 1. Create /etc/cron.d/mysql-backup
print("\n1. Creating /etc/cron.d/mysql-backup...")
run_cmd(ip, f"echo '{cron_b64}' | base64 -d > /etc/cron.d/mysql-backup", timeout=30)
run_cmd(ip, "chmod 644 /etc/cron.d/mysql-backup", timeout=20)

out = run_cmd(ip, "cat /etc/cron.d/mysql-backup", timeout=20)
print(f"   Content:\n{out.strip()}")

# 2. Set root crontab
print("\n2. Setting root crontab...")
run_cmd(ip, f"echo '{root_b64}' | base64 -d | crontab -u root -", timeout=30)

out = run_cmd(ip, "crontab -u root -l 2>&1", timeout=20)
print(f"   Root crontab: {out.strip()}")

# 3. Restart cron
print("\n3. Restarting cron service...")
run_cmd(ip, "systemctl restart cron", timeout=30)
out = run_cmd(ip, "systemctl is-active cron", timeout=20)
print(f"   Cron service: {out.strip()}")

client.close()

print("\n" + "=" * 60)
print("✅ CRON FIXED!")
print("=" * 60)
