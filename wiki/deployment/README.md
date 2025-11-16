# Deployment Guide

Backstock deployment documentation for hosting your portfolio demo.

## Overview

Backstock is configured for deployment on **Render.com** as a free Heroku alternative. This provides:

- Free web hosting with auto-deploy from GitHub
- Free PostgreSQL database (1GB storage)
- Free SSL certificates
- Automated weekly backups

## Quick Links

- **[Initial Setup](Render-Setup.md)** - Deploy to Render for the first time
- **[Database Rotation](Database-Rotation.md)** - Handle 90-day expiration
- **[Backup & Restore](Backup-and-Restore.md)** - Database backup procedures
- **[Troubleshooting](Troubleshooting.md)** - Common issues and solutions
- **[Quick Reference](Quick-Reference.md)** - Commands and checklist

## Free Tier Specifications

| Resource | Limit | Notes |
|----------|-------|-------|
| Web Service | Free | Auto-sleep after 15 min inactivity |
| PostgreSQL | 1GB | ⚠️ **Expires after 90 days** |
| SSL Certificate | Included | Automatic provisioning |
| Build Minutes | Unlimited | Shared resources |

## Important Warning

**Free Render databases expire after 90 days** from creation (not from inactivity). This is a hard limit. You must rotate the database before expiration to avoid data loss.

See [Database Rotation](Database-Rotation.md) for the complete process.

## Getting Started

1. **[Set up Render deployment](Render-Setup.md)** - 5 minutes
2. **Configure GitHub secrets** for automated backups
3. **Set calendar reminder** for Day 85 (database rotation)

## Automation

This repository includes GitHub Actions workflows for:

- **Deployment** (`.github/workflows/deploy.yml`)
  - Auto-deploy on push to `main`
  - Run tests before deployment

- **Database Backups** (`.github/workflows/database-backup.yml`)
  - Weekly backups (Monday 2 AM UTC)
  - Stored in GitHub Releases
  - 90-day retention

## Support

- **Render Issues:** support@render.com
- **Application Issues:** GitHub Issues
- **Documentation:** This wiki
