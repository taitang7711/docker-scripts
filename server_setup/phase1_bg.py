# -*- coding: utf-8 -*-
"""
Phase 1: Update & Upgrade - Background version
Chạy upgrade ở background và kiểm tra status
"""

import paramiko
import time
import sys

def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)
    return client

def run_cmd(client, ip, cmd, sudo=False, timeout=300):
    password = 'vnpt@123'
    if sudo:
        ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    else:
        ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} '{cmd}'"
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    code = stdout.channel.recv_exit_status()
    return output, error, code

SERVERS = {
    "APP02": "10.67.2.12",
    "DB01": "10.68.2.11",
    "DB02": "10.68.2.12",
}

def update_server(client, name, ip):
    print(f"\n{'='*60}")
    print(f"📦 {name} ({ip})")
    print(f"{'='*60}")
    
    # Clear locks
    print("🔓 Clearing apt locks...")
    kill_cmd = "pkill -9 apt 2>/dev/null; pkill -9 dpkg 2>/dev/null; rm -f /var/lib/dpkg/lock-frontend /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock 2>/dev/null; dpkg --configure -a 2>/dev/null; true"
    run_cmd(client, ip, kill_cmd, sudo=True, timeout=120)
    
    # Update
    print("📥 apt-get update...")
    cmd = "export DEBIAN_FRONTEND=noninteractive && apt-get update -y 2>&1 | tail -5"
    out, err, code = run_cmd(client, ip, cmd, sudo=True, timeout=300)
    print(out if out else "Done")
    
    # Upgrade in background with nohup
    print("⬆️  apt-get upgrade (background)...")
    upgrade_cmd = "export DEBIAN_FRONTEND=noninteractive && nohup apt-get upgrade -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold > /tmp/upgrade.log 2>&1 &"
    run_cmd(client, ip, upgrade_cmd, sudo=True, timeout=60)
    print("   Upgrade started in background...")
    
    # Wait and check status
    time.sleep(10)
    for i in range(30):  # Check every 10 seconds, max 5 minutes
        out, _, _ = run_cmd(client, ip, "pgrep -f 'apt-get upgrade' && echo RUNNING || echo DONE", sudo=False, timeout=30)
        if "DONE" in out:
            # Get result
            log_out, _, _ = run_cmd(client, ip, "tail -10 /tmp/upgrade.log", sudo=True, timeout=60)
            print(f"   {log_out}")
            print(f"✅ {name}: Update/Upgrade COMPLETED!")
            return True
        else:
            print(f"   Still upgrading... ({(i+1)*10}s)")
            time.sleep(10)
    
    print(f"⚠️ {name}: Upgrade taking too long, continuing...")
    return False

if __name__ == "__main__":
    client = get_ssh_client()
    print("🔌 Connected to Jump Host!")
    
    for name, ip in SERVERS.items():
        update_server(client, name, ip)
    
    client.close()
    print("\n🎉 Phase 1 completed!")
