#!/bin/bash

# SSL Certificate Generation Script for Daemon Frontend
# Creates self-signed certificates for development or prepares for production certificates

set -e

# Configuration
SSL_DIR="${SSL_DIR:-./ssl}"
DOMAIN="${DOMAIN:-localhost}"
CERT_DAYS="${CERT_DAYS:-365}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 SSL Certificate Setup for Daemon Frontend${NC}"
echo "================================================"

# Create SSL directory
mkdir -p "$SSL_DIR"

# Function to generate self-signed certificate
generate_self_signed() {
    echo -e "${YELLOW}📋 Generating self-signed certificate for development...${NC}"

    openssl req -x509 -nodes -days "$CERT_DAYS" -newkey rsa:2048 \
        -keyout "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" \
        -subj "/C=US/ST=State/L=City/O=Daemon/OU=Development/CN=$DOMAIN" \
        -addext "subjectAltName=DNS:$DOMAIN,DNS:localhost,IP:127.0.0.1"

    echo -e "${GREEN}✅ Self-signed certificate generated${NC}"
    echo "   Certificate: $SSL_DIR/cert.pem"
    echo "   Private Key: $SSL_DIR/key.pem"
    echo "   Valid for: $CERT_DAYS days"
    echo "   Domain: $DOMAIN"
}

# Function to setup Let's Encrypt (production)
setup_letsencrypt() {
    echo -e "${YELLOW}📋 Setting up Let's Encrypt certificate...${NC}"

    if ! command -v certbot &> /dev/null; then
        echo -e "${RED}❌ Certbot not found. Please install certbot first:${NC}"
        echo "   Ubuntu/Debian: sudo apt install certbot"
        echo "   CentOS/RHEL: sudo yum install certbot"
        echo "   macOS: brew install certbot"
        exit 1
    fi

    echo "🔄 Requesting certificate from Let's Encrypt..."
    sudo certbot certonly --standalone \
        --agree-tos \
        --no-eff-email \
        --email "admin@$DOMAIN" \
        -d "$DOMAIN"

    # Copy certificates to our SSL directory
    sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/cert.pem"
    sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/key.pem"
    sudo chown $(whoami):$(whoami) "$SSL_DIR"/*.pem

    echo -e "${GREEN}✅ Let's Encrypt certificate installed${NC}"
}

# Function to validate existing certificates
validate_certs() {
    if [[ -f "$SSL_DIR/cert.pem" && -f "$SSL_DIR/key.pem" ]]; then
        echo -e "${YELLOW}📋 Validating existing certificates...${NC}"

        # Check certificate validity
        if openssl x509 -in "$SSL_DIR/cert.pem" -noout -checkend 86400; then
            echo -e "${GREEN}✅ Certificate is valid for at least 24 hours${NC}"
        else
            echo -e "${RED}⚠️  Certificate expires within 24 hours${NC}"
        fi

        # Show certificate info
        echo "📊 Certificate Information:"
        openssl x509 -in "$SSL_DIR/cert.pem" -noout -subject -dates

        return 0
    else
        echo -e "${RED}❌ No certificates found in $SSL_DIR${NC}"
        return 1
    fi
}

# Main menu
echo "Choose an option:"
echo "1) Generate self-signed certificate (development)"
echo "2) Setup Let's Encrypt certificate (production)"
echo "3) Validate existing certificates"
echo "4) Exit"
echo

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        generate_self_signed
        ;;
    2)
        if [[ "$DOMAIN" == "localhost" ]]; then
            echo -e "${RED}❌ Cannot use Let's Encrypt with localhost${NC}"
            echo "Please set DOMAIN environment variable to your actual domain:"
            echo "   export DOMAIN=yourdomain.com"
            echo "   $0"
            exit 1
        fi
        setup_letsencrypt
        ;;
    3)
        validate_certs
        ;;
    4)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}🎉 SSL setup complete!${NC}"
echo
echo "Next steps:"
echo "1. Start the production Docker containers:"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo
echo "2. Access your application:"
echo "   HTTP:  http://$DOMAIN"
echo "   HTTPS: https://$DOMAIN"
echo
echo "3. For production, consider:"
echo "   - Setting up automatic certificate renewal"
echo "   - Configuring firewall rules"
echo "   - Setting up monitoring and logging"
