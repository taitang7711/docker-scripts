#!/bin/bash

set -e

# Add cloudflare gpg key
docker run -d --name cloudflared-tunnel --restart=always cloudflare/cloudflared:latest tunnel --no-autoupdate run --token eyJhIjoiZjY4Mjk2ZjI5MmQ4Y2I4YTZmNmJlY2FjMTFmZmFhMWUiLCJ0IjoiMDA2YjIyYzYtMWE3Zi00Njc2LWFkNDAtYzA5MWQxZDIxYTY1IiwicyI6IlpqYzFPVEZqTVdFdFpXUXpZaTAwTWpBMExXRmxNRFV0Tm1SallUYzRNR1pqTm1VdyJ9
echo "CLOUDFLARE_TUNNEL_STARTED"