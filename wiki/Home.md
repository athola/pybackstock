# Backstock Wiki

Welcome to the Backstock documentation wiki.

## Quick Links

### 🚀 Deployment
- **[Deployment Overview](deployment/README.md)** - Start here for deployment
- **[Render Setup](deployment/Render-Setup.md)** - Initial deployment guide
- **[Database Rotation](deployment/Database-Rotation.md)** - 90-day rotation process
- **[Backup & Restore](deployment/Backup-and-Restore.md)** - Database backup procedures
- **[Troubleshooting](deployment/Troubleshooting.md)** - Common issues
- **[Quick Reference](deployment/Quick-Reference.md)** - Commands and checklists

### 🏗️ Architecture
- **[Architecture Overview](architecture/README.md)** - Architecture decisions
- **[ADR-0001: Security Controls](architecture/ADR-0001-implement-comprehensive-security-controls.md)** - Security implementation

## About Backstock

Backstock is a Python Flask application for managing grocery store inventory. It provides:

- Search inventory by multiple criteria
- Add individual items or bulk upload via CSV
- PostgreSQL database with SQLAlchemy ORM
- Bootstrap-based web interface
- Comprehensive security controls (CSRF, XSS, security headers)

### Technology Stack

- **Backend**: Python 3.11+, Flask 3.x
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Frontend**: HTML, CSS (Bootstrap), JavaScript (jQuery)
- **Testing**: pytest, pytest-flask, playwright
- **Deployment**: Render.com (free tier)
- **CI/CD**: GitHub Actions

## Getting Started

### For Deployment
1. Read [Deployment Overview](deployment/README.md)
2. Follow [Render Setup](deployment/Render-Setup.md)
3. Configure automated backups
4. Set calendar reminder for database rotation

### For Development
See the main [README.md](../README.md) in the repository root for:
- Local development setup
- Running tests
- Database management
- Interactive demo

## Wiki Organization

```
wiki/
├── Home.md (this page)
├── deployment/
│   ├── README.md - Deployment overview
│   ├── Render-Setup.md - Initial setup
│   ├── Database-Rotation.md - 90-day rotation
│   ├── Backup-and-Restore.md - Backup procedures
│   ├── Troubleshooting.md - Common issues
│   └── Quick-Reference.md - Commands/checklists
└── architecture/
    ├── README.md - Architecture overview
    └── ADR-0001-*.md - Architecture decisions
```

## Contributing

When adding new documentation:

1. **Deployment guides** → `wiki/deployment/`
2. **Architecture decisions** → `wiki/architecture/ADR-NNNN-*.md`
3. **Update this Home page** with links to new content
4. **Follow existing format** for consistency

## External Resources

- **Repository**: [GitHub](https://github.com/YOUR_USERNAME/backstock)
- **Live Demo**: [Render](https://backstock.onrender.com)
- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Flask Docs**: [flask.palletsprojects.com](https://flask.palletsprojects.com/)

## Support

- **Deployment Issues**: [Troubleshooting](deployment/Troubleshooting.md)
- **Application Bugs**: GitHub Issues
- **Render Platform**: support@render.com
