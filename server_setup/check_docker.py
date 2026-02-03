# Check Docker status directly
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=30)

def run(ip, cmd, timeout=60):
    ssh_cmd = f"sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} '{cmd}'"
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    return stdout.read().decode().strip()

print("=" * 60)
print("🔍 CHECKING DOCKER STATUS ON DB SERVERS")
print("=" * 60)

for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    print(f"\n[{name}] ({ip})")
    print("-" * 40)
    
    # Check docker command
    docker_v = run(ip, "docker --version 2>/dev/null || echo NOT_FOUND")
    print(f"  docker --version: {docker_v}")
    
    # Check systemd service
    docker_svc = run(ip, "systemctl is-active docker 2>/dev/null || echo INACTIVE")
    print(f"  docker service: {docker_svc}")
    
    # Check docker ps
    docker_ps = run(ip, "docker ps 2>/dev/null || echo ERROR")
    print(f"  docker ps: {docker_ps[:100]}")

print("\n" + "=" * 60)
print("🔍 CHECKING MYSQL ON DB01")
print("=" * 60)

mysql_ps = run("10.68.2.11", "docker ps -a --format '{{.Names}} {{.Status}}' 2>/dev/null | grep mysql || echo NOT_FOUND")
print(f"MySQL container: {mysql_ps}")

mysql_volume = run("10.68.2.11", "ls -la /home/mysql 2>/dev/null | head -5 || echo NOT_FOUND")
print(f"MySQL volume:\n{mysql_volume}")

print("\n" + "=" * 60)
print("🔍 CHECKING BACKUP ON DB02")
print("=" * 60)

backup_script = run("10.68.2.12", "cat /opt/scripts/mysql_backup_sync.sh 2>/dev/null || echo NOT_FOUND")
print(f"Backup script exists: {'YES' if 'rsync' in backup_script else 'NO'}")

backup_cron = run("10.68.2.12", "crontab -l 2>/dev/null | grep mysql || echo NOT_FOUND")
print(f"Backup cron: {backup_cron}")

client.close()
