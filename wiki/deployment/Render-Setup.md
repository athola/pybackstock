# Render Setup Guide

Get your Backstock application deployed to Render in 5 minutes.

## Prerequisites

- GitHub account
- Backstock repository forked or cloned
- Code pushed to GitHub

## Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Click **Get Started** or **Sign Up**
3. Choose **Sign up with GitHub**
4. Authorize Render to access your repositories

## Step 2: Deploy with Blueprint

1. In Render dashboard, click **New +**
2. Select **Blueprint**
3. Connect your GitHub repository (if not already connected)
4. Select the `backstock` repository
5. Render automatically detects `render.yaml`
6. Click **Apply**

Render will now:
- Create PostgreSQL database (`backstock-db`)
- Create web service (`backstock`)
- Install dependencies
- Deploy the application
- Provision SSL certificate

**Wait 5-10 minutes** for initial deployment.

## Step 3: Verify Deployment

1. Check deployment status in Render dashboard
2. Click on your `backstock` service
3. View the **Logs** tab for deployment progress
4. Once deployed, click the URL (e.g., `https://backstock.onrender.com`)

## Step 4: Configure GitHub Secret (for Backups)

1. In Render dashboard → `backstock-db` database
2. Click **Connect** → **External Connection**
3. Copy the **Internal Database URL**
4. Go to GitHub repository → **Settings** → **Secrets and variables** → **Actions**
5. Click **New repository secret**
   - Name: `RENDER_DATABASE_URL`
   - Value: (paste the database URL)
6. Click **Add secret**

## Step 5: Set Rotation Reminder

Calculate expiration date:
```
Creation Date + 90 days = Expiration Date
```

Set calendar reminders:
- **Day 85**: Create database backup
- **Day 86**: Start rotation process

See [Database Rotation](Database-Rotation.md) for details.

## Environment Variables

Render automatically configures these via `render.yaml`:

| Variable | Source | Description |
|----------|--------|-------------|
| `APP_SETTINGS` | `render.yaml` | Set to `config.ProductionConfig` |
| `SECRET_KEY` | Auto-generated | Flask secret key |
| `DATABASE_URL` | Auto-connected | PostgreSQL connection string |

## Your URLs

After deployment:

- **Application**: `https://backstock.onrender.com` (or your assigned URL)
- **Render Dashboard**: https://dashboard.render.com
- **Database Console**: Dashboard → `backstock-db`

## Next Steps

- ✅ Application is deployed
- 📅 Set calendar reminder for database rotation
- 📖 Read [Database Rotation](Database-Rotation.md) guide
- 🔍 Check [Troubleshooting](Troubleshooting.md) if issues occur

## Auto-Deploy Configuration

Every push to `main` branch automatically triggers deployment:

1. GitHub Actions runs tests (`.github/workflows/deploy.yml`)
2. If tests pass, Render detects the push
3. Render rebuilds and deploys the application
4. Zero-downtime deployment

## Troubleshooting

**Deployment Failed?**
- Check Render dashboard **Logs** tab
- Verify `runtime.txt` has Python 3.11.14
- Ensure all dependencies are in `requirements.txt`

**Can't Access Application?**
- Wait 5-10 minutes for initial SSL provisioning
- Check Render service status is "Live"
- Try accessing via HTTP first, then HTTPS

**Database Connection Error?**
- Verify `DATABASE_URL` is set in environment variables
- Check database status in Render dashboard

For more issues, see [Troubleshooting](Troubleshooting.md).
