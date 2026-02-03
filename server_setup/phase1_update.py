# -*- coding: utf-8 -*-
"""
Phase 1: Update & Upgrade all servers
"""

import paramiko

def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=30)
    return client

def run_sudo(client, ip, cmd, timeout=600):
    password = 'vnpt@123'
    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{ip} \"echo '{password}' | sudo -S bash -c '{cmd}'\""
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    code = stdout.channel.recv_exit_status()
    return output, error, code

SERVERS = {
    "APP01": "10.67.2.11",
    "APP02": "10.67.2.12",
    "DB01": "10.68.2.11",
    "DB02": "10.68.2.12",
}

if __name__ == "__main__":
    client = get_ssh_client()
    print("Connected to Jump Host!")
    
    for name, ip in SERVERS.items():
        print("=" * 60)
        print(f"PHASE 1: UPDATE {name} ({ip})")
        print("=" * 60)
        
        # Update
        cmd = "export DEBIAN_FRONTEND=noninteractive && apt-get update -y"
        out, err, code = run_sudo(client, ip, cmd)
        print(out[-800:] if out else err[-500:])
        
        # Upgrade
        print(f"\nUpgrading {name}...")
        cmd = "export DEBIAN_FRONTEND=noninteractive && apt-get upgrade -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold"
        out, err, code = run_sudo(client, ip, cmd, timeout=900)
        print(out[-800:] if out else err[-500:])
        
        if code == 0:
            print(f"✅ {name}: Update/Upgrade DONE!")
        else:
            print(f"⚠️ {name}: Exit code {code}")
        print("\n")
    
    client.close()
    print("🎉 Phase 1 completed!")
