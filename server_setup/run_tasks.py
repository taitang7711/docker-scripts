# -*- coding: utf-8 -*-
"""
Run Tasks Script - Chạy từng task theo checklist
"""

import paramiko
import sys

def get_ssh_client():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=30)
    return client

def run_on_server(client, server_ip, command, sudo=False, timeout=600):
    """Chạy command trên server qua sshpass"""
    password = 'vnpt@123'
    
    if sudo:
        ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{server_ip} \"echo '{password}' | sudo -S bash -c '{command}'\""
    else:
        ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no adminsgddt@{server_ip} '{command}'"
    
    stdin, stdout, stderr = client.exec_command(ssh_cmd, timeout=timeout)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    exit_code = stdout.channel.recv_exit_status()
    
    return output, error, exit_code

# Server IPs
SERVERS = {
    "PROXY": "192.168.71.2",
    "APP01": "10.67.2.11",
    "APP02": "10.67.2.12",
    "DB01": "10.68.2.11",
    "DB02": "10.68.2.12",
}

if __name__ == "__main__":
    client = get_ssh_client()
    print("Connected to Jump Host!")
    
    # Test all servers
    for name, ip in SERVERS.items():
        output, error, code = run_on_server(client, ip, "hostname && uname -a")
        print(f"=== {name} ({ip}) ===")
        print(output if output else error)
    
    client.close()
