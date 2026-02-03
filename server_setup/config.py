# -*- coding: utf-8 -*-
"""
Cấu hình Server SGDDT Infrastructure
"""

# Jump Host Configuration
JUMP_HOST = {
    "host": "127.0.0.1",
    "port": 2222,
    "username": "adminsgddt",
    "password": "vnpt@123"
}

# Server List
SERVERS = {
    "PROXY": {
        "ip": "192.168.71.2",
        "role": "proxy",
        "username": "adminsgddt",
        "password": "vnpt@123"
    },
    "APP01": {
        "ip": "10.67.2.11",
        "role": "app",
        "username": "adminsgddt",
        "password": "vnpt@123"
    },
    "APP02": {
        "ip": "10.67.2.12",
        "role": "app",
        "username": "adminsgddt",
        "password": "vnpt@123"
    },
    "DB01": {
        "ip": "10.68.2.11",
        "role": "db_master",
        "username": "adminsgddt",
        "password": "vnpt@123"
    },
    "DB02": {
        "ip": "10.68.2.12",
        "role": "db_backup",
        "username": "adminsgddt",
        "password": "vnpt@123"
    }
}

# MySQL Configuration
MYSQL_CONFIG = {
    "root_password": "Sgdt@2026",
    "volume_path": "/home/mysql",
    "container_name": "mysql-master",
    "port": 3306
}

# Hosts entry
HOSTS_ENTRY = "113.163.158.54 gitlab.vnptkiengiang.vn"
