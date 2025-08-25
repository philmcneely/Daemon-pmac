#!/bin/bash
# remote-deploy.sh - Deploy updates to remote Daemon server

set -e

# Configuration
DAEMON_HOST="${DAEMON_HOST:-daemon.pmac.dev}"
DAEMON_USER="${DAEMON_USER:-daemon}"
DAEMON_PATH="${DAEMON_PATH:-/opt/daemon-pmac}"
LOCAL_PATH="${LOCAL_PATH:-$(pwd)}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }

# Check if we can connect to the server
check_connection() {
    log_info "Checking connection to $DAEMON_HOST..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$DAEMON_USER@$DAEMON_HOST" "echo 'Connected'" &>/dev/null; then
        log_success "SSH connection successful"
    else
        log_error "Cannot connect to $DAEMON_HOST"
        log_error "Please check your SSH configuration and ensure you can connect:"
        echo "  ssh $DAEMON_USER@$DAEMON_HOST"
        exit 1
    fi
}

# Sync code to server
sync_code() {
    log_info "Syncing code to server..."
    
    # Exclude patterns
    local exclude_opts=(
        --exclude='.git'
        --exclude='__pycache__'
        --exclude='*.pyc'
        --exclude='.pytest_cache'
        --exclude='data/private'
        --exclude='backups'
        --exclude='logs'
        --exclude='.DS_Store'
        --exclude='*.log'
    )
    
    if rsync -avz --delete "${exclude_opts[@]}" \
        "$LOCAL_PATH/" "$DAEMON_USER@$DAEMON_HOST:$DAEMON_PATH/"; then
        log_success "Code sync completed"
    else
        log_error "Code sync failed"
        return 1
    fi
}

# Update dependencies
update_dependencies() {
    log_info "Updating dependencies on server..."
    
    ssh "$DAEMON_USER@$DAEMON_HOST" "
        cd $DAEMON_PATH &&
        source venv/bin/activate &&
        pip install -r requirements.txt
    "
    
    log_success "Dependencies updated"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    ssh "$DAEMON_USER@$DAEMON_HOST" "
        cd $DAEMON_PATH &&
        source venv/bin/activate &&
        python -c '
import sys
sys.path.append(\".\")
from app.database import init_db, engine
from sqlalchemy import text

# Create tables
init_db()

# Check if UserPrivacySettings table exists
with engine.connect() as conn:
    result = conn.execute(text(\"SELECT name FROM sqlite_master WHERE type=\"\"table\"\" AND name=\"\"user_privacy_settings\"\"\"))
    if not result.fetchone():
        print(\"Creating UserPrivacySettings table...\")
        conn.execute(text(\"\"\"
        CREATE TABLE user_privacy_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            privacy_level VARCHAR(20) DEFAULT \"\"public_full\"\",
            show_contact_info BOOLEAN DEFAULT TRUE,
            ai_assistant_access BOOLEAN DEFAULT TRUE,
            business_card_mode BOOLEAN DEFAULT FALSE,
            custom_filters TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users (id)
        )\"\"\"))
        conn.commit()
        print(\"UserPrivacySettings table created\")
    
    # Check if DataPrivacyRule table exists
    result = conn.execute(text(\"SELECT name FROM sqlite_master WHERE type=\"\"table\"\" AND name=\"\"data_privacy_rules\"\"\"))
    if not result.fetchone():
        print(\"Creating DataPrivacyRule table...\")
        conn.execute(text(\"\"\"
        CREATE TABLE data_privacy_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name VARCHAR(50) NOT NULL,
            pattern VARCHAR(200) NOT NULL,
            privacy_level VARCHAR(20) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )\"\"\"))
        conn.commit()
        print(\"DataPrivacyRule table created\")
        
        # Insert default privacy rules
        default_rules = [
            (\"phone\", \"\\\\b\\\\d{3}[-.]?\\\\d{3}[-.]?\\\\d{4}\\\\b\", \"business_card\"),
            (\"ssn\", \"\\\\b\\\\d{3}-\\\\d{2}-\\\\d{4}\\\\b\", \"ai_safe\"),
            (\"email\", \"\\\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Z|a-z]{2,}\\\\b\", \"professional\"),
            (\"salary\", \"\\\\$[0-9,]+(\\\\.[0-9]{2})?\", \"professional\"),
            (\"address\", \"\\\\d+\\\\s+[A-Za-z0-9\\\\s,.-]+\\\\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln)\", \"professional\")
        ]
        
        for rule in default_rules:
            conn.execute(text(\"\"\"
            INSERT INTO data_privacy_rules (field_name, pattern, privacy_level)
            VALUES (:field_name, :pattern, :privacy_level)
            \"\"\"), {\"field_name\": rule[0], \"pattern\": rule[1], \"privacy_level\": rule[2]})
        
        conn.commit()
        print(\"Default privacy rules inserted\")

print(\"Database migration completed successfully\")
'
    "
    
    log_success "Database migrations completed"
}

# Restart the service
restart_service() {
    log_info "Restarting daemon service..."
    
    ssh "$DAEMON_USER@$DAEMON_HOST" "
        sudo systemctl restart daemon-pmac
    "
    
    # Wait for service to start
    sleep 5
    
    # Check service status
    local status=$(ssh "$DAEMON_USER@$DAEMON_HOST" "sudo systemctl is-active daemon-pmac")
    
    if [[ "$status" == "active" ]]; then
        log_success "Service restarted successfully"
    else
        log_error "Service failed to start"
        ssh "$DAEMON_USER@$DAEMON_HOST" "sudo systemctl status daemon-pmac"
        return 1
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if server responds
    local url="https://$DAEMON_HOST/health"
    local response=$(curl -s "$url" || echo "failed")
    
    if echo "$response" | grep -q '"status":"healthy"'; then
        log_success "Server is responding correctly"
        
        # Check system info
        local info_url="https://$DAEMON_HOST/api/v1/system/info"
        local info=$(curl -s "$info_url" || echo "{}")
        
        local mode=$(echo "$info" | jq -r '.mode // "unknown"')
        local version=$(echo "$info" | jq -r '.version // "unknown"')
        
        log_info "System mode: $mode"
        log_info "Version: $version"
        
    else
        log_error "Server health check failed"
        echo "Response: $response"
        return 1
    fi
}

# Backup before deployment
backup_remote() {
    log_info "Creating backup on remote server..."
    
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    
    ssh "$DAEMON_USER@$DAEMON_HOST" "
        mkdir -p $DAEMON_PATH/backups &&
        cd $DAEMON_PATH &&
        tar -czf backups/$backup_name.tar.gz \
            --exclude='backups' \
            --exclude='venv' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='logs' \
            .
    "
    
    log_success "Backup created: $backup_name.tar.gz"
}

# Show logs
show_logs() {
    log_info "Showing recent logs..."
    
    ssh "$DAEMON_USER@$DAEMON_HOST" "
        sudo journalctl -u daemon-pmac -n 20 --no-pager
    "
}

# Quick status check
quick_status() {
    log_info "Checking remote status..."
    
    # Check SSH connection
    if ssh -o ConnectTimeout=5 -o BatchMode=yes "$DAEMON_USER@$DAEMON_HOST" "echo 'SSH OK'" &>/dev/null; then
        log_success "SSH connection: OK"
    else
        log_error "SSH connection: FAILED"
        return 1
    fi
    
    # Check service status
    local service_status=$(ssh "$DAEMON_USER@$DAEMON_HOST" "sudo systemctl is-active daemon-pmac 2>/dev/null || echo 'inactive'")
    if [[ "$service_status" == "active" ]]; then
        log_success "Service status: ACTIVE"
    else
        log_warning "Service status: $service_status"
    fi
    
    # Check HTTP response
    local http_status=$(curl -s -o /dev/null -w "%{http_code}" "https://$DAEMON_HOST/health" || echo "000")
    if [[ "$http_status" == "200" ]]; then
        log_success "HTTP status: OK (200)"
    else
        log_warning "HTTP status: $http_status"
    fi
}

# Full deployment
full_deploy() {
    log_info "Starting full deployment to $DAEMON_HOST..."
    
    check_connection
    backup_remote
    sync_code
    update_dependencies
    run_migrations
    restart_service
    verify_deployment
    
    log_success "🎉 Deployment completed successfully!"
    log_info "Server: https://$DAEMON_HOST"
}

# Code-only deployment (no service restart)
code_deploy() {
    log_info "Starting code-only deployment..."
    
    check_connection
    sync_code
    
    log_success "Code sync completed!"
    log_warning "Remember to restart the service manually if needed"
}

# Show usage
usage() {
    cat << EOF
Remote Deployment Script for Daemon Server

Usage:
  $0 [command]

Commands:
  deploy          # Full deployment (default)
  code            # Code sync only
  status          # Quick status check
  logs            # Show recent logs
  backup          # Create backup only
  migrate         # Run migrations only
  restart         # Restart service only
  verify          # Verify deployment only

Environment Variables:
  DAEMON_HOST     # Remote server hostname (default: daemon.pmac.dev)
  DAEMON_USER     # SSH username (default: daemon)
  DAEMON_PATH     # Remote installation path (default: /opt/daemon-pmac)
  LOCAL_PATH      # Local project path (default: current directory)

Examples:
  $0                                    # Full deployment
  $0 status                            # Check status
  $0 code                              # Code sync only
  DAEMON_HOST=my-server.com $0 deploy  # Deploy to different server

Prerequisites:
  - SSH key-based authentication configured
  - rsync installed locally
  - curl and jq installed locally
  - Remote server has sudo access for systemctl commands
EOF
}

# Main execution
main() {
    local command=${1:-deploy}
    
    case $command in
        deploy|full)
            full_deploy
            ;;
        code)
            code_deploy
            ;;
        status)
            quick_status
            ;;
        logs)
            show_logs
            ;;
        backup)
            check_connection
            backup_remote
            ;;
        migrate)
            check_connection
            run_migrations
            ;;
        restart)
            check_connection
            restart_service
            ;;
        verify)
            verify_deployment
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            log_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# Check for help flag first
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
fi

# Make scripts directory if it doesn't exist
mkdir -p "$(dirname "$0")"

# Run main function
main "$@"
