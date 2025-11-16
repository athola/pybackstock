# Backup and Restore

Database backup and restoration procedures for Backstock.

## Automated Backups

### GitHub Actions Workflow

Backups run automatically every **Monday at 2 AM UTC**.

**Features:**
- Creates compressed PostgreSQL dump (`.sql.gz`)
- Uploads to GitHub Releases
- 90-day retention period
- Email notification on failure

**View Backups:**
1. Go to repository **Releases** tab
2. Look for releases tagged `backup-*`
3. Download `.sql.gz` file

### Manual Trigger

1. Go to **Actions** tab
2. Select **Database Backup** workflow
3. Click **Run workflow**
4. (Optional) Add reason for backup
5. Click **Run workflow** button
6. Wait for completion (1-2 minutes)

## Manual Backup

### Using Backup Script

```bash
# Set database URL
export DATABASE_URL="postgresql://user:pass@host:port/dbname"

# Run backup
./scripts/backup_database.sh

# Optional: Specify output directory
./scripts/backup_database.sh ./my-backups
```

**Output:**
```
Starting database backup...
Backup file: backups/backstock_backup_20250116_143022.sql
✓ Backup completed successfully!
  File: backups/backstock_backup_20250116_143022.sql
  Size: 2.4M
✓ Compressed to backstock_backup_20250116_143022.sql.gz (512K)
✓ Cleanup complete
```

### Using pg_dump Directly

```bash
# Get DATABASE_URL from Render dashboard
export DATABASE_URL="postgresql://..."

# Create backup
pg_dump $DATABASE_URL > backup.sql

# Compress
gzip backup.sql
```

## Restore Database

### Using Restore Script

```bash
# Set NEW database URL
export DATABASE_URL="postgresql://new_database_url"

# Restore from backup
./scripts/restore_database.sh backups/backstock_backup_20250116_143022.sql.gz

# Confirm when prompted
Are you sure you want to continue? (yes/no): yes
```

**Output:**
```
Database Restore Process
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backup file: backups/backstock_backup_20250116_143022.sql.gz
Target database: postgresql://...

⚠ WARNING: This will OVERWRITE the target database!
Are you sure you want to continue? (yes/no): yes

Decompressing backup file...
Starting database restore...
✓ Database restore completed successfully!

Restore process complete!

Next steps:
  1. Verify data with: psql $DATABASE_URL -c 'SELECT COUNT(*) FROM grocery_items;'
  2. Run migrations if needed: python manage.py db upgrade
```

### Using psql Directly

```bash
# Decompress if needed
gunzip -c backup.sql.gz > backup.sql

# Restore
psql $DATABASE_URL < backup.sql

# Clean up
rm backup.sql
```

## Verification

### Check Restore Success

```bash
# Count items
psql $DATABASE_URL -c "SELECT COUNT(*) FROM grocery_items;"

# Check tables exist
psql $DATABASE_URL -c "\dt"

# View recent items
psql $DATABASE_URL -c "SELECT * FROM grocery_items LIMIT 5;"
```

### Run Migrations

After restoring, apply any pending migrations:

```bash
python manage.py db upgrade
```

## Backup Storage

### GitHub Releases

- **Automatic**: Weekly backups stored for 90 days
- **Manual**: Triggered backups also stored in releases
- **Download**: Go to Releases tab → Select backup → Download `.sql.gz`

### Local Storage

Backups created locally are stored in:
```
backups/
├── backstock_backup_20250116_143022.sql.gz
├── backstock_backup_20250123_143015.sql.gz
└── backstock_backup_20250130_143008.sql.gz
```

**Cleanup**: Scripts automatically keep last 5 backups

### Recommended Practice

**Multiple Locations:**
1. ✅ GitHub Releases (automatic)
2. ✅ Local machine (download weekly)
3. ✅ Cloud storage (optional: Google Drive, Dropbox)

## Backup Schedule

| Backup Type | Frequency | Retention | Location |
|-------------|-----------|-----------|----------|
| Automated | Weekly (Mon 2AM UTC) | 90 days | GitHub Releases |
| Pre-rotation | Day 85 | Permanent | GitHub + Local |
| Manual | As needed | 90 days | GitHub Releases |
| Local | As needed | Last 5 | `backups/` directory |

## Best Practices

### Before Major Changes

Always backup before:
- Database schema migrations
- Bulk data imports
- Application updates
- Database rotation (Day 85)

### Testing Restores

Periodically test restore process:

1. Create test database on Render
2. Restore latest backup
3. Verify data integrity
4. Delete test database

### Backup Verification

After creating backup:

```bash
# Check file size (should not be 0)
ls -lh backups/*.sql.gz

# Test compressed file integrity
gzip -t backups/backstock_backup_*.sql.gz

# View backup metadata
file backups/backstock_backup_*.sql.gz
```

## Troubleshooting

### Backup Issues

**pg_dump not found:**
```bash
# Install PostgreSQL client
# Ubuntu/Debian:
sudo apt-get install postgresql-client

# macOS:
brew install postgresql
```

**Permission denied:**
- Verify DATABASE_URL is correct
- Ensure database user has SELECT permissions

**Backup file too large:**
- Free tier: 1GB database limit
- Compressed backups are ~10-20% of original size
- Consider data cleanup if approaching limit

### Restore Issues

**Database not empty:**
- Restore overwrites existing data
- To start fresh: Drop all tables first
- Or create new database

**Permission errors:**
- Use database owner credentials
- For Render: Use provided Internal Database URL

**Timeout errors:**
- Large databases may take longer
- Increase timeout or restore in sections

## Scripts Reference

### backup_database.sh

**Location:** `scripts/backup_database.sh`

**Usage:**
```bash
./scripts/backup_database.sh [output_directory]
```

**Features:**
- Creates timestamped SQL dump
- Automatic compression
- Cleanup of old backups
- Color-coded output

### restore_database.sh

**Location:** `scripts/restore_database.sh`

**Usage:**
```bash
./scripts/restore_database.sh <backup_file>
```

**Features:**
- Safety confirmation prompt
- Handles compressed files
- Verification steps
- Next-steps guidance

### automated_backup.py

**Location:** `scripts/automated_backup.py`

**Usage:** (Used by GitHub Actions)
```bash
python scripts/automated_backup.py
```

**Features:**
- CI/CD optimized
- GitHub Actions integration
- Progress indicators
- Error handling

## Security

### Connection Strings

**Never commit:**
- DATABASE_URL values
- PostgreSQL passwords
- Connection strings

**Store securely:**
- GitHub Secrets (for workflows)
- `.env` file (gitignored)
- Environment variables

### Backup Files

Backup files may contain sensitive data:

- ✅ Stored in `.gitignore` (`backups/`, `*.sql`, `*.sql.gz`)
- ✅ GitHub Releases (private repos only)
- ❌ Never commit to repository
- ❌ Be careful with public sharing

## Quick Commands

```bash
# Create backup
export DATABASE_URL="postgresql://..."
./scripts/backup_database.sh

# Restore backup
export DATABASE_URL="postgresql://..."
./scripts/restore_database.sh backups/backup_file.sql.gz

# Verify database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM grocery_items;"

# List backups
ls -lh backups/

# Download from GitHub Release
# Go to: https://github.com/YOUR_USERNAME/backstock/releases
```
