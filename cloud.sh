#!/bin/bash

set -e

# Add cloudflare gpg key
# Add cloudflare gpg key
# Add cloudflare gpg key
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-public-v2.gpg | sudo tee /usr/share/keyrings/cloudflare-public-v2.gpg >/dev/null

# Add this repo to your apt repositories
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-public-v2.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list

# install cloudflared
sudo apt-get update && sudo apt-get install cloudflared -y

sudo cloudflared service install eyJhIjoiZjY4Mjk2ZjI5MmQ4Y2I4YTZmNmJlY2FjMTFmZmFhMWUiLCJ0IjoiMDA2YjIyYzYtMWE3Zi00Njc2LWFkNDAtYzA5MWQxZDIxYTY1IiwicyI6IlpqYzFPVEZqTVdFdFpXUXpZaTAwTWpBMExXRmxNRFV0Tm1SallUYzRNR1pqTm1VdyJ9

echo "cloudflared version:"
cloudflared --version