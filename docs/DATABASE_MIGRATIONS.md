# Database Migration & Upgrade Guide

## 🚨 Critical Migration Information

**This guide is MANDATORY reading before upgrading between versions.**

## 📋 Version Migration Matrix

| From Version | To Version | Migration Required | Breaking Changes | Data Loss Risk |
|--------------|------------|-------------------|------------------|----------------|
| v0.2.x       | v0.3.0     | ✅ Required       | ❌ None          | 🟢 None       |
| v0.1.x       | v0.2.x     | ✅ Required       | ⚠️  Minor        | 🟢 None       |
| v0.1.x       | v0.3.0     | ✅ Required       | ⚠️  Minor        | 🟢 None       |

## � Migration Tools

### Version Tracker (`scripts/version_tracker.py`)
- **Purpose**: Track database schema versions and migration history
- **Usage**: `python scripts/version_tracker.py`
- **Features**: Version checking, schema integrity validation, migration history

### Comprehensive Migration (`scripts/migrate_comprehensive.py`)
- **Purpose**: Automated migration with safety checks and rollback
- **Usage**: `python scripts/migrate_comprehensive.py [--target VERSION] [--force] [--check-only]`
- **Features**: Pre-migration checks, automatic backups, rollback capability

### Legacy Migration (`scripts/migrate_database.py`)
- **Purpose**: Original v0.1.x → v0.2.x migration script
- **Usage**: `python scripts/migrate_database.py`
- **Status**: Still functional, integrated into comprehensive system

## 📊 Quick Status Check

```bash
# Check current version and status
python scripts/migrate_comprehensive.py --check-only

# View detailed version history
python scripts/version_tracker.py
```

## �🔄 Migration Types

### Automatic Migrations
- **Schema updates**: New tables, columns, indexes
- **Default data**: Privacy rules, endpoint definitions
- **Data format changes**: Content structure updates

### Manual Migrations
- **Configuration changes**: Environment variables
- **File system changes**: Directory structure
- **Service changes**: Docker compose updates

## 🐳 Docker Container Upgrades

### Container-to-Container Migration

**For Docker deployments upgrading from any version:**

#### 1. Check Current Version and Create Backup

```bash
# Check current database version
docker compose exec api python scripts/migrate_comprehensive.py --check-only

# Create backup before upgrade
docker compose exec api python -m app.cli backup create
```

#### 2. Stop Current Services

```bash
# Stop containers but preserve volumes
docker compose down
```

#### 3. Update Code and Images

```bash
# Pull latest code
git pull origin main
git checkout v0.3.0  # or desired version

# Rebuild images with new version
docker compose build --no-cache
```

#### 4. Run Database Migrations

```bash
# Start only the API container for migration
docker compose up -d api

# Run comprehensive migration (automatically detects and runs needed migrations)
docker compose exec api python scripts/migrate_comprehensive.py --target 0.3.0

# Alternative: Check what migration would do first
docker compose exec api python scripts/migrate_comprehensive.py --check-only

# Verify migration completed successfully
docker compose exec api python scripts/version_tracker.py
```

#### 5. Start All Services

```bash
# Start all services
docker compose up -d

# Verify health
curl http://localhost:8004/health
```

### Database Volume Persistence

Your database is stored in Docker volumes and **automatically preserved** during upgrades:

```yaml
# docker-compose.yml volumes section
volumes:
  - ./data:/app/data        # Database files persist here
  - ./backups:/app/backups  # Backup files persist here
```

**Key Points:**
- Database file: `./data/daemon.db` (preserved)
- Backups: `./backups/` (preserved)
- Logs: `./logs/` (preserved)

## 🖥️ Bare Metal Upgrades

### Upgrading Existing Installation

#### 1. Pre-Upgrade Backup

```bash
# Stop the service
sudo systemctl stop daemon

# Create backup
cd /opt/daemon
python -m app.cli backup create

# Export user data (additional safety)
python -m app.cli export-user-data $(whoami) --output-dir ./backups/
```

#### 2. Update Code

```bash
# Pull latest code
git pull origin main
git checkout v0.3.0  # or desired version

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Run Migrations

```bash
# Check current version and what migration is needed
python scripts/migrate_comprehensive.py --check-only

# Run comprehensive migration
python scripts/migrate_comprehensive.py --target 0.3.0

# Verify migration completed successfully
python scripts/version_tracker.py
```
with engine.connect() as conn:
    # Check tables exist
    tables = conn.execute(text(\"SELECT name FROM sqlite_master WHERE type='table'\")).fetchall()
    print(f'📊 Tables: {[t[0] for t in tables]}')

    # Check user count
    user_count = conn.execute(text('SELECT COUNT(*) FROM users')).scalar()
    print(f'👤 Users: {user_count}')

    # Check privacy rules
    rule_count = conn.execute(text('SELECT COUNT(*) FROM data_privacy_rules')).scalar()
    print(f'🔒 Privacy Rules: {rule_count}')
print('✅ Database verification complete')
"
```

#### 4. Restart Service

```bash
# Start the service
sudo systemctl start daemon

# Check status
sudo systemctl status daemon

# Verify API health
curl http://localhost:8004/health
```

## 📝 Version-Specific Migration Notes

### v0.1.x → v0.2.x

**New Features:**
- Multi-user support
- Privacy settings system
- Enhanced authentication

**Database Changes:**
- Added `UserPrivacySettings` table
- Added `DataPrivacyRule` table
- Added `full_name` column to `users` table

**Migration Script:** `scripts/migrate_database.py`

**Breaking Changes:**
- Environment variable changes (see [Configuration Changes](#configuration-changes))

### v0.2.x → v0.3.0

**New Features:**
- Docker naming cleanup
- Improved container orchestration
- Enhanced CI/CD pipeline

**Database Changes:**
- No schema changes (compatible)

**Breaking Changes:**
- Container names changed from `daemon-pmac-*` to `daemon-*`
- CLI command changed from `daemon-pmac` to `daemon`

**Migration Script:** Not required for database (compatible)

### v0.1.x → v0.3.0 (Direct Upgrade)

**Database Changes:**
- All changes from v0.1.x → v0.2.x apply
- Plus v0.2.x → v0.3.0 changes

**Migration Script:** `scripts/migrate_database.py` (covers all changes)

## ⚙️ Configuration Changes

### Environment Variables

#### v0.2.x Changes
```bash
# NEW: Privacy settings
PRIVACY_LEVEL=public_full
BACKUP_ENABLED=true

# UPDATED: Database path (if using custom location)
DATABASE_URL=sqlite:///./data/daemon.db
```

#### v0.3.0 Changes
```bash
# CHANGED: CLI command name
# Old: daemon-pmac --help
# New: daemon --help

# Container names updated automatically in docker-compose.yml
```

### Service Files

#### v0.3.0 Updates
```bash
# Update service file paths
sudo sed -i 's|/opt/daemon-pmac|/opt/daemon|g' /etc/systemd/system/daemon.service
sudo systemctl daemon-reload
```

## 🧪 Testing Migration

### Pre-Migration Tests

```bash
# Test current version works
curl http://localhost:8004/health
curl http://localhost:8004/api/v1/system/info

# Create test data
curl -X POST http://localhost:8004/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"content": "# Test Idea\nThis is a test before migration"}'
```

### Post-Migration Tests

```bash
# Test health after migration
curl http://localhost:8004/health

# Test data integrity
curl http://localhost:8004/api/v1/ideas

# Test new features (privacy system)
curl http://localhost:8004/api/v1/system/info
```

## 🚨 Rollback Procedures

### Docker Rollback

```bash
# Stop current version
docker compose down

# Restore from backup
docker compose exec api python -m app.cli backup restore backup_YYYYMMDD_HHMMSS.db

# Roll back to previous version
git checkout v0.2.2  # or previous version
docker compose build --no-cache
docker compose up -d
```

### Bare Metal Rollback

```bash
# Stop service
sudo systemctl stop daemon

# Restore database
python -m app.cli backup restore backup_YYYYMMDD_HHMMSS.db

# Roll back code
git checkout v0.2.2  # or previous version
pip install -r requirements.txt

# Start service
sudo systemctl start daemon
```

## 📊 Migration Verification

### Database Schema Check

```bash
# Check all tables exist
sqlite3 data/daemon.db ".tables"

# Expected tables:
# - users
# - endpoints
# - data_entries
# - api_keys
# - audit_logs
# - user_privacy_settings  (v0.2.x+)
# - data_privacy_rules     (v0.2.x+)
```

### Data Integrity Check

```bash
# Run integrity verification
python -c "
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check foreign key constraints
    conn.execute(text('PRAGMA foreign_key_check'))

    # Check data counts
    print('Data Integrity Check:')
    for table in ['users', 'endpoints', 'data_entries']:
        count = conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
        print(f'  {table}: {count} records')

    print('✅ All checks passed')
"
```

## 🔒 Security Considerations

### Privacy Rule Updates

**v0.2.x+ includes automatic privacy scanning:**

```bash
# Check privacy rules are active
python -c "
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    rules = conn.execute(text('SELECT field_name, privacy_level FROM data_privacy_rules WHERE is_active = 1')).fetchall()
    print(f'Active Privacy Rules: {len(rules)}')
    for rule in rules:
        print(f'  {rule[0]}: {rule[1]}')
"
```

### User Permission Verification

```bash
# Verify admin users
python -c "
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    admins = conn.execute(text('SELECT username FROM users WHERE is_admin = 1')).fetchall()
    print(f'Admin Users: {[admin[0] for admin in admins]}')
"
```

## 📈 Performance After Migration

### Index Verification

```bash
# Check database indexes
sqlite3 data/daemon.db ".indexes"

# Verify query performance
python -c "
from app.database import engine
from sqlalchemy import text
import time

with engine.connect() as conn:
    start = time.time()
    conn.execute(text('SELECT COUNT(*) FROM data_entries')).scalar()
    duration = time.time() - start
    print(f'Query performance: {duration:.3f}s')
"
```

## 🆘 Troubleshooting

### Common Migration Issues

#### "Table already exists" Error
```bash
# Check if migration was partially run
python -c "
from sqlalchemy import inspect
from app.database import engine

inspector = inspect(engine)
tables = inspector.get_table_names()
print('Existing tables:', tables)

# If user_privacy_settings exists, migration was run
if 'user_privacy_settings' in tables:
    print('✅ Migration already completed')
else:
    print('❌ Migration needed')
"
```

#### Foreign Key Constraint Errors
```bash
# Check and fix foreign key issues
sqlite3 data/daemon.db "PRAGMA foreign_key_check;"
```

#### Permission Errors (Bare Metal)
```bash
# Fix file permissions
sudo chown -R daemon:daemon /opt/daemon
sudo chmod -R 755 /opt/daemon
```

### Recovery from Failed Migration

```bash
# If migration fails, restore from backup
python -m app.cli backup restore backup_YYYYMMDD_HHMMSS.db

# Then retry migration with verbose output
python scripts/migrate_database.py
```

## 📞 Support

If you encounter issues during migration:

1. **Check logs**: `tail -f logs/server.log`
2. **Verify backups**: Ensure you have working backups before starting
3. **Test rollback**: Verify rollback procedure works before migration
4. **Document issues**: Note any errors for future reference

## 🔄 Future Migration Planning

### Best Practices

1. **Always backup before migrating**
2. **Test migrations in development first**
3. **Plan maintenance windows** for production
4. **Verify rollback procedures** work
5. **Document any custom changes** you've made

### Automated Migration (Future)

Future versions will include:
- Automatic schema version detection
- Progressive migration paths
- Built-in rollback capabilities
- Migration status tracking
