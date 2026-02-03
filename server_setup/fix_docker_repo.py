# Fix docker.list and install Docker
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
print("🔧 FIX DOCKER REPOSITORY AND INSTALL")
print("=" * 60)

for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    print(f"\n{'='*50}")
    print(f"[{name}] ({ip})")
    print(f"{'='*50}")
    
    # 1. Remove corrupted docker.list and gpg
    print("1. Cleaning up...")
    run_cmd(ip, "rm -f /etc/apt/sources.list.d/docker.list /etc/apt/keyrings/docker.gpg", timeout=20)
    run_cmd(ip, "rm -f /etc/apt/sources.list.d/docker.list.save 2>/dev/null || true", timeout=20)
    
    # 2. Verify cleanup
    out = run_cmd(ip, "ls -la /etc/apt/sources.list.d/", timeout=20)
    print(f"   Sources dir: {out.strip()[-100:]}")
    
    # 3. Update apt (should work now without docker.list)
    print("2. Testing apt update without docker...")
    out = run_cmd(ip, "apt-get update 2>&1 | tail -3", timeout=120)
    if "Err" in out:
        print(f"   Error: {out[-100:]}")
    else:
        print("   ✅ apt update OK")
    
    # 4. Setup Docker GPG properly
    print("3. Setting up Docker GPG key...")
    run_cmd(ip, "install -m 0755 -d /etc/apt/keyrings", timeout=20)
    
    # Download and dearmor GPG key
    out = run_cmd(ip, "curl -fsSL https://download.docker.com/linux/ubuntu/gpg 2>/dev/null | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && chmod a+r /etc/apt/keyrings/docker.gpg && echo OK", timeout=60)
    if "OK" in out:
        print("   ✅ GPG key added")
    else:
        print(f"   ⚠️ {out[-100:]}")
    
    # 5. Create docker.list with hardcoded correct value for Ubuntu 24.04 (noble)
    print("4. Creating docker.list for Ubuntu Noble (24.04)...")
    docker_repo = "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu noble stable"
    
    # Write file directly using echo with proper escaping
    run_cmd(ip, f'echo "{docker_repo}" > /etc/apt/sources.list.d/docker.list', timeout=20)
    
    # Verify the file content
    out = run_cmd(ip, "cat /etc/apt/sources.list.d/docker.list", timeout=20)
    print(f"   Content: {out.strip()[-80:]}")
    
    # 6. Update apt
    print("5. Updating apt with Docker repo...")
    out = run_cmd(ip, "apt-get update 2>&1 | grep -i docker || echo 'No docker errors'", timeout=120)
    print(f"   {out.strip()[:80]}")
    
    # 7. Check if docker-ce is available
    print("6. Checking Docker CE availability...")
    out = run_cmd(ip, "apt-cache policy docker-ce 2>/dev/null | head -5", timeout=30)
    if "Candidate:" in out and "none" not in out.lower():
        print(f"   ✅ Docker CE available!")
        candidate = [l for l in out.split('\n') if 'Candidate' in l]
        if candidate:
            print(f"   {candidate[0].strip()}")
    else:
        print(f"   ⚠️ {out[:100]}")
        continue
    
    # 8. Install Docker
    print("7. Installing Docker CE (this may take a few minutes)...")
    out = run_cmd(ip, "DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>&1 | tail -10", timeout=600)
    
    if "Setting up docker" in out or "already the newest" in out:
        print("   ✅ Docker installed!")
    else:
        print(f"   Output: {out[-200:]}")
    
    # 9. Start Docker
    print("8. Starting Docker service...")
    run_cmd(ip, "systemctl enable docker && systemctl start docker", timeout=60)
    time.sleep(3)
    
    # 10. Verify Docker
    out = run_cmd(ip, "docker --version 2>&1", timeout=30)
    if "Docker version" in out:
        version = [l for l in out.split('\n') if 'Docker version' in l][0]
        print(f"   ✅ {version}")
    else:
        print(f"   ⚠️ {out[:80]}")

print("\n" + "=" * 60)
print("📊 VERIFICATION")
print("=" * 60)

for name, ip in [("DB01", "10.68.2.11"), ("DB02", "10.68.2.12")]:
    out = run_cmd(ip, "docker --version && docker ps", timeout=30)
    docker_ok = "Docker version" in out
    print(f"[{name}] Docker: {'✅' if docker_ok else '❌'}")
    if docker_ok:
        version = [l for l in out.split('\n') if 'Docker version' in l]
        print(f"        {version[0] if version else ''}")

client.close()
