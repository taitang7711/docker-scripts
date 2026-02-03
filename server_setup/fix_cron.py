# Fix crontab for root user on DB02
import paramiko

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
print("⏰ FIXING CRON JOB ON DB02")
print("=" * 60)

ip = "10.68.2.12"

# Method 1: Write directly to /etc/cron.d/
print("\n1. Creating cron file in /etc/cron.d/...")
cron_content = "0 */6 * * * root /opt/scripts/mysql_backup_sync.sh"
run_cmd(ip, f'echo "{cron_content}" > /etc/cron.d/mysql-backup', timeout=30)
run_cmd(ip, "chmod 644 /etc/cron.d/mysql-backup", timeout=20)

# Verify
out = run_cmd(ip, "cat /etc/cron.d/mysql-backup", timeout=20)
print(f"   Cron file content: {out.strip()}")

# Method 2: Also add to root's crontab using -u root
print("\n2. Adding to root crontab...")
run_cmd(ip, 'echo "0 */6 * * * /opt/scripts/mysql_backup_sync.sh" | crontab -u root -', timeout=30)

# Verify root crontab
out = run_cmd(ip, "crontab -u root -l 2>&1", timeout=20)
print(f"   Root crontab: {out.strip()[:80]}")

# Restart cron service
print("\n3. Restarting cron service...")
run_cmd(ip, "systemctl restart cron", timeout=30)
out = run_cmd(ip, "systemctl status cron | head -3", timeout=20)
print(f"   {out.strip()[:80]}")

client.close()

print("\n" + "=" * 60)
print("✅ CRON SETUP COMPLETE!")
print("=" * 60)
