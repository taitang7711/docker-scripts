# Check network connectivity to APP servers
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

print("=" * 60)
print("🔌 NETWORK CONNECTIVITY CHECK")
print("=" * 60)

# Test ping and SSH from Jump Host
test_script = '''
echo "=== Ping Test ==="
for ip in 10.68.2.5 10.68.2.6 10.68.2.11 10.68.2.12 192.168.71.2; do
    echo -n "$ip: "
    ping -c 1 -W 2 $ip >/dev/null 2>&1 && echo "PING OK" || echo "PING FAILED"
done

echo ""
echo "=== SSH Test (with verbose) ==="
echo "APP01 (10.68.2.5):"
timeout 10 sshpass -p 'vnpt@123' ssh -v -o StrictHostKeyChecking=no -o ConnectTimeout=5 adminsgddt@10.68.2.5 "echo connected" 2>&1 | tail -20

echo ""
echo "DB01 (10.68.2.11):"
timeout 10 sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 adminsgddt@10.68.2.11 "echo connected" 2>&1
'''

stdin, stdout, stderr = client.exec_command(test_script, timeout=90)
out = stdout.read().decode()
err = stderr.read().decode()
print(out)
if err:
    print(f"STDERR: {err}")

client.close()
