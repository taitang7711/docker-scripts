# Install Docker CE now that repo is working
import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

def run_cmd(ip, cmd, timeout=600):
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
print("🐳 INSTALLING DOCKER CE ON DB SERVERS")
print("=" * 60)

for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    print(f"\n{'='*50}")
    print(f"[{name}] ({ip}) - Installing Docker CE...")
    print(f"{'='*50}")
    
    # Install Docker packages
    print("Installing docker-ce docker-ce-cli containerd.io...")
    out = run_cmd(ip, "DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>&1", timeout=900)
    
    if "Setting up docker" in out or "already the newest" in out or "is already the newest version" in out:
        print("✅ Docker packages installed!")
    elif "Unable to locate package" in out or "E: Package" in out:
        print(f"❌ Package error: {out[-300:]}")
        continue
    else:
        # Still might have installed, check
        print(f"Output (last 300 chars): {out[-300:]}")
    
    # Enable and start Docker
    print("Enabling and starting Docker service...")
    run_cmd(ip, "systemctl enable docker", timeout=30)
    run_cmd(ip, "systemctl start docker", timeout=30)
    time.sleep(3)
    
    # Verify Docker
    out = run_cmd(ip, "docker --version 2>&1", timeout=30)
    if "Docker version" in out:
        version = [l for l in out.split('\n') if 'Docker version' in l][0]
        print(f"✅ {version.strip()}")
    else:
        print(f"⚠️ Docker check: {out[:100]}")

# Final verification
print("\n" + "=" * 60)
print("📊 FINAL DOCKER VERIFICATION")
print("=" * 60)

docker_status = {}
for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    out = run_cmd(ip, "docker --version && systemctl is-active docker 2>&1", timeout=30)
    if "Docker version" in out:
        version = [l for l in out.split('\n') if 'Docker version' in l][0]
        active = "active" in out
        print(f"[{name}] ✅ Docker installed: {version.strip()}")
        print(f"        Service: {'active ✅' if active else 'not active ⚠️'}")
        docker_status[name] = True
    else:
        print(f"[{name}] ❌ Docker not installed")
        docker_status[name] = False

client.close()

# Summary
print("\n" + "=" * 60)
if all(docker_status.values()):
    print("🎉 DOCKER INSTALLED ON ALL DB SERVERS!")
    print("Next: Run mysql_setup.py to create MySQL container on DB01")
else:
    print("⚠️ Some servers failed. Check output above.")
print("=" * 60)
