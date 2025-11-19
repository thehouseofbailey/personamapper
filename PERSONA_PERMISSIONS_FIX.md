# Persona Permission Fix - PythonAnywhere Deployment

## 🔒 Security Fix Summary
**Issue**: Website Viewers could access persona edit functionality when they should only have view-only access.

**Fix**: Added proper RBAC permissions to restrict edit access to Website Managers and above.

## 📦 Deployment Package
**File**: `personamap-persona-permissions-fix.zip`

## 🔧 What's Fixed
✅ **Template Permission Check**: Edit button now only shows for users who can manage the website
✅ **Route Protection**: Edit and delete routes now require `persona_manager_required` permission
✅ **RBAC Compliance**: Proper role-based access control for persona management

## 📝 Files Modified

### 1. **`app/templates/personas/view.html`**
**Change**: Added permission check around edit button
```html
<!-- Before: Always visible -->
<a href="{{ url_for('personas.edit_persona', id=persona.id) }}" class="btn btn-outline-primary me-2">
    <i class="bi bi-pencil"></i> Edit
</a>

<!-- After: Only visible to website managers -->
{% if current_user.can_manage_website(persona.website_id) %}
<a href="{{ url_for('personas.edit_persona', id=persona.id) }}" class="btn btn-outline-primary me-2">
    <i class="bi bi-pencil"></i> Edit
</a>
{% endif %}
```

### 2. **`app/routes/personas.py`**
**Changes**: 
- Added `persona_manager_required` import
- Added `@persona_manager_required()` decorator to edit and delete routes

```python
# Added imports
from app.auth.permissions import website_manager_required, persona_manager_required

# Protected edit route
@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@persona_manager_required()  # ← New permission check
def edit_persona(id):

# Protected delete route  
@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@persona_manager_required()  # ← New permission check
def delete_persona(id):
```

## 🚀 PythonAnywhere Deployment Steps

### 1. Upload the Package
1. Go to **Files** tab in PythonAnywhere dashboard
2. Upload `personamap-persona-permissions-fix.zip` to your home directory
3. Extract it: `unzip personamap-persona-permissions-fix.zip -d temp/`

### 2. Backup Current Installation
```bash
# In PythonAnywhere Bash console
cd ~/personamapper
cp -r app app_backup_permissions_$(date +%Y%m%d)
echo "✅ Backup created"
```

### 3. Update Modified Files
```bash
# Copy the updated files from temp directory
cd ~/
cp temp/app/templates/personas/view.html ~/personamapper/app/templates/personas/view.html
cp temp/app/routes/personas.py ~/personamapper/app/routes/personas.py

echo "✅ Updated files copied"
```

### 4. Verify File Updates
```bash
# Check that the permission check is present in template
cd ~/personamapper
grep -n "can_manage_website" app/templates/personas/view.html

# Verify route has persona_manager_required decorator
grep -A 2 -B 1 "persona_manager_required" app/routes/personas.py

echo "✅ Permission checks verified"
```

### 5. Restart Web App
1. Go to **Web** tab in PythonAnywhere dashboard
2. Click **"Reload [yourusername].pythonanywhere.com"**
3. Wait for reload to complete

### 6. Test the Fix

#### As Website Viewer:
1. Login with Website Viewer credentials
2. Navigate to any persona: `/personas/[id]`
3. **Expected**: ✅ Can view persona details, ❌ Edit button should be hidden
4. Try direct access to edit URL: `/personas/[id]/edit`
5. **Expected**: ❌ Should get 403 Forbidden error

#### As Website Manager or above:
1. Login with Website Manager/Organisation Admin credentials  
2. Navigate to persona: `/personas/[id]`
3. **Expected**: ✅ Can view persona, ✅ Edit button visible and functional

## 🔍 Troubleshooting

### If edit button still appears for Website Viewers:
- Clear browser cache and reload
- Check that `app/templates/personas/view.html` was updated correctly
- Verify user role assignment in database
- Restart the web app

### If edit route throws 500 error instead of 403:
- Check that `app/routes/personas.py` imports were updated
- Verify `persona_manager_required` decorator is present
- Check error logs in PythonAnywhere dashboard

### If permission check fails for valid users:
- Verify user has correct website role assignment
- Check that persona belongs to the correct website
- Ensure RBAC system is functioning properly

## 📋 Verification Checklist
- [ ] Files uploaded and extracted
- [ ] Backup created
- [ ] Template file updated (`view.html`)
- [ ] Route file updated (`personas.py`) 
- [ ] Web app reloaded
- [ ] Website Viewer cannot see edit button
- [ ] Website Viewer gets 403 on direct edit URL access
- [ ] Website Manager can still edit personas
- [ ] No errors in application logs

## 🎯 Expected Behavior After Fix

### Website Viewer Role:
- ✅ Can view persona details and mappings
- ❌ Cannot see edit button
- ❌ Cannot access edit URL (gets 403 Forbidden)
- ❌ Cannot delete personas

### Website Manager+ Roles:
- ✅ Can view persona details and mappings  
- ✅ Can see and use edit button
- ✅ Can access edit URL and modify personas
- ✅ Can delete personas (if authorized)

## 🛡️ Security Impact
This fix ensures proper separation of roles:
- **Viewers**: Read-only access to content they're authorized to see
- **Managers**: Full management capabilities for their assigned websites
- **Admins**: Elevated permissions as designed

The fix operates at both the UI level (hiding buttons) and security level (route protection), ensuring defense in depth.

---
**✅ This deployment secures persona management according to RBAC principles.**