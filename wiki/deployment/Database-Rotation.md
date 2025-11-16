# Database Rotation Guide

Free Render PostgreSQL databases **expire after 90 days**. This guide explains the rotation process.

## Why Rotation is Needed

Render's free tier databases have a hard **90-day expiration** from creation date. After 90 days, the database is automatically deleted. To maintain your data, you must:

1. Backup the old database
2. Create a new database
3. Restore the backup
4. Update your application
5. Delete the old database

## Rotation Timeline

| Day | Action | Time Required |
|-----|--------|---------------|
| **Day 1** | Database created | - |
| **Day 85** | Create final backup | 5 minutes |
| **Day 86** | Create new database | 5 minutes |
| **Day 87** | Restore backup | 10 minutes |
| **Day 88** | Test new database | 15 minutes |
| **Day 89** | Update production | 10 minutes |
| **Day 90** | Delete old database | 2 minutes |

**Total time: ~1 hour** spread over 6 days

## Detailed Steps

### Day 85: Create Final Backup

**Via GitHub Actions (Recommended):**

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **Database Backup** workflow
4. Click **Run workflow** → **Run workflow**
5. Wait for green checkmark (1-2 minutes)
6. Go to **Releases** tab to verify backup created

**Via Local Script:**

```bash
export DATABASE_URL="your_current_database_url"
./scripts/backup_database.sh
```

**Verify:**
```bash
ls -lh backups/
# Should see: backstock_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Day 86: Create New Database

1. Log into [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `backstock-db-v2` (or use date)
   - **Database**: `backstock`
   - **User**: `backstock`
   - **Region**: Same as current
   - **Plan**: **Free**
4. Click **Create Database**
5. Wait 2-3 minutes for provisioning
6. Copy **Internal Database URL** (starts with `postgresql://`)
7. Save this URL for next step

### Day 87: Restore Backup

1. Download backup from GitHub Releases (if using GitHub Actions)
2. Set new database URL:
   ```bash
   export DATABASE_URL="postgresql://new_database_url_from_day_86"
   ```
3. Restore:
   ```bash
   ./scripts/restore_database.sh backups/backstock_backup_YYYYMMDD_HHMMSS.sql.gz
   ```
4. Type `yes` to confirm
5. Verify:
   ```bash
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM grocery_items;"
   ```

### Day 88: Test New Database

**Local Testing:**

1. Update `.env` file:
   ```bash
   DATABASE_URL=postgresql://new_database_url
   ```
2. Start application:
   ```bash
   python manage.py runserver
   ```
3. Test features:
   - Search items
   - Add new item
   - Upload CSV
4. Verify data matches production

### Day 89: Update Production

1. Go to Render Dashboard → `backstock` service
2. Click **Environment** tab
3. Find `DATABASE_URL`
4. Click **Edit** → Paste new database URL
5. Click **Save Changes**
6. Render automatically redeploys (5-10 minutes)
7. Verify application is accessible
8. Test critical features

**Update GitHub Secret:**

1. GitHub → Settings → Secrets → Actions
2. Edit `RENDER_DATABASE_URL`
3. Update with new database URL
4. Click **Update secret**

### Day 90: Delete Old Database

**⚠️ ONLY after confirming new database works!**

1. Verify application is running correctly
2. Check data is present
3. Go to Render Dashboard
4. Select old database (e.g., `backstock-db`)
5. **Settings** tab → Scroll to **Danger Zone**
6. Click **Delete Database**
7. Type database name to confirm
8. Click **Delete**

## Post-Rotation

**Update Records:**
- Note new database creation date
- Calculate next expiration: Creation Date + 90 days
- Set calendar reminder for Day 85

**Document New Database:**
```
Created: YYYY-MM-DD
Expires: YYYY-MM-DD
Name: backstock-db-v2
```

## Automation

Weekly backups run automatically every Monday at 2 AM UTC via GitHub Actions. These backups are stored in GitHub Releases for 90 days.

**Manual Backup Anytime:**
- GitHub → Actions → Database Backup → Run workflow

## Emergency Recovery

**Database expired before rotation?**

1. Check GitHub Releases for latest backup
2. Create new database on Render
3. Restore from backup (Day 87 steps)
4. Update DATABASE_URL (Day 89 steps)

**No backup available?**

If you have no backups, you'll need to:
1. Create new database
2. Re-import data from original source
3. Set up automated backups immediately

## Best Practices

- ✅ **Set calendar reminders** for Day 85
- ✅ **Download backups locally** as extra safety
- ✅ **Test restore process** before rotation
- ✅ **Keep multiple backup copies** (GitHub + local)
- ✅ **Document database creation dates**
- ❌ **Don't wait until Day 90** to start rotation
- ❌ **Don't skip testing phase** (Day 88)

## Quick Reference

See [Quick Reference](Quick-Reference.md) for checklist format and common commands.
