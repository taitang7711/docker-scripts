# Test SSH connectivity from Jump Host
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

print("=" * 60)
print("🔌 SSH CONNECTIVITY TEST FROM JUMP HOST")
print("=" * 60)

# Run test directly on jump host
test_script = '''
echo "Testing SSH to servers..."
for ip in 10.68.2.5 10.68.2.6 10.68.2.11 10.68.2.12; do
    echo -n "Testing $ip: "
    timeout 5 sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@$ip "hostname" 2>&1 || echo "FAILED"
done
'''

stdin, stdout, stderr = client.exec_command(test_script, timeout=60)
out = stdout.read().decode()
err = stderr.read().decode()
print(out)
print(err)

print("\n" + "=" * 60)
print("🔍 CHECKING APP01 in detail")
print("=" * 60)

# Try detailed check on APP01
check_app01 = '''
echo "=== Checking APP01 (10.68.2.5) ==="
sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@10.68.2.5 << 'ENDSSH'
echo "Hostname: $(hostname)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME)"
echo "Hosts entry: $(grep gitlab /etc/hosts 2>/dev/null || echo 'not found')"
echo "Node: $(which node 2>/dev/null || echo 'not found')"
echo "Node version: $(node --version 2>/dev/null || echo 'not installed')"
echo "PM2: $(which pm2 2>/dev/null || echo 'not found')"
echo "NodeSource: $(ls /etc/apt/sources.list.d/ | grep -i node 2>/dev/null || echo 'not found')"
ENDSSH
'''

stdin, stdout, stderr = client.exec_command(check_app01, timeout=60)
out = stdout.read().decode()
err = stderr.read().decode()
print(out)
if err:
    print(f"Errors: {err}")

client.close()
