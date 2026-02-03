# -*- coding: utf-8 -*-
"""
SSH Manager V2 - Chạy SSH command từ Jump Host
"""

import paramiko
import time

# Jump Host Configuration
JUMP_HOST = {
    "host": "127.0.0.1",
    "port": 2222,
    "username": "adminsgddt",
    "password": "vnpt@123"
}

# Server List
SERVERS = {
    "PROXY": {"ip": "192.168.71.2", "role": "proxy"},
    "APP01": {"ip": "10.67.2.11", "role": "app"},
    "APP02": {"ip": "10.67.2.12", "role": "app"},
    "DB01": {"ip": "10.68.2.11", "role": "db_master"},
    "DB02": {"ip": "10.68.2.12", "role": "db_backup"},
}

USERNAME = "adminsgddt"
PASSWORD = "vnpt@123"


class SSHManagerV2:
    def __init__(self):
        self.client = None
        
    def connect(self):
        """Kết nối tới Jump Host"""
        print(f"🔌 Connecting to Jump Host...")
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            JUMP_HOST['host'], 
            port=JUMP_HOST['port'], 
            username=JUMP_HOST['username'], 
            password=JUMP_HOST['password'],
            timeout=30
        )
        print("✅ Connected to Jump Host!")
        return True
    
    def run_on_server(self, server_name, command, sudo=False, timeout=600):
        """Chạy command trên server qua SSH từ Jump Host"""
        if server_name not in SERVERS:
            print(f"❌ Server {server_name} not found!")
            return None, None, -1
        
        ip = SERVERS[server_name]['ip']
        
        # Build SSH command từ Jump Host
        if sudo:
            # Sử dụng sshpass để tự động nhập password
            ssh_cmd = f"sshpass -p '{PASSWORD}' ssh -o StrictHostKeyChecking=no {USERNAME}@{ip} \"echo '{PASSWORD}' | sudo -S bash -c '{command}'\""
        else:
            ssh_cmd = f"sshpass -p '{PASSWORD}' ssh -o StrictHostKeyChecking=no {USERNAME}@{ip} \"{command}\""
        
        print(f"⚡ Running on {server_name} ({ip}): {command[:60]}...")
        
        try:
            stdin, stdout, stderr = self.client.exec_command(ssh_cmd, timeout=timeout)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            exit_code = stdout.channel.recv_exit_status()
            return output, error, exit_code
        except Exception as e:
            print(f"❌ Error: {e}")
            return None, str(e), -1
    
    def close(self):
        if self.client:
            self.client.close()
            print("🔌 Connection closed")


def run_task(server_name, command, sudo=True, description=""):
    """Helper function để chạy một task"""
    ssh = SSHManagerV2()
    ssh.connect()
    
    print(f"\n{'='*60}")
    print(f"📋 {description}")
    print(f"🖥️  Server: {server_name}")
    print(f"{'='*60}")
    
    output, error, code = ssh.run_on_server(server_name, command, sudo=sudo)
    
    if output:
        # Chỉ in 1500 ký tự cuối
        print(output[-1500:])
    if error and code != 0:
        print(f"⚠️ Error: {error[-500:]}")
    
    ssh.close()
    
    return code == 0, output


if __name__ == "__main__":
    # Test
    ssh = SSHManagerV2()
    ssh.connect()
    output, error, code = ssh.run_on_server("PROXY", "hostname && whoami")
    print(f"Output: {output}")
    ssh.close()
