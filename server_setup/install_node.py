# Install Node.js 22 using NodeSource (faster & simpler)
import paramiko
from concurrent.futures import ThreadPoolExecutor

def get_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=30)
    return client

def run_sudo(client, ip, cmd, timeout=300):
    password = 'vnpt@123'
    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    out = stdout.read().decode()
    err = stderr.read().decode()
    code = stdout.channel.recv_exit_status()
    return out, err, code

NODE_INSTALL = '''
export DEBIAN_FRONTEND=noninteractive

# Install Node.js 22 from NodeSource
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs

# Install PM2 globally
npm install -g pm2

# Setup PM2 startup
pm2 startup systemd -u adminsgddt --hp /home/adminsgddt

# Verify
node -v
npm -v  
pm2 -v

echo "NODEJS_DONE"
'''

def install_node(name, ip):
    print(f"[{name}] 🚀 Installing Node.js 22 + PM2...")
    client = get_client()
    
    out, err, code = run_sudo(client, ip, NODE_INSTALL.replace("'", "'\"'\"'"), timeout=300)
    
    if "NODEJS_DONE" in out:
        # Get versions
        lines = [l for l in out.split('\n') if l.strip()]
        versions = lines[-4:-1]  # node -v, npm -v, pm2 -v
        print(f"[{name}] ✅ Installed: {' | '.join(versions)}")
    else:
        print(f"[{name}] ⚠️ Issue: {out[-300:]}")
    
    client.close()
    return name

if __name__ == "__main__":
    print("=" * 60)
    print("📦 Installing Node.js 22 + PM2 on APP servers")
    print("=" * 60)
    
    import time
    start = time.time()
    
    # Install in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(install_node, "APP01", "10.67.2.11"),
            executor.submit(install_node, "APP02", "10.67.2.12"),
        ]
        for f in futures:
            f.result()
    
    print(f"\n⏱️  Done in {time.time()-start:.1f}s")
