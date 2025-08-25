#!/bin/bash
# remote-setup.sh - Complete setup script for managing remote Daemon server

set -e  # Exit on any error

# Configuration
DAEMON_URL="${DAEMON_URL:-https://daemon.pmac.dev}"
ADMIN_USER="${ADMIN_USER:-pmac}"
ADMIN_PASS="${ADMIN_PASS}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }

# Check dependencies
check_dependencies() {
    for cmd in curl jq; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "$cmd is required but not installed"
            exit 1
        fi
    done
}

# Get authentication token
get_token() {
    if [[ -z "$ADMIN_PASS" ]]; then
        read -s -p "Enter admin password: " ADMIN_PASS
        echo
    fi
    
    log_info "Authenticating with $DAEMON_URL..."
    
    local response=$(curl -s -X POST "$DAEMON_URL/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$ADMIN_USER&password=$ADMIN_PASS")
    
    local token=$(echo "$response" | jq -r '.access_token')
    
    if [[ "$token" == "null" || -z "$token" ]]; then
        log_error "Authentication failed"
        echo "$response" | jq .
        exit 1
    fi
    
    log_success "Authentication successful"
    echo "$token"
}

# Check system status
check_system() {
    log_info "Checking system status..."
    
    local health=$(curl -s "$DAEMON_URL/health")
    local info=$(curl -s "$DAEMON_URL/api/v1/system/info")
    
    if echo "$health" | jq -e '.status == "healthy"' > /dev/null; then
        log_success "Server is healthy"
    else
        log_warning "Server health check failed"
        echo "$health" | jq .
    fi
    
    local mode=$(echo "$info" | jq -r '.mode')
    local users=$(echo "$info" | jq -r '.users[]? // empty' | wc -l)
    
    log_info "System mode: $mode"
    log_info "Total users: $users"
    
    if [[ "$mode" == "multi_user" ]]; then
        log_info "Available users:"
        echo "$info" | jq -r '.users[]?' | sed 's/^/  - /'
    fi
}

# Create a new user
create_user() {
    local username=$1
    local email=$2
    local password=${3:-"temp_password_$username"}
    local is_admin=${4:-false}
    
    log_info "Creating user: $username"
    
    local response=$(curl -s -X POST "$DAEMON_URL/api/v1/setup/user/$username" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"$username\",
            \"email\": \"$email\",
            \"password\": \"$password\",
            \"is_admin\": $is_admin
        }")
    
    if echo "$response" | jq -e '.success' > /dev/null; then
        log_success "User $username created successfully"
        
        local imported=$(echo "$response" | jq -r '.import_result.total_entries // 0')
        if [[ "$imported" -gt 0 ]]; then
            log_success "Imported $imported data entries for $username"
        fi
    else
        log_error "Failed to create user $username"
        echo "$response" | jq .
        return 1
    fi
}

# Import data for all users
import_all_data() {
    log_info "Importing data for all users..."
    
    local response=$(curl -s -X POST "$DAEMON_URL/api/v1/import/all" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$response" | jq -e '.success' > /dev/null; then
        local total_users=$(echo "$response" | jq -r '.total_users')
        local total_entries=$(echo "$response" | jq -r '.total_entries')
        
        log_success "Data import completed"
        log_success "Users processed: $total_users"
        log_success "Total entries imported: $total_entries"
        
        # Show per-user breakdown
        echo "$response" | jq -r '.users_processed[]? | "  - \(.username): \(.total_entries) entries"'
        
        # Show any errors
        local errors=$(echo "$response" | jq '.errors | length')
        if [[ "$errors" -gt 0 ]]; then
            log_warning "$errors errors occurred:"
            echo "$response" | jq -r '.errors[]? | "  - \(.username): \(.error)"'
        fi
    else
        log_error "Data import failed"
        echo "$response" | jq .
        return 1
    fi
}

# Import data for specific user
import_user_data() {
    local username=$1
    
    log_info "Importing data for user: $username"
    
    local response=$(curl -s -X POST "$DAEMON_URL/api/v1/import/user/$username" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$response" | jq -e '.success' > /dev/null; then
        local total_entries=$(echo "$response" | jq -r '.total_entries')
        log_success "Imported $total_entries entries for $username"
    else
        log_error "Failed to import data for $username"
        echo "$response" | jq .
        return 1
    fi
}

# List all users
list_users() {
    log_info "Listing all users..."
    
    local response=$(curl -s -X GET "$DAEMON_URL/auth/users" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$response" | jq -e 'type == "array"' > /dev/null; then
        echo "$response" | jq -r '.[] | "  - \(.username) (\(.email)) - Admin: \(.is_admin)"'
    else
        log_error "Failed to list users"
        echo "$response" | jq .
    fi
}

# Update user privacy settings
update_privacy() {
    local username=$1
    
    log_info "Updating privacy settings for $username..."
    
    # This would require the user's token, not admin token
    # For demo purposes, showing the structure
    cat << EOF
To update privacy settings for $username, they need to:

1. Login to get their token:
   curl -X POST "$DAEMON_URL/auth/login" \\
     -H "Content-Type: application/x-www-form-urlencoded" \\
     -d "username=$username&password=their_password"

2. Update their privacy settings:
   curl -X PUT "$DAEMON_URL/api/v1/privacy/settings" \\
     -H "Authorization: Bearer <user_token>" \\
     -H "Content-Type: application/json" \\
     -d '{
       "show_contact_info": true,
       "ai_assistant_access": true,
       "business_card_mode": false
     }'
EOF
}

# Main menu
show_menu() {
    echo
    echo "🚀 Remote Daemon Management"
    echo "============================"
    echo "1. Check system status"
    echo "2. List users"
    echo "3. Create new user"
    echo "4. Import all user data"
    echo "5. Import specific user data"
    echo "6. Update privacy settings (info)"
    echo "7. Exit"
    echo
}

# Interactive mode
interactive_mode() {
    while true; do
        show_menu
        read -p "Select an option (1-7): " choice
        
        case $choice in
            1)
                check_system
                ;;
            2)
                list_users
                ;;
            3)
                read -p "Username: " username
                read -p "Email: " email
                read -s -p "Password (or leave empty for temp): " password
                echo
                read -p "Make admin? (y/N): " is_admin
                
                if [[ -z "$password" ]]; then
                    password="temp_password_$username"
                fi
                
                if [[ "$is_admin" =~ ^[Yy]$ ]]; then
                    is_admin="true"
                else
                    is_admin="false"
                fi
                
                create_user "$username" "$email" "$password" "$is_admin"
                ;;
            4)
                import_all_data
                ;;
            5)
                read -p "Username: " username
                import_user_data "$username"
                ;;
            6)
                read -p "Username: " username
                update_privacy "$username"
                ;;
            7)
                log_info "Goodbye!"
                exit 0
                ;;
            *)
                log_error "Invalid option"
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# Batch mode for automation
batch_mode() {
    local action=$1
    shift
    
    case $action in
        "create-user")
            create_user "$@"
            ;;
        "import-all")
            import_all_data
            ;;
        "import-user")
            import_user_data "$1"
            ;;
        "list-users")
            list_users
            ;;
        "status")
            check_system
            ;;
        *)
            log_error "Unknown batch action: $action"
            echo "Available actions: create-user, import-all, import-user, list-users, status"
            exit 1
            ;;
    esac
}

# Main execution
main() {
    echo "🌍 Remote Daemon Server Management"
    echo "Server: $DAEMON_URL"
    echo "Admin User: $ADMIN_USER"
    echo
    
    check_dependencies
    TOKEN=$(get_token)
    
    if [[ $# -eq 0 ]]; then
        # Interactive mode
        check_system
        interactive_mode
    else
        # Batch mode
        batch_mode "$@"
    fi
}

# Usage information
usage() {
    cat << EOF
Remote Daemon Server Management Script

Usage:
  $0                              # Interactive mode
  $0 status                       # Check system status
  $0 list-users                   # List all users
  $0 create-user <user> <email>   # Create new user
  $0 import-all                   # Import all user data
  $0 import-user <username>       # Import specific user data

Environment Variables:
  DAEMON_URL     # Server URL (default: https://daemon.pmac.dev)
  ADMIN_USER     # Admin username (default: pmac)
  ADMIN_PASS     # Admin password (prompted if not set)

Examples:
  $0 create-user kime kime@example.com
  $0 import-all
  DAEMON_URL=https://my-server.com $0 status
EOF
}

# Handle help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
fi

# Run main function
main "$@"
