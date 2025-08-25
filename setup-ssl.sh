#!/bin/bash

# Generate SSL certificate for Daemon
# This script creates a self-signed certificate or sets up Let's Encrypt

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DOMAIN=""
EMAIL=""
SSL_DIR="/opt/daemon-pmac/ssl"
LETSENCRYPT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        --letsencrypt)
            LETSENCRYPT=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -d, --domain DOMAIN    Domain name for certificate"
            echo "  -e, --email EMAIL      Email for Let's Encrypt"
            echo "  --letsencrypt          Use Let's Encrypt (default: self-signed)"
            echo "  -h, --help             Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== SSL Certificate Setup ===${NC}"

# Create SSL directory
sudo mkdir -p $SSL_DIR
sudo chown daemon:daemon $SSL_DIR

if [ "$LETSENCRYPT" = true ]; then
    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        echo -e "${RED}Error: Domain and email are required for Let's Encrypt${NC}"
        echo "Usage: $0 --letsencrypt -d yourdomain.com -e your@email.com"
        exit 1
    fi
    
    echo -e "${YELLOW}Setting up Let's Encrypt certificate for $DOMAIN${NC}"
    
    # Install certbot
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
    
    # Stop nginx temporarily
    sudo systemctl stop nginx
    
    # Get certificate
    sudo certbot certonly --standalone \
        --email $EMAIL \
        --agree-tos \
        --non-interactive \
        -d $DOMAIN
    
    # Copy certificates to our SSL directory
    sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $SSL_DIR/cert.pem
    sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $SSL_DIR/key.pem
    sudo chown daemon:daemon $SSL_DIR/*.pem
    sudo chmod 600 $SSL_DIR/key.pem
    sudo chmod 644 $SSL_DIR/cert.pem
    
    # Update nginx configuration
    sudo tee /etc/nginx/sites-available/daemon-pmac > /dev/null <<EOF
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate $SSL_DIR/cert.pem;
    ssl_certificate_key $SSL_DIR/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
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
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

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

    # Set up auto-renewal
    echo -e "${YELLOW}Setting up certificate auto-renewal...${NC}"
    sudo tee /etc/cron.d/certbot-renew > /dev/null <<EOF
# Renew Let's Encrypt certificates twice daily
0 */12 * * * root certbot renew --quiet --deploy-hook "systemctl reload nginx"
EOF

    echo -e "${GREEN}✓ Let's Encrypt certificate installed${NC}"

else
    # Self-signed certificate
    if [ -z "$DOMAIN" ]; then
        DOMAIN="localhost"
    fi
    
    echo -e "${YELLOW}Creating self-signed certificate for $DOMAIN${NC}"
    
    # Generate self-signed certificate
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout $SSL_DIR/key.pem \
        -out $SSL_DIR/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
    
    sudo chown daemon:daemon $SSL_DIR/*.pem
    sudo chmod 600 $SSL_DIR/key.pem
    sudo chmod 644 $SSL_DIR/cert.pem
    
    # Update nginx configuration for self-signed
    sudo tee /etc/nginx/sites-available/daemon-pmac > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate $SSL_DIR/cert.pem;
    ssl_certificate_key $SSL_DIR/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

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
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

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

    echo -e "${GREEN}✓ Self-signed certificate created${NC}"
    echo -e "${YELLOW}Warning: Browsers will show security warnings for self-signed certificates${NC}"
fi

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

echo -e "${GREEN}"
echo "=== SSL Setup Complete ==="
echo "✓ SSL certificate installed"
echo "✓ Nginx configured for HTTPS"
if [ "$LETSENCRYPT" = true ]; then
    echo "✓ Auto-renewal configured"
    echo "✓ HTTPS available at: https://$DOMAIN"
else
    echo "✓ HTTPS available at: https://$(hostname -I | awk '{print $1}')"
fi
echo -e "${NC}"
