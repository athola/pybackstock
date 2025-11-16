# Troubleshooting

Common issues and solutions for Render deployment.

## Deployment Issues

### Build Fails

**Symptoms:**
- Deployment stuck on "Building"
- Build errors in logs
- Dependencies not installing

**Solutions:**

1. **Check Python version:**
   ```bash
   # Verify runtime.txt
   cat runtime.txt
   # Should show: python-3.11.14
   ```

2. **Verify dependencies:**
   ```bash
   # Ensure pyproject.toml dependencies are correct
   uv sync --frozen
   ```

3. **Check build logs:**
   - Render Dashboard → Service → Logs tab
   - Look for error messages
   - Common: missing dependencies, syntax errors

4. **Clear build cache:**
   - Dashboard → Service → Settings
   - Scroll to "Build & Deploy"
   - Click "Clear build cache"
   - Trigger new deployment

### Application Won't Start

**Symptoms:**
- Build succeeds but app crashes
- "Application failed to start" error
- 502/503 errors

**Solutions:**

1. **Check start command:**
   ```yaml
   # In render.yaml
   startCommand: "gunicorn 'src.backstock.app:app'"
   ```

2. **Verify environment variables:**
   - Dashboard → Service → Environment
   - Ensure DATABASE_URL is set
   - Check APP_SETTINGS is `config.ProductionConfig`
   - Verify SECRET_KEY exists

3. **Check application logs:**
   - Dashboard → Service → Logs
   - Look for Python exceptions
   - Check database connection errors

4. **Test locally:**
   ```bash
   # Use production config
   export APP_SETTINGS=config.ProductionConfig
   gunicorn 'src.backstock.app:app'
   ```

### Auto-Deploy Not Working

**Symptoms:**
- Push to main doesn't trigger deployment
- GitHub shows push but Render doesn't deploy

**Solutions:**

1. **Check auto-deploy setting:**
   - Dashboard → Service → Settings
   - Verify "Auto-Deploy" is enabled
   - Check correct branch is set (main)

2. **Verify GitHub connection:**
   - Dashboard → Account Settings
   - Check GitHub integration is active
   - Reconnect if needed

3. **Check render.yaml:**
   ```yaml
   autoDeploy: true
   branch: main
   ```

4. **Manual deploy:**
   - Dashboard → Service
   - Click "Manual Deploy" → "Deploy latest commit"

## Database Issues

### Connection Timeout

**Symptoms:**
- First request takes 30+ seconds
- "Could not connect to database" error
- Intermittent connection issues

**Cause:** Free tier databases sleep after inactivity

**Solutions:**

1. **First request warm-up:**
   - Free tier databases wake on first request
   - Expect 10-30 second delay
   - Subsequent requests are fast

2. **Keep-alive (not recommended for free tier):**
   - Creates unnecessary load
   - May exceed free tier limits

3. **Health check adjustments:**
   - Increase timeout in health check
   - Dashboard → Service → Settings → Health Check Path

### Database Connection Errors

**Symptoms:**
- "Connection refused"
- "FATAL: password authentication failed"
- "could not connect to server"

**Solutions:**

1. **Verify DATABASE_URL:**
   ```bash
   # In Render dashboard
   # Database → Connect → Internal Database URL

   # Should look like:
   # postgresql://user:pass@host:port/dbname
   ```

2. **Check database status:**
   - Dashboard → Database
   - Ensure status is "Available"
   - Check for maintenance windows

3. **Update environment variable:**
   - Dashboard → Service → Environment
   - Edit DATABASE_URL
   - Paste correct value from database

4. **Test connection:**
   ```bash
   export DATABASE_URL="postgresql://..."
   psql $DATABASE_URL -c "SELECT 1;"
   ```

### Out of Storage

**Symptoms:**
- "disk quota exceeded"
- Insert operations fail
- 1GB limit reached

**Solutions:**

1. **Check database size:**
   ```bash
   psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('backstock'));"
   ```

2. **Clean up data:**
   ```sql
   -- Delete old items (example)
   DELETE FROM grocery_items WHERE last_sold < '2020-01-01';

   -- Vacuum to reclaim space
   VACUUM FULL;
   ```

3. **Optimize tables:**
   ```bash
   psql $DATABASE_URL -c "VACUUM ANALYZE;"
   ```

4. **Upgrade plan:**
   - Free tier: 1GB limit
   - Paid tier: 10GB+ available

### Database Expired

**Symptoms:**
- "database does not exist"
- 90 days passed since creation
- Cannot connect to database

**Solutions:**

1. **Retrieve latest backup:**
   - GitHub → Releases tab
   - Download latest backup
   - Or check local `backups/` directory

2. **Create new database:**
   - See [Database Rotation](Database-Rotation.md)
   - Follow Day 86-89 steps

3. **Restore data:**
   ```bash
   export DATABASE_URL="new_database_url"
   ./scripts/restore_database.sh backups/latest_backup.sql.gz
   ```

## SSL Certificate Issues

### Certificate Not Provisioning

**Symptoms:**
- "Not secure" in browser
- SSL certificate pending
- HTTPS not working

**Solutions:**

1. **Wait for provisioning:**
   - Initial SSL takes 5-10 minutes
   - Check Dashboard → Service → Settings

2. **Custom domain:**
   - Render domains get automatic SSL
   - Custom domains require DNS configuration
   - Add CNAME record as shown in dashboard

3. **Check HTTPS enforcement:**
   ```python
   # In config.py
   # Should be True in production
   force_https=is_production
   ```

4. **Access via HTTP first:**
   - Try http://your-app.onrender.com
   - Then upgrade to https://

## Performance Issues

### Slow Response Times

**Symptoms:**
- Pages load slowly
- API requests timeout
- Intermittent performance

**Solutions:**

1. **Free tier limitations:**
   - Shared CPU/memory
   - Auto-sleep after 15 min
   - First request wakes service (10-30s)

2. **Check service status:**
   - Dashboard → Service
   - Look for "Suspended" or "Sleeping"
   - First request after sleep is slow

3. **Optimize queries:**
   ```python
   # Add indexes to frequent queries
   # Minimize database round-trips
   # Use SQLAlchemy eager loading
   ```

4. **Monitor resources:**
   - Dashboard → Service → Metrics
   - Check CPU/memory usage
   - Consider upgrading if consistently high

### Build Takes Too Long

**Symptoms:**
- Build phase exceeds 10 minutes
- Frequent timeouts
- Slow dependency installation

**Solutions:**

1. **Using uv for faster installs:**
   ```yaml
   # In render.yaml (already configured)
   buildCommand: "pip install uv && uv sync --frozen"
   ```

2. **Minimize dependencies:**
   - Remove unused packages from pyproject.toml
   - Keep only necessary dependencies

3. **Cache dependencies:**
   - Render caches between builds
   - First build is slower
   - Subsequent builds are faster

## GitHub Actions Issues

### Backup Workflow Fails

**Symptoms:**
- Workflow shows red X
- No backup created
- Error in workflow logs

**Solutions:**

1. **Check DATABASE_URL secret:**
   - GitHub → Settings → Secrets → Actions
   - Verify `RENDER_DATABASE_URL` exists
   - Update if database rotated

2. **Check workflow logs:**
   - Actions tab → Failed workflow
   - Click on failed step
   - Read error message

3. **Test backup locally:**
   ```bash
   export DATABASE_URL="..."
   python scripts/automated_backup.py
   ```

4. **Verify pg_dump available:**
   - Workflow installs postgresql-client
   - Check installation step succeeds

### Deploy Workflow Fails

**Symptoms:**
- Tests fail
- Linting errors
- Deployment blocked

**Solutions:**

1. **Run tests locally:**
   ```bash
   uv run pytest -v
   ```

2. **Check linting:**
   ```bash
   uv run ruff check .
   ```

3. **Fix issues and push:**
   ```bash
   git add .
   git commit -m "Fix test/lint issues"
   git push
   ```

## Application Errors

### CSRF Token Missing

**Symptoms:**
- 400 Bad Request
- "CSRF token missing" error
- Forms don't submit

**Solutions:**

1. **Check form has token:**
   ```html
   <form method="POST">
       {{ csrf_token() }}
       <!-- form fields -->
   </form>
   ```

2. **Verify CSRF enabled:**
   ```python
   # In config.py
   WTF_CSRF_ENABLED = True
   ```

3. **Clear browser cache:**
   - Old cached pages may not have token
   - Hard refresh (Ctrl+Shift+R)

### 500 Internal Server Error

**Symptoms:**
- Generic error page
- No specific error message
- Application crashes

**Solutions:**

1. **Check logs:**
   - Dashboard → Service → Logs
   - Look for Python tracebacks
   - Identify error source

2. **Check database connection:**
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```

3. **Verify migrations:**
   ```bash
   # If database schema outdated
   python scripts/manage.py db upgrade
   ```

4. **Check SECRET_KEY:**
   - Dashboard → Service → Environment
   - Ensure SECRET_KEY is set
   - Should be auto-generated

## Getting Help

### Check These First

1. Render Dashboard logs
2. GitHub Actions workflow logs
3. This troubleshooting guide
4. [Render documentation](https://render.com/docs)

### Contact Support

**Render Support:**
- Email: support@render.com
- Dashboard → Help & Support
- [Render Community](https://community.render.com)

**Application Issues:**
- GitHub Issues for this repository
- Include error messages
- Provide steps to reproduce

### Useful Commands

```bash
# Check database connection
psql $DATABASE_URL -c "SELECT version();"

# View database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('backstock'));"

# Test local deployment
gunicorn 'src.backstock.app:app'

# Run tests
uv run pytest -v

# Check linting
uv run ruff check .

# Create backup
./scripts/backup_database.sh

# View logs
# (Use Render Dashboard → Service → Logs)
```

### Debug Mode

**Never enable in production!**

For local debugging only:
```bash
# .env file
APP_SETTINGS=config.DevelopmentConfig
DEBUG=True
```

This shows detailed error pages with stack traces. Never use in production as it exposes sensitive information.
