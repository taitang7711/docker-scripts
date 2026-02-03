# Debug check for APP servers and MySQL
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

def run_cmd(ip, cmd, timeout=60):
    password = 'vnpt@123'
    full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"{cmd}\""
    try:
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        return (out + err).strip()
    except Exception as e:
        return str(e)

print("=" * 60)
print("🔍 DETAILED CHECK")
print("=" * 60)

# Check APP servers without sudo
print("\n[APP01] Checking Node.js (no sudo)...")
out = run_cmd("10.68.2.5", "node --version", timeout=20)
print(f"  node --version: {out}")

out = run_cmd("10.68.2.5", "which node", timeout=20)
print(f"  which node: {out}")

out = run_cmd("10.68.2.5", "cat /etc/hosts | grep gitlab", timeout=20)
print(f"  /etc/hosts: {out}")

print("\n[APP02] Checking Node.js (no sudo)...")
out = run_cmd("10.68.2.6", "node --version", timeout=20)
print(f"  node --version: {out}")

out = run_cmd("10.68.2.6", "cat /etc/hosts | grep gitlab", timeout=20)
print(f"  /etc/hosts: {out}")

# Check MySQL on DB01
print("\n[DB01] Checking MySQL container...")
out = run_cmd("10.68.2.11", "docker ps -a", timeout=20)
print(f"  docker ps -a:\n{out}")

out = run_cmd("10.68.2.11", "docker logs mysql-master 2>&1 | tail -10", timeout=30)
print(f"\n  mysql-master logs:\n{out}")

client.close()
