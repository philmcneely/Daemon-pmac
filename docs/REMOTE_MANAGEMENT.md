# Remote Server Management Guide

This guide covers managing your Daemon server remotely, specifically for scenarios where your server is in a different location (e.g., Germany) and you're managing it from elsewhere (e.g., USA).

## 📋 Deployment Types

Your remote server can be deployed in two ways, and the commands differ:

### **🖥️ Bare Metal Deployment (Recommended)**
- **Setup**: Uses `setup-pi.sh` script
- **Location**: `/opt/daemon/`
- **Python**: Uses virtual environment at `/opt/daemon/venv/`
- **Commands**: `cd /opt/daemon && venv/bin/python -m app.cli ...`

### **🐳 Docker Deployment**
- **Setup**: Uses Docker Compose
- **Location**: `/app/` (inside container)
- **Python**: Container Python (no venv needed)
- **Commands**: `docker exec daemon-container python -m app.cli ...`

**⚠️ Important**: Make sure you use the correct commands for your deployment type!

## 🌍 Remote Access Methods

### 1. **API-Based Management (Recommended)**

The cleanest way to manage your remote server is through the API:

#### **Setup Environment**
```bash
# Set your server URL as an environment variable
export DAEMON_URL="https://daemon.example.com"
ADMIN_USER="jime"
export DAEMON_ADMIN_PASS="your_secure_password"
```

#### **Authentication Helper Script**
Create a helper script to manage authentication:

```bash
#!/bin/bash
# auth-helper.sh

get_token() {
    curl -s -X POST "$DAEMON_URL/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$DAEMON_ADMIN_USER&password=$DAEMON_ADMIN_PASS" | \
        jq -r '.access_token'
}

# Usage
TOKEN=$(get_token)
echo "Token: $TOKEN"
```

#### **User Management**
```bash
# Create new user with complete setup
create_user() {
    local username=$1
    local email=$2
    local password=$3

    curl -X POST "$DAEMON_URL/api/v1/setup/user/$username" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"$username\",
            \"email\": \"$email\",
            \"password\": \"$password\",
            \"is_admin\": false
        }"
}

# Usage
TOKEN=$(get_token)
create_user "janee" "janee@example.com" "secure_password"
```

#### **Data Management**
```bash
# Import data for all users
import_all_data() {
    curl -X POST "$DAEMON_URL/api/v1/import/all" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json"
}

# Import specific user data
import_user_data() {
    local username=$1
    curl -X POST "$DAEMON_URL/api/v1/import/user/$username" \
        -H "Authorization: Bearer $TOKEN"
}

# Check system status
check_status() {
    curl -s "$DAEMON_URL/api/v1/system/info" | jq .
    curl -s "$DAEMON_URL/health" | jq .
}
```

### 2. **SSH-Based Management**

For direct server access when you need more control:

#### **SSH Configuration**
```bash
# Add to ~/.ssh/config
Host daemon-server
    HostName your-german-server.com
    User daemon-user
    IdentityFile ~/.ssh/daemon-key
    Port 22
    ServerAliveInterval 60
```

#### **Remote CLI Usage**

**For Bare Metal Deployment (using setup-pi.sh):**
```bash
# Connect and run commands (uses virtual environment)
ssh daemon-server "cd /opt/daemon && venv/bin/python -m app.cli create-user admin"
ssh daemon-server "cd /opt/daemon && venv/bin/python -m app.cli import-all-data"

# Interactive session
ssh daemon-server
cd /opt/daemon
source venv/bin/activate
python -m app.cli create-user janee --admin
python -m app.cli import-user-data admin --data-dir data/private/admin
```

**For Docker Deployment:**
```bash
# Connect and run commands in container
ssh daemon-server "docker exec daemon-container python -m app.cli create-user admin"
ssh daemon-server "docker exec daemon-container python -m app.cli import-all-data"
```

### 3. **File Transfer Methods**

#### **SCP for Data Files**

**For Bare Metal Deployment:**
```bash
# Upload user data directories
scp -r ./data/private/admin/ daemon-server:/opt/daemon/data/private/admin/
scp -r ./data/private/janee/ daemon-server:/opt/daemon/data/private/janee/

# Upload and import in one go
upload_and_import() {
    local username=$1
    local local_dir="./data/private/$username"
    local remote_dir="/opt/daemon/data/private/$username"

    # Upload files
    scp -r "$local_dir/" "daemon-server:$remote_dir/"

    # Import via SSH (using virtual environment)
    ssh daemon-server "cd /opt/daemon && venv/bin/python -m app.cli import-user-data $username"
}
```

**For Docker Deployment:**
```bash
# Upload to temp directory then copy to container
scp -r ./data/private/admin/ daemon-server:/tmp/
ssh daemon-server "docker cp /tmp/admin/ daemon-container:/app/data/private/"
ssh daemon-server "docker exec daemon-container python -m app.cli import-user-data admin"
```

#### **rsync for Synchronization**

**For Bare Metal Deployment:**
```bash
# Sync data directories (more efficient)
rsync -avz --progress ./data/private/ daemon-server:/opt/daemon/data/private/

# Sync with deletion (careful!)
rsync -avz --delete ./data/private/ daemon-server:/opt/daemon/data/private/
```

**For Docker Deployment:**
```bash
# Sync to temp directory then copy to container
rsync -avz --progress ./data/private/ daemon-server:/tmp/daemon-data/
ssh daemon-server "docker cp /tmp/daemon-data/ daemon-container:/app/data/private/"
```

### 4. **Docker-Based Management**

If your server runs via Docker:

#### **Docker Compose Management**
```bash
# Connect to server and manage containers
ssh daemon-server "cd /opt/daemon && docker-compose restart"
ssh daemon-server "cd /opt/daemon && docker-compose logs -f"

# Execute commands in container
ssh daemon-server "docker exec daemon-container python -m app.cli create-user admin"
```

#### **Volume Management**
```bash
# Copy data to Docker volume
scp -r ./data/private/admin/ daemon-server:/tmp/
ssh daemon-server "docker cp /tmp/admin/ daemon-container:/app/data/private/"
ssh daemon-server "docker exec daemon-container python -m app.cli import-user-data admin"
```

## 🔧 Complete Remote Setup Scripts

### **Setup Script for Multiple Users**
```bash
#!/bin/bash
# remote-setup.sh

DAEMON_URL="https://daemon.example.com"
ADMIN_USER="admin"
ADMIN_PASS="your_secure_password"

# Function to get auth token
get_token() {
    curl -s -X POST "$DAEMON_URL/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$ADMIN_USER&password=$ADMIN_PASS" | \
        jq -r '.access_token'
}

# Function to create user
create_user() {
    local username=$1
    local email=$2
    local password=${3:-"temp_password_$username"}

    echo "Creating user: $username"

    response=$(curl -s -X POST "$DAEMON_URL/api/v1/setup/user/$username" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"$username\",
            \"email\": \"$email\",
            \"password\": \"$password\",
            \"is_admin\": false
        }")

    if echo "$response" | jq -e '.success' > /dev/null; then
        echo "✓ User $username created successfully"
    else
        echo "❌ Failed to create user $username"
        echo "$response" | jq .
    fi
}

# Function to check system status
check_system() {
    echo "System Status:"
    curl -s "$DAEMON_URL/api/v1/system/info" | jq .
    echo -e "\nHealth Check:"
    curl -s "$DAEMON_URL/health" | jq .
}

# Main execution
echo "🚀 Remote Daemon Setup Starting..."

# Get authentication token
TOKEN=$(get_token)
if [[ "$TOKEN" == "null" || -z "$TOKEN" ]]; then
    echo "❌ Failed to authenticate. Check credentials."
    exit 1
fi
echo "✓ Authentication successful"

# Create users
create_user "janee" "janee@example.com"
create_user "brianc" "brian.c@example.com"
create_user "sarah" "sarah@example.com"

# Import data for all users
echo "📥 Importing data for all users..."
import_response=$(curl -s -X POST "$DAEMON_URL/api/v1/import/all" \
    -H "Authorization: Bearer $TOKEN")

if echo "$import_response" | jq -e '.success' > /dev/null; then
    echo "✓ Data import completed"
    echo "$import_response" | jq '.users_processed[] | "  - \(.username): \(.total_entries) entries"'
else
    echo "⚠ Data import had issues"
    echo "$import_response" | jq .
fi

# Final system check
echo -e "\n📊 Final System Status:"
check_system

echo -e "\n🎉 Remote setup complete!"
echo "Your server is now configured with multiple users."
echo "Access endpoints like: $DAEMON_URL/api/v1/resume/users/admin"
```

### **Data Sync Script**
```bash
#!/bin/bash
# sync-data.sh

LOCAL_DATA_DIR="./data/private"
REMOTE_SERVER="daemon-server"
DAEMON_URL="https://daemon.pmac.dev"

# Set deployment type
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-bare-metal}"  # or "docker"

if [[ "$DEPLOYMENT_TYPE" == "docker" ]]; then
    REMOTE_DATA_DIR="/app/data/private"
    REMOTE_PYTHON_CMD="docker exec daemon-container python"
else
    REMOTE_DATA_DIR="/opt/daemon/data/private"
    REMOTE_PYTHON_CMD="cd /opt/daemon && venv/bin/python"
fi

sync_and_import() {
    echo "🔄 Syncing data to remote server ($DEPLOYMENT_TYPE deployment)..."

    if [[ "$DEPLOYMENT_TYPE" == "docker" ]]; then
        # Docker: sync to temp dir then copy to container
        echo "Syncing to temporary directory..."
        rsync -avz --progress "$LOCAL_DATA_DIR/" "$REMOTE_SERVER:/tmp/daemon-data/"

        echo "Copying to Docker container..."
        ssh "$REMOTE_SERVER" "docker cp /tmp/daemon-data/ daemon-container:/app/data/private/"
    else
        # Bare metal: direct sync
        rsync -avz --progress "$LOCAL_DATA_DIR/" "$REMOTE_SERVER:$REMOTE_DATA_DIR/"
    fi

    if [[ $? -eq 0 ]]; then
        echo "✓ File sync completed"

        # Trigger import via API
        TOKEN=$(get_token)
        if [[ -n "$TOKEN" && "$TOKEN" != "null" ]]; then
            echo "📥 Triggering data import..."
            curl -X POST "$DAEMON_URL/api/v1/import/all" \
                -H "Authorization: Bearer $TOKEN"
        fi
    else
        echo "❌ File sync failed"
        exit 1
    fi
}

# Usage
sync_and_import
```

## ⏰ Time Zone Considerations

### **Server Time vs Local Time**
```bash
# Check server time
ssh daemon-server "date"
curl "$DAEMON_URL/health" | jq '.timestamp'

# Convert timestamps
# Server in Germany (CET/CEST), you in USA (EST/EDT)
# Server is typically 6-9 hours ahead depending on DST
```

### **Scheduled Operations**
- **Backups**: Run on German server time (usually 2-3 AM CET)
- **Maintenance**: Plan during German night hours (10 PM - 6 AM CET)
- **Rate limits**: Reset based on server time
- **Log rotation**: Happens on server schedule

## 🔐 Security Best Practices

### **Authentication**
- Use strong passwords for all accounts
- Rotate JWT tokens regularly (they expire automatically)
- Consider API keys for automated scripts
- Use SSH keys instead of passwords for CLI access

### **Network Security**
- Always use HTTPS for API calls
- Consider VPN for sensitive operations
- Whitelist your IP if possible
- Monitor failed login attempts

### **Data Protection**
- Encrypt data in transit (HTTPS/SSH)
- Regular backups (automated on server)
- Monitor audit logs
- Test restore procedures

## 🚨 Troubleshooting Remote Issues

### **Connection Problems**
```bash
# Test basic connectivity
curl -I "$DAEMON_URL/health"

# Check if server is responding
ping your-german-server.com

# Test SSH connectivity
ssh -T daemon-server "echo 'Connection successful'"
```

### **Authentication Issues**
```bash
# Verify credentials
curl -X POST "$DAEMON_URL/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=jime&password=wrongpassword"

# Check token expiration
echo "$TOKEN" | base64 -d | jq .
```

### **Import Problems**
```bash
# Check file permissions (deployment specific)
# For Docker deployment:
ssh daemon-server "docker exec daemon-container ls -la /app/data/private/"

# For bare metal deployment:
ssh daemon-server "ls -la /opt/daemon/data/private/"

# Verify data format (deployment specific)
# For Docker deployment:
ssh daemon-server "docker exec daemon-container python -m json.tool /app/data/private/jime/resume.json"

# For bare metal deployment:
ssh daemon-server "cd /opt/daemon && venv/bin/python -m json.tool data/private/username/resume.json"

# Check server logs (deployment specific)
# For Docker deployment:
ssh daemon-server "docker logs daemon-container --tail 100"

# For bare metal deployment:
ssh daemon-server "tail -f /opt/daemon/logs/daemon.log"
```

This setup allows you to fully manage your German server from anywhere in the world! 🌍
