#!/bin/bash

set -e

echo "===== KIỂM TRA DOCKER ====="

if command -v docker >/dev/null 2>&1; then
    echo "✅ Docker đã được cài đặt."
    docker --version
else
    echo "❌ Docker chưa được cài đặt. Bắt đầu cài đặt Docker..."

    # Cập nhật hệ thống
    apt update -y

    # Cài các gói cần thiết
    apt install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Thêm Docker GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    # Thêm Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" \
      | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Cập nhật lại apt
    apt update -y

    # Cài Docker
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    echo "🎉 Cài đặt Docker hoàn tất!"
fi

echo "===== KIỂM TRA SAU CÙNG ====="
docker --version
systemctl status docker --no-pager --lines=5

echo "✅ Docker đã sẵn sàng sử dụng."
