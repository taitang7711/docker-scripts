# -*- coding: utf-8 -*-
"""
Phase 1: Update & Upgrade - Fire and forget version
"""

import paramiko
import time

def get_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)
    return client

def fire_and_forget(client, ip, cmd):
    """Chạy command không đợi kết quả"""
    password = 'vnpt@123'
    # Dùng nohup và redirect để không block
    full_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 adminsgddt@{ip} \"echo '{password}' | sudo -S nohup bash -c '{cmd}' > /tmp/cmd.log 2>&1 &\""
    client.exec_command(full_cmd, timeout=30)
    time.sleep(2)

def run_quick(client, ip, cmd, sudo=True, timeout=60):
    """Chạy command nhanh"""
    password = 'vnpt@123'
    if sudo:
        ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 adminsgddt@{ip} \"echo '{password}' | sudo -S {cmd}\""
    else:
        ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 adminsgddt@{ip} '{cmd}'"
    
    try:
        stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
        output = stdout.read().decode('utf-8', errors='ignore')
        return output.strip()
    except:
        return ""

SERVERS = {
    "APP01": "10.67.2.11",
    "APP02": "10.67.2.12",
    "DB01": "10.68.2.11",
    "DB02": "10.68.2.12",
}

if __name__ == "__main__":
    print("🔌 Connecting to Jump Host...")
    client = get_client()
    print("✅ Connected!\n")
    
    # First, start upgrade on all servers in background
    for name, ip in SERVERS.items():
        print(f"{'='*60}")
        print(f"📦 Starting update/upgrade on {name} ({ip})")
        print(f"{'='*60}")
        
        # Clear locks first
        run_quick(client, ip, "pkill -9 apt; pkill -9 dpkg; rm -f /var/lib/dpkg/lock* /var/lib/apt/lists/lock /var/cache/apt/archives/lock; dpkg --configure -a; true", sudo=True, timeout=30)
        
        # Start update+upgrade in background
        upgrade_script = "export DEBIAN_FRONTEND=noninteractive; apt-get update -y && apt-get upgrade -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold"
        fire_and_forget(client, ip, upgrade_script)
        print(f"   ⏳ Upgrade started in background on {name}")
    
    print(f"\n{'='*60}")
    print("⏳ Waiting for upgrades to complete (checking every 30s)...")
    print(f"{'='*60}")
    
    # Monitor progress
    completed = set()
    for attempt in range(20):  # Max 10 minutes
        time.sleep(30)
        print(f"\n[Check {attempt+1}]")
        
        for name, ip in SERVERS.items():
            if name in completed:
                continue
            
            # Check if apt is still running
            result = run_quick(client, ip, "pgrep -c apt-get || echo 0", sudo=False, timeout=30)
            
            if result == "0" or result == "":
                # Check last log
                log = run_quick(client, ip, "tail -3 /tmp/cmd.log 2>/dev/null || echo 'No log'", sudo=True, timeout=30)
                print(f"   ✅ {name}: Upgrade completed!")
                print(f"      Last log: {log[:100]}")
                completed.add(name)
            else:
                print(f"   ⏳ {name}: Still upgrading...")
        
        if len(completed) == len(SERVERS):
            break
    
    client.close()
    
    print(f"\n{'='*60}")
    print("🎉 Phase 1 COMPLETED!")
    print(f"{'='*60}")
    print(f"✅ Completed: {', '.join(completed)}")
    remaining = set(SERVERS.keys()) - completed
    if remaining:
        print(f"⏳ Still running: {', '.join(remaining)}")
