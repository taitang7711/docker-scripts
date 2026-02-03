# -*- coding: utf-8 -*-
"""
SSH Manager - Kết nối SSH qua Jump Host sử dụng Paramiko
"""

import paramiko
import time
import socket
from config import JUMP_HOST, SERVERS


class SSHManager:
    def __init__(self):
        self.jump_client = None
        self.target_client = None
        
    def connect_jump_host(self):
        """Kết nối tới Jump Host"""
        print(f"🔌 Đang kết nối Jump Host {JUMP_HOST['host']}:{JUMP_HOST['port']}...")
        
        self.jump_client = paramiko.SSHClient()
        self.jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            self.jump_client.connect(
                hostname=JUMP_HOST['host'],
                port=JUMP_HOST['port'],
                username=JUMP_HOST['username'],
                password=JUMP_HOST['password'],
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            print("✅ Đã kết nối Jump Host thành công!")
            return True
        except Exception as e:
            print(f"❌ Lỗi kết nối Jump Host: {e}")
            return False
    
    def connect_target_server(self, server_name):
        """Kết nối tới server đích qua Jump Host"""
        if server_name not in SERVERS:
            print(f"❌ Server {server_name} không tồn tại trong config!")
            return False
            
        server = SERVERS[server_name]
        target_ip = server['ip']
        username = server['username']
        password = server['password']
        
        print(f"🔌 Đang kết nối tới {server_name} ({target_ip}) qua Jump Host...")
        
        try:
            # Tạo channel qua Jump Host
            jump_transport = self.jump_client.get_transport()
            dest_addr = (target_ip, 22)
            local_addr = ('127.0.0.1', 0)
            
            channel = jump_transport.open_channel(
                "direct-tcpip", 
                dest_addr, 
                local_addr,
                timeout=30
            )
            
            # Kết nối tới target qua channel
            self.target_client = paramiko.SSHClient()
            self.target_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.target_client.connect(
                hostname=target_ip,
                username=username,
                password=password,
                sock=channel,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            
            print(f"✅ Đã kết nối {server_name} thành công!")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi kết nối {server_name}: {e}")
            return False
    
    def execute_command(self, command, sudo=False, timeout=300):
        """Thực thi command trên target server"""
        if not self.target_client:
            print("❌ Chưa kết nối tới target server!")
            return None, None, -1
        
        if sudo:
            server_pass = JUMP_HOST['password']  # Same password for all
            command = f"echo '{server_pass}' | sudo -S bash -c '{command}'"
        
        print(f"⚡ Executing: {command[:80]}{'...' if len(command) > 80 else ''}")
        
        try:
            stdin, stdout, stderr = self.target_client.exec_command(
                command, 
                timeout=timeout,
                get_pty=True
            )
            
            # Đọc output
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code == 0:
                print(f"✅ Command thành công!")
            else:
                print(f"⚠️ Command exit code: {exit_code}")
                
            return output, error, exit_code
            
        except Exception as e:
            print(f"❌ Lỗi thực thi command: {e}")
            return None, str(e), -1
    
    def execute_script(self, script_content, sudo=False):
        """Thực thi một script nhiều dòng"""
        # Escape script và chạy
        escaped_script = script_content.replace("'", "'\"'\"'")
        command = f"bash -c '{escaped_script}'"
        return self.execute_command(command, sudo=sudo, timeout=600)
    
    def close_target(self):
        """Đóng kết nối target server"""
        if self.target_client:
            self.target_client.close()
            self.target_client = None
            print("🔌 Đã đóng kết nối target server")
    
    def close_all(self):
        """Đóng tất cả kết nối"""
        self.close_target()
        if self.jump_client:
            self.jump_client.close()
            self.jump_client = None
            print("🔌 Đã đóng kết nối Jump Host")


# Test connection
if __name__ == "__main__":
    ssh = SSHManager()
    if ssh.connect_jump_host():
        for server_name in SERVERS:
            if ssh.connect_target_server(server_name):
                output, error, code = ssh.execute_command("hostname && whoami")
                print(f"Output: {output}")
                ssh.close_target()
    ssh.close_all()
