# Debug with sudo for all
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

def run_sudo(ip, cmd, timeout=60):
    password = 'vnpt@123'
    full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S {cmd} 2>&1\""
    try:
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        return (out + err).strip()
    except Exception as e:
        return str(e)

def run_user(ip, cmd, timeout=60):
    password = 'vnpt@123'
    full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"{cmd} 2>&1\""
    try:
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        return (out + err).strip()
    except Exception as e:
        return str(e)

print("=" * 60)
print("🔍 DETAILED DEBUG CHECK")
print("=" * 60)

# Check APP01
print("\n[APP01] (10.68.2.5)")
print("-" * 40)

# First check basic connectivity
out = run_user("10.68.2.5", "hostname")
print(f"  hostname: {out}")

out = run_sudo("10.68.2.5", "cat /etc/hosts | grep -v password")
print(f"  /etc/hosts:\n{out[-200:]}")

out = run_sudo("10.68.2.5", "which node")
print(f"  which node: {out}")

out = run_sudo("10.68.2.5", "ls -la /usr/bin/node 2>/dev/null || echo 'not found'")
print(f"  /usr/bin/node: {out}")

out = run_user("10.68.2.5", "source ~/.bashrc && node --version 2>&1 || echo 'failed'")
print(f"  node --version: {out}")

# Check NodeSource installation
out = run_sudo("10.68.2.5", "ls -la /etc/apt/sources.list.d/ | grep node || echo 'no nodesource'")
print(f"  nodesource: {out[-100:]}")

out = run_sudo("10.68.2.5", "dpkg -l | grep nodejs || echo 'nodejs not installed'")
print(f"  dpkg nodejs: {out[-100:]}")

# Check DB01 MySQL
print("\n[DB01] (10.68.2.11)")
print("-" * 40)

out = run_sudo("10.68.2.11", "docker ps -a --format 'table {{.Names}}\\t{{.Status}}'")
print(f"  docker ps:\n{out}")

out = run_sudo("10.68.2.11", "docker logs mysql-master 2>&1 | tail -5")
print(f"  mysql logs: {out[-200:]}")

client.close()
