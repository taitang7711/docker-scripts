# Upload and run script on Jump Host
import paramiko
import time

print("=" * 60)
print("🚀 UPLOADING AND RUNNING INSTALL SCRIPT ON JUMP HOST")
print("=" * 60)

# Read the script
with open('scripts/install_docker.sh', 'r') as f:
    script_content = f.read()

# Connect to jump host
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('127.0.0.1', port=2222, username='adminsgddt', password='vnpt@123', timeout=60)

# Upload script using SFTP
sftp = client.open_sftp()
with sftp.file('/tmp/install_docker.sh', 'w') as f:
    f.write(script_content)
sftp.close()

print("✅ Script uploaded to Jump Host: /tmp/install_docker.sh")

# Make executable and run
print("\n🔧 Running installation script...")
print("(This may take several minutes)")
print("-" * 60)

stdin, stdout, stderr = client.exec_command('chmod +x /tmp/install_docker.sh && bash /tmp/install_docker.sh', timeout=1800)

# Stream output
for line in iter(stdout.readline, ""):
    print(line.rstrip())

err = stderr.read().decode()
if err:
    print(f"Errors: {err[-500:]}")

client.close()
print("\n✅ Installation completed!")
