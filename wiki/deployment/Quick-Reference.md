# Quick Reference

Checklists and common commands for Backstock deployment.

## 90-Day Rotation Checklist

### Day 85: Backup
- [ ] Go to GitHub → Actions → Database Backup
- [ ] Click "Run workflow"
- [ ] Verify backup in Releases tab
- [ ] Download backup locally as safety copy

### Day 86: New Database
- [ ] Log into [Render Dashboard](https://dashboard.render.com)
- [ ] New + → PostgreSQL
- [ ] Name: `backstock-db-v2` (or date)
- [ ] Plan: Free
- [ ] Copy Internal Database URL

### Day 87: Restore
- [ ] `export DATABASE_URL="new_url"`
- [ ] `./scripts/restore_database.sh backups/latest.sql.gz`
- [ ] Verify: `psql $DATABASE_URL -c "SELECT COUNT(*) FROM grocery_items;"`

### Day 88: Test
- [ ] Update local `.env` with new DATABASE_URL
- [ ] `python manage.py runserver`
- [ ] Test: Search, Add Item, Upload CSV
- [ ] Confirm data matches production

### Day 89: Deploy
- [ ] Render → backstock service → Environment
- [ ] Edit DATABASE_URL → Paste new URL
- [ ] Save (auto-redeploys)
- [ ] GitHub → Settings → Secrets → Update `RENDER_DATABASE_URL`
- [ ] Test production app

### Day 90: Cleanup
- [ ] Verify app works correctly
- [ ] Render → old database → Settings → Delete
- [ ] Set reminder for next rotation (+90 days)

## Common Commands

### Deployment

```bash
# Push to deploy
git push origin main

# Manual deploy
# Dashboard → Service → Manual Deploy

# View logs
# Dashboard → Service → Logs

# Check deployment status
# Dashboard → Service → Events
```

### Database

```bash
# Connect to database
export DATABASE_URL="postgresql://..."
psql $DATABASE_URL

# Check database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('backstock'));"

# Count items
psql $DATABASE_URL -c "SELECT COUNT(*) FROM grocery_items;"

# List tables
psql $DATABASE_URL -c "\dt"

# Run migrations
python manage.py db upgrade
```

### Backup & Restore

```bash
# Create backup
export DATABASE_URL="postgresql://..."
./scripts/backup_database.sh

# Restore backup
export DATABASE_URL="postgresql://..."
./scripts/restore_database.sh backups/backup_file.sql.gz

# Manual pg_dump
pg_dump $DATABASE_URL > backup.sql
gzip backup.sql

# Manual restore
gunzip -c backup.sql.gz | psql $DATABASE_URL
```

### Testing

```bash
# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest tests/test_app.py -v

# Check linting
uv run ruff check .

# Check types
uv run mypy src/

# Run demo
make demo
```

### Local Development

```bash
# Install dependencies
uv sync --all-extras

# Run local server
python manage.py runserver

# Run with gunicorn
gunicorn 'src.backstock.app:app'

# Set environment
export APP_SETTINGS=config.DevelopmentConfig
export DATABASE_URL="postgresql://localhost/backstock_dev"
```

## Important URLs

### Render
- **Dashboard**: https://dashboard.render.com
- **Your App**: https://backstock.onrender.com
- **Documentation**: https://render.com/docs

### GitHub
- **Repository**: https://github.com/YOUR_USERNAME/backstock
- **Actions**: /actions
- **Releases** (backups): /releases
- **Secrets**: /settings/secrets/actions

## Environment Variables

| Variable | Value | Where |
|----------|-------|-------|
| `APP_SETTINGS` | `config.ProductionConfig` | Render Service |
| `SECRET_KEY` | Auto-generated | Render Service |
| `DATABASE_URL` | From database | Render Service |
| `RENDER_DATABASE_URL` | From database | GitHub Secrets |

## File Locations

| File | Purpose |
|------|---------|
| `render.yaml` | Render configuration |
| `Procfile` | Process commands |
| `runtime.txt` | Python version |
| `.github/workflows/deploy.yml` | Deploy workflow |
| `.github/workflows/database-backup.yml` | Backup workflow |
| `scripts/backup_database.sh` | Backup script |
| `scripts/restore_database.sh` | Restore script |

## Database Rotation Calculator

```
Creation Date: __________
Expiration Date: Creation Date + 90 days = __________

Day 85: __________ (Create backup)
Day 86: __________ (New database)
Day 87: __________ (Restore)
Day 88: __________ (Test)
Day 89: __________ (Deploy)
Day 90: __________ (Delete old)
```

## Troubleshooting Quick Checks

| Issue | Quick Fix |
|-------|-----------|
| Build fails | Check Logs tab |
| App won't start | Verify DATABASE_URL |
| Connection timeout | Wait 30s (free tier wake-up) |
| CSRF error | Clear browser cache |
| Backup fails | Check `RENDER_DATABASE_URL` secret |
| No auto-deploy | Verify branch is `main` |
| SSL pending | Wait 5-10 minutes |
| 500 error | Check Logs for traceback |

## Support Contacts

- **Render Support**: support@render.com
- **Render Community**: https://community.render.com
- **GitHub Issues**: Repository issues tab

## Quick Links

- [Initial Setup](Render-Setup.md)
- [Database Rotation](Database-Rotation.md)
- [Backup & Restore](Backup-and-Restore.md)
- [Troubleshooting](Troubleshooting.md)
- [Deployment Overview](README.md)

## Workflow Badges

Add to your README:

```markdown
![Deploy](https://github.com/YOUR_USERNAME/backstock/workflows/Deploy%20to%20Render/badge.svg)
![Backup](https://github.com/YOUR_USERNAME/backstock/workflows/Database%20Backup/badge.svg)
```

## Monitoring Checklist

### Weekly
- [ ] Check app is accessible
- [ ] Verify automated backup ran (Monday 2 AM UTC)
- [ ] Check GitHub Actions status

### Monthly
- [ ] Review database size
- [ ] Test restore process
- [ ] Update dependencies if needed

### Day 85 of 90
- [ ] Create final backup
- [ ] Download backup locally
- [ ] Begin rotation process
- [ ] Update calendar for next rotation
