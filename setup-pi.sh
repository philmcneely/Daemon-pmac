#!/bin/bash

# Daemon-pmac Setup Script for Raspberry Pi
# This script automates the installation and setup of Daemon-pmac

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/daemon-pmac"
SERVICE_USER="daemon"
PYTHON_VERSION="3.11"

echo -e "${GREEN}=== Daemon-pmac Setup Script ===${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root${NC}"
   exit 1
fi

# Check if Python 3.11+ is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo -e "${RED}Python 3.9+ is required. Found: ${PYTHON_VER}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python ${PYTHON_VER} detected${NC}"

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    sqlite3 \
    nginx \
    supervisor \
    curl \
    git

echo -e "${GREEN}✓ System dependencies installed${NC}"

# Create service user
if ! id "$SERVICE_USER" &>/dev/null; then
    echo -e "${YELLOW}Creating service user: $SERVICE_USER${NC}"
    sudo useradd --system --shell /bin/bash --home-dir $PROJECT_DIR --create-home $SERVICE_USER
    echo -e "${GREEN}✓ Service user created${NC}"
else
    echo -e "${GREEN}✓ Service user already exists${NC}"
fi

# Create project directory
echo -e "${YELLOW}Setting up project directory...${NC}"
sudo mkdir -p $PROJECT_DIR
sudo chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR

# Copy application files
echo -e "${YELLOW}Copying application files...${NC}"
if [ -d "app" ]; then
    sudo -u $SERVICE_USER cp -r app $PROJECT_DIR/
    sudo -u $SERVICE_USER cp requirements.txt $PROJECT_DIR/
    sudo -u $SERVICE_USER cp -r tests $PROJECT_DIR/ 2>/dev/null || true
else
    echo -e "${RED}Error: Application files not found. Run this script from the Daemon-pmac directory.${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${YELLOW}Creating Python virtual environment...${NC}"
sudo -u $SERVICE_USER python3 -m venv $PROJECT_DIR/venv
sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install --upgrade pip

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt

echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Create directories
echo -e "${YELLOW}Creating application directories...${NC}"
sudo -u $SERVICE_USER mkdir -p $PROJECT_DIR/{data,backups,logs}

# Create .env file if it doesn't exist
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Creating environment configuration...${NC}"

    # Generate secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    sudo -u $SERVICE_USER tee $ENV_FILE > /dev/null <<EOF
# Environment Configuration
SECRET_KEY=$SECRET_KEY
DATABASE_URL=sqlite:///$PROJECT_DIR/data/daemon.db
BACKUP_DIR=$PROJECT_DIR/backups

# Server Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=false
RELOAD=false

# Security
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60
CORS_ORIGINS=["http://localhost", "http://127.0.0.1"]

# Features
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
METRICS_ENABLED=true
LOGGING_LEVEL=INFO

# API Configuration
API_PREFIX=/api/v1
DOCS_URL=/docs
REDOC_URL=/redoc
EOF

    echo -e "${GREEN}✓ Environment configuration created${NC}"
else
    echo -e "${GREEN}✓ Environment configuration already exists${NC}"
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
cd $PROJECT_DIR
sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/python -m app.cli db init

# Create default admin user
echo -e "${YELLOW}Setting up admin user...${NC}"
echo -e "${YELLOW}Please enter admin user details:${NC}"
read -p "Admin username: " ADMIN_USER
read -p "Admin email: " ADMIN_EMAIL
read -s -p "Admin password: " ADMIN_PASS
echo

sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/python -m app.cli user create "$ADMIN_USER" "$ADMIN_EMAIL" --password="$ADMIN_PASS" --admin

echo -e "${GREEN}✓ Admin user created${NC}"

# Install systemd service
echo -e "${YELLOW}Installing systemd service...${NC}"
sudo tee /etc/systemd/system/daemon-pmac.service > /dev/null <<EOF
[Unit]
Description=Daemon-pmac Personal API
After=network.target

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$PROJECT_DIR

# Resource limits
LimitNOFILE=65535
MemoryLimit=512M

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable daemon-pmac

echo -e "${GREEN}✓ Systemd service installed${NC}"

# Configure nginx
echo -e "${YELLOW}Configuring nginx...${NC}"
sudo tee /etc/nginx/sites-available/daemon-pmac > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check - no rate limiting
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/daemon-pmac /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo -e "${GREEN}✓ Nginx configured${NC}"

# Set up log rotation
echo -e "${YELLOW}Setting up log rotation...${NC}"
sudo tee /etc/logrotate.d/daemon-pmac > /dev/null <<EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    postrotate
        systemctl reload daemon-pmac
    endscript
}
EOF

echo -e "${GREEN}✓ Log rotation configured${NC}"

# Create backup script
echo -e "${YELLOW}Creating backup script...${NC}"
sudo tee /usr/local/bin/daemon-backup > /dev/null <<EOF
#!/bin/bash
cd $PROJECT_DIR
sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/python -m app.cli backup create
sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/python -m app.cli backup cleanup
EOF

sudo chmod +x /usr/local/bin/daemon-backup

# Set up daily backup cron job
echo -e "${YELLOW}Setting up daily backup...${NC}"
sudo tee /etc/cron.d/daemon-pmac-backup > /dev/null <<EOF
# Daily backup at 2 AM
0 2 * * * root /usr/local/bin/daemon-backup >/dev/null 2>&1
EOF

echo -e "${GREEN}✓ Daily backup configured${NC}"

# Start services
echo -e "${YELLOW}Starting services...${NC}"
sudo systemctl start daemon-pmac
sudo systemctl status daemon-pmac --no-pager -l

# Test the installation
echo -e "${YELLOW}Testing installation...${NC}"
sleep 5

if curl -f http://localhost/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Installation successful!${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo -e "${YELLOW}Check the service status: sudo systemctl status daemon-pmac${NC}"
    exit 1
fi

# Display summary
echo -e "${GREEN}"
echo "=== Installation Complete ==="
echo "✓ Daemon-pmac API is running"
echo "✓ Available at: http://$(hostname -I | awk '{print $1}')"
echo "✓ Documentation: http://$(hostname -I | awk '{print $1}')/docs"
echo "✓ Health check: http://$(hostname -I | awk '{print $1}')/health"
echo ""
echo "Admin credentials:"
echo "  Username: $ADMIN_USER"
echo "  Email: $ADMIN_EMAIL"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status daemon-pmac    # Check service status"
echo "  sudo systemctl restart daemon-pmac   # Restart service"
echo "  sudo journalctl -u daemon-pmac -f    # View logs"
echo "  daemon-backup                         # Create backup"
echo ""
echo "Configuration files:"
echo "  $PROJECT_DIR/.env                    # Environment settings"
echo "  /etc/nginx/sites-available/daemon-pmac # Nginx config"
echo "  /etc/systemd/system/daemon-pmac.service # Service config"
echo -e "${NC}"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update the .env file with your specific configuration"
echo "2. Configure SSL/HTTPS if needed"
echo "3. Set up firewall rules"
echo "4. Add your data using the API or web interface"
echo ""
echo -e "${GREEN}Happy API building! 🚀${NC}"
