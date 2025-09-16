# Role-Based Access Control (RBAC) System

PersonaMap now includes a comprehensive role-based access control system that supports organizations, websites, and granular permissions.

## 🏗️ Architecture Overview

### Hierarchical Structure
```
Super Admin (global access)
└── Organisation
    ├── Users (with organisation roles)
    └── Websites (many-to-many relationship)
        ├── Crawl Jobs
        ├── Personas
        └── Reports/Content Mappings
```

### Core Entities

#### 1. **Organisation**
- Top-level entity that groups users and websites
- Users belong to one or more organisations
- Websites can be shared across multiple organisations

#### 2. **Website** 
- Contains crawl jobs, personas, and content mappings
- Can belong to multiple organisations (many-to-many)
- Access controlled at website level

#### 3. **User Roles**
- **Super Admin**: Global access to everything
- **Organisation Admin**: Full control within their organisation(s)
- **Website Manager**: Manage specific websites they're assigned to
- **Website Viewer**: Read-only access to assigned websites

## 🔑 Permission Matrix

| Action | Super Admin | Org Admin | Website Manager | Website Viewer |
|--------|-------------|-----------|-----------------|----------------|
| Create/Delete Organisations | ✅ | ❌ | ❌ | ❌ |
| Manage Organisation Users | ✅ | ✅* | ❌ | ❌ |
| Create/Delete Websites | ✅ | ❌ | ❌ | ❌ |
| Assign Websites to Orgs | ✅ | ✅* | ❌ | ❌ |
| Manage Website Users | ✅ | ✅* | ✅* | ❌ |
| Create/Edit Crawl Jobs | ✅ | ✅* | ✅* | ❌ |
| View Crawl Jobs | ✅ | ✅* | ✅* | ✅* |
| Create/Edit Personas | ✅ | ✅* | ✅* | ❌ |
| View Personas & Reports | ✅ | ✅* | ✅* | ✅* |

*Only for their assigned organisations/websites

## 📊 Database Schema

### New Tables

```sql
-- Organisations
CREATE TABLE organisations (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Websites
CREATE TABLE websites (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    domain VARCHAR(500) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Organisation-Website many-to-many
CREATE TABLE organisation_websites (
    id INTEGER PRIMARY KEY,
    organisation_id INTEGER REFERENCES organisations(id),
    website_id INTEGER REFERENCES websites(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organisation_id, website_id)
);

-- User organisation roles
CREATE TABLE user_organisation_roles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    organisation_id INTEGER REFERENCES organisations(id),
    role VARCHAR(50) DEFAULT 'website_viewer',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, organisation_id)
);

-- User website roles
CREATE TABLE user_website_roles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    website_id INTEGER REFERENCES websites(id),
    role VARCHAR(50) DEFAULT 'website_viewer',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, website_id)
);
```

### Updated Tables

```sql
-- Users table (added is_super_admin column)
ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE;

-- Crawl jobs (added website_id foreign key)
ALTER TABLE crawl_jobs ADD COLUMN website_id INTEGER REFERENCES websites(id);

-- Personas (added website_id foreign key)
ALTER TABLE personas ADD COLUMN website_id INTEGER REFERENCES websites(id);
```

## 🚀 Getting Started

### 1. Run Migration
```bash
# Initialize database with RBAC system
export FLASK_APP=run.py
flask init-db

# Or run just the RBAC migration
flask migrate-rbac
```

### 2. Create Super Admin
```bash
# Create additional super admin users
flask create-super-admin
```

### 3. Create Organisation and Website
```bash
# Create your first organisation
flask create-organisation

# Create your first website
flask create-website

# Add users to organisation
flask add-user-to-org
```

### 4. Access New Features
- Navigate to `/organisations` to manage organisations
- Navigate to `/websites` to manage websites
- Users will only see content they have access to

## 🔧 API Usage Examples

### Check User Permissions in Views
```python
from flask import abort
from flask_login import current_user
from app.auth.permissions import website_access_required

@bp.route('/websites/<int:id>/crawls')
@login_required
@website_access_required(website_id_param='id')
def view_crawls(id):
    # User has been verified to have access to website
    website = Website.query.get_or_404(id)
    crawls = website.get_crawl_jobs()
    return render_template('crawls.html', crawls=crawls)

# Or check permissions manually
@bp.route('/some-endpoint')
@login_required
def some_view():
    if not current_user.can_manage_website(website_id):
        abort(403)
    # ... rest of view logic
```

### Filter Data by Access
```python
from app.auth.permissions import get_user_accessible_websites

@bp.route('/dashboard')
@login_required
def dashboard():
    # Only get websites user has access to
    websites = get_user_accessible_websites()
    crawl_jobs = get_user_accessible_crawl_jobs()
    personas = get_user_accessible_personas()
    
    return render_template('dashboard.html', 
                         websites=websites,
                         crawl_jobs=crawl_jobs,
                         personas=personas)
```

### Assign Users Programmatically
```python
from app.auth.permissions import assign_user_to_organisation, assign_user_to_website

# Add user to organisation (requires super admin)
assign_user_to_organisation(user.id, org.id, 'org_admin')

# Add user to website (requires super admin or website manager)
assign_user_to_website(user.id, website.id, 'website_manager')
```

## 🔄 Migration Strategy

The RBAC system is designed to be backward compatible:

1. **Existing users** are automatically migrated to a "Default Organisation"
2. **Existing crawl jobs and personas** are assigned to a "Default Website"
3. **Legacy permission methods** still work for backward compatibility
4. **Super admin flag** is set for existing admin users

### Legacy Support
```python
# These methods still work for backward compatibility
current_user.is_admin()           # Checks super admin OR legacy admin role
current_user.can_create_crawls()  # Uses new RBAC if website_id present, 
                                  # falls back to legacy permissions
```

## 🛡️ Security Considerations

### Permission Decorators
```python
# Require super admin access
@super_admin_required
def admin_only_view(): pass

# Require organisation admin access
@organisation_admin_required(organisation_id_param='org_id')
def org_admin_view(org_id): pass

# Require website access
@website_access_required(website_id_param='website_id')
def website_view(website_id): pass

# Require specific crawl job access
@crawl_job_access_required(crawl_job_id_param='id')
def crawl_job_view(id): pass
```

### Data Isolation
- Users can only see organisations they belong to
- Website access is controlled by organisation membership + direct assignment
- Crawl jobs, personas, and content mappings inherit website permissions
- Super admins bypass all restrictions (use carefully!)

## 🔍 Troubleshooting

### Common Issues

1. **"Access Denied" errors**: Check user has correct organisation/website roles
2. **Missing data**: Ensure user has access to the website containing the data
3. **Migration issues**: Run `flask migrate-rbac` manually if needed

### Debug Commands
```bash
# List all users and their roles
flask list-users

# Check database state
flask shell
>>> User.query.count()
>>> Organisation.query.count()
>>> Website.query.count()
```

### Logs
```python
# Enable debug logging for permissions
import logging
logging.getLogger('app.auth.permissions').setLevel(logging.DEBUG)
```

## 📝 Future Enhancements

- **Team/Group roles**: Intermediate level between organisation and website
- **Time-based access**: Temporary permissions with expiration
- **API key management**: Service account authentication
- **Audit logging**: Track permission changes and access patterns
- **Custom permissions**: Fine-grained action-based permissions

## 🤝 Contributing

When adding new features that involve data access:

1. **Add permission checks** using decorators or manual checks
2. **Filter data** using the helper functions
3. **Test with different user roles** to ensure proper isolation
4. **Update permission matrix** in this documentation
