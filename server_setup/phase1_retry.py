# -*- coding: utf-8 -*-
"""
Phase 1: Update & Upgrade - Retry version
"""

import paramiko
import time

def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)
    return client

def run_sudo(client, ip, cmd, timeout=1200):
    password = 'vnpt@123'
    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    stdout.channel.settimeout(timeout)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    code = stdout.channel.recv_exit_status()
    return output, error, code

def run_simple(client, ip, cmd, timeout=300):
    password = 'vnpt@123'
    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} '{cmd}'"
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    output = stdout.read().decode('utf-8', errors='ignore')
    return output.strip()

SERVERS = {
    "APP02": "10.67.2.12",
    "DB01": "10.68.2.11",
    "DB02": "10.68.2.12",
}

if __name__ == "__main__":
    client = get_ssh_client()
    print("Connected to Jump Host!")
    
    for name, ip in SERVERS.items():
        print("=" * 60)
        print(f"PHASE 1: UPDATE & UPGRADE {name} ({ip})")
        print("=" * 60)
        
        # Kill any existing apt processes first
        print(f"Checking for apt locks on {name}...")
        kill_cmd = "pkill -9 apt || true; pkill -9 dpkg || true; rm -f /var/lib/dpkg/lock-frontend /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock || true; dpkg --configure -a || true"
        out, err, code = run_sudo(client, ip, kill_cmd, timeout=120)
        print("Lock cleared.")
        
        # Update
        print(f"Running apt-get update on {name}...")
        cmd = "export DEBIAN_FRONTEND=noninteractive && apt-get update -y"
        out, err, code = run_sudo(client, ip, cmd, timeout=300)
        if "Reading package lists" in out:
            print(f"✅ {name}: apt-get update completed!")
        else:
            print(out[-500:] if out else err[-300:])
        
        # Upgrade
        print(f"Running apt-get upgrade on {name}...")
        cmd = "export DEBIAN_FRONTEND=noninteractive && apt-get upgrade -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold"
        out, err, code = run_sudo(client, ip, cmd, timeout=1200)
        
        if code == 0:
            print(f"✅ {name}: Update/Upgrade DONE!")
        else:
            print(f"⚠️ {name}: Exit code {code}")
            print(out[-500:] if out else err[-300:])
        
        print("\n")
    
    client.close()
    print("🎉 Phase 1 completed for remaining servers!")
