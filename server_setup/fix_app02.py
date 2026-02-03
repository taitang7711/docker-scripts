# Fix APP02 and verify all
import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=30)

def run_sudo(ip, cmd, timeout=300):
    password = 'vnpt@123'
    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    return stdout.read().decode()

ip = "10.67.2.12"
print("=" * 60)
print("🔧 Fixing APP02 (10.67.2.12)")
print("=" * 60)

# Kill locks
print("🔓 Clearing apt locks...")
run_sudo(ip, "pkill -9 apt; pkill -9 dpkg; rm -f /var/lib/dpkg/lock* /var/lib/apt/lists/lock; dpkg --configure -a; true", timeout=60)
time.sleep(3)

# Install Node.js
print("📦 Installing Node.js 22...")
out = run_sudo(ip, """
export DEBIAN_FRONTEND=noninteractive
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs
npm install -g pm2
node -v && npm -v && pm2 -v
echo DONE
""".replace("'", "'\"'\"'"), timeout=300)

print(out[-500:])

client.close()

# Verify both
print("\n" + "=" * 60)
print("✅ FINAL VERIFICATION")
print("=" * 60)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=30)

def run(ip, cmd):
    ssh_cmd = f"sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} '{cmd}'"
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=60)
    return stdout.read().decode().strip()

for name, ip in [("APP01", "10.67.2.11"), ("APP02", "10.67.2.12")]:
    node = run(ip, "node -v")
    npm = run(ip, "npm -v")
    pm2 = run(ip, "pm2 -v")
    print(f"{name}: Node {node} | NPM {npm} | PM2 {pm2}")

client.close()
