# Check and fix Node.js on APP servers
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=30)

def run(ip, cmd, timeout=60):
    ssh_cmd = f"sshpass -p 'vnpt@123' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} '{cmd}'"
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    return stdout.read().decode().strip()

def run_sudo(ip, cmd, timeout=120):
    password = 'vnpt@123'
    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    return stdout.read().decode().strip()

print("=" * 50)
print("Checking Node.js on APP servers...")
print("=" * 50)

for name, ip in [("APP01", "10.67.2.11"), ("APP02", "10.67.2.12")]:
    print(f"\n=== {name} ({ip}) ===")
    
    # Check if nvm exists
    nvm_check = run(ip, "[ -d ~/.nvm ] && echo EXISTS || echo NOT_EXISTS")
    print(f"NVM directory: {nvm_check}")
    
    # Check node
    node_v = run(ip, "source ~/.nvm/nvm.sh 2>/dev/null && node -v 2>/dev/null || echo NOT_FOUND")
    print(f"Node version: {node_v}")
    
    # Check pm2
    pm2_v = run(ip, "source ~/.nvm/nvm.sh 2>/dev/null && pm2 -v 2>/dev/null || echo NOT_FOUND")
    print(f"PM2 version: {pm2_v}")
    
    if "NOT_FOUND" in node_v or "NOT_FOUND" in pm2_v:
        print(f"\n🔧 Fixing Node.js on {name}...")
        
        # Install node directly
        fix_cmd = """
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
        nvm install 22 2>/dev/null || true
        nvm use 22
        npm install -g pm2
        node -v && pm2 -v
        """
        result = run(ip, fix_cmd.replace('\n', ' '), timeout=180)
        print(f"Fix result: {result}")

client.close()
print("\n✅ Check completed!")
