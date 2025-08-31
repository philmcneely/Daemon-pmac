# Migration Scripts

This directory contains database migration and management tools for the Daemon API.

## 🛠️ Available Scripts

### `version_tracker.py`
**Purpose**: Database version tracking and schema validation

**Usage**:
```bash
python scripts/version_tracker.py
```

**Features**:
- Shows current database version
- Validates schema integrity
- Displays migration history
- Initializes version tracking for new databases

### `migrate_comprehensive.py`
**Purpose**: Automated database migration with safety features

**Usage**:
```bash
# Check current status
python scripts/migrate_comprehensive.py --check-only

# Run migration to specific version
python scripts/migrate_comprehensive.py --target 0.3.1

# Force migration (skip version checks)
python scripts/migrate_comprehensive.py --target 0.3.1 --force
```

**Features**:
- Pre-migration safety checks
- Automatic backup creation
- Rollback capability on failure
- Schema validation
- Version-specific migration paths

### `migrate_database.py`
**Purpose**: Legacy migration script (v0.1.x → v0.2.x)

**Usage**:
```bash
python scripts/migrate_database.py
```

**Status**: Still functional, now integrated into comprehensive migration system

## 🔄 Migration Workflow

### For New Installations
1. Database is automatically initialized with current schema
2. Version tracking records baseline version

### For Upgrades
1. **Check Status**: `python scripts/migrate_comprehensive.py --check-only`
2. **Run Migration**: `python scripts/migrate_comprehensive.py --target X.Y.Z`
3. **Verify Success**: `python scripts/version_tracker.py`

### For Troubleshooting
- Check schema integrity: `python scripts/version_tracker.py`
- View migration history: Look for "Migration History" section
- Manual backup: Use app's backup system before migration

## 📋 Migration Matrix

| Migration Path | Script Used | Automatic Backup | Rollback Support |
|---------------|-------------|------------------|------------------|
| v0.1.x → v0.2.x | migrate_comprehensive.py | ✅ | ✅ |
| v0.2.x → v0.3.0 | migrate_comprehensive.py | ✅ | ✅ |
| v0.1.x → v0.3.0 | migrate_comprehensive.py | ✅ | ✅ |
| Any → Any | migrate_comprehensive.py | ✅ | ✅ |

## 🚨 Safety Features

### Automatic Backups
- Created before every migration
- Stored in `backups/` directory
- Named with timestamp for easy identification

### Pre-Migration Checks
- Database file existence
- Schema integrity validation
- Disk space verification (3x database size needed)
- Version compatibility verification

### Rollback Capability
- Automatic rollback on migration failure
- Manual restore instructions provided
- Backup path clearly documented

## 📖 Documentation

For complete migration procedures and troubleshooting, see:
- `docs/DATABASE_MIGRATIONS.md` - Comprehensive migration guide
- Docker upgrade procedures
- Bare metal upgrade procedures
- Version-specific notes and breaking changes
