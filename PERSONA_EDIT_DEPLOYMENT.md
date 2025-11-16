# Persona Edit Functionality - PythonAnywhere Deployment

## 📦 Deployment Package
**File**: `personamap-persona-edit-fix.zip`

## 🔧 What's Fixed
✅ **Persona Selection in Edit Form**: Users can now add/remove persona assignments when editing existing crawl jobs
✅ **Pre-selected Personas**: Currently assigned personas appear as checked in the edit form
✅ **Database Schema Sync**: Local database updated with missing columns from PythonAnywhere

## 📝 Files Modified

### Key Changes:
1. **`app/templates/crawler/edit.html`**: 
   - Added persona selection UI matching the create form
   - Fixed checkbox state logic with `|string` filter for proper pre-selection

2. **`app/routes/crawler.py`**: 
   - Enhanced edit route to handle persona assignments
   - Added persona removal/addition logic
   - Provided `available_personas` and `current_persona_ids` to templates

## 🚀 PythonAnywhere Deployment Steps

### 1. Upload the Package
1. Go to **Files** tab in PythonAnywhere dashboard
2. Upload `personamap-persona-edit-fix.zip` to your home directory
3. Extract it: `unzip personamap-persona-edit-fix.zip -d temp/`

### 2. Backup Current Installation
```bash
# In PythonAnywhere Bash console
cd ~/personamapper
cp -r app app_backup_$(date +%Y%m%d)
echo "✅ Backup created"
```

### 3. Update Modified Files
```bash
# Copy the updated files from temp directory
cd ~/
cp temp/app/templates/crawler/edit.html ~/personamapper/app/templates/crawler/edit.html
cp temp/app/routes/crawler.py ~/personamapper/app/routes/crawler.py

echo "✅ Updated files copied"
```

### 4. Verify File Updates
```bash
# Check that the key changes are present
cd ~/personamapper

# Verify edit.html has persona selection
grep -n "persona.id|string" app/templates/crawler/edit.html

# Verify crawler.py has persona handling  
grep -n "persona_ids.*getlist" app/routes/crawler.py

echo "✅ Files updated successfully"
```

### 5. Restart Web App
1. Go to **Web** tab in PythonAnywhere dashboard
2. Click **"Reload [yourusername].pythonanywhere.com"**
3. Wait for reload to complete

### 6. Test the Functionality
1. Visit your PythonAnywhere site: `https://[yourusername].pythonanywhere.com`
2. Login with your credentials
3. Navigate to any crawl job that has personas assigned
4. Click **"Edit"** - you should see:
   - ✅ Personas section in the form
   - ✅ Currently assigned personas pre-checked
   - ✅ Ability to add/remove personas
5. Make a test edit and save to confirm personas are updated

## 🔍 Troubleshooting

### If personas don't appear pre-checked:
- Clear browser cache and reload
- Check that crawl job actually has personas assigned
- Verify the template syntax is correct

### If edit form doesn't show persona section:
- Ensure `app/templates/crawler/edit.html` was updated correctly
- Check that `available_personas` is being passed from the route
- Restart the web app

### If persona updates don't save:
- Verify `app/routes/crawler.py` has the persona handling code
- Check error logs in PythonAnywhere dashboard
- Ensure database has `crawl_job_personas` table

## 📋 Verification Checklist
- [ ] Files uploaded and extracted
- [ ] Backup created
- [ ] Template file updated (`edit.html`)  
- [ ] Route file updated (`crawler.py`)
- [ ] Web app reloaded
- [ ] Login successful
- [ ] Edit form shows persona section
- [ ] Assigned personas appear checked
- [ ] Can modify persona assignments
- [ ] Changes save successfully

## 🎯 Expected Behavior After Deployment
1. **Edit Crawl Form**: Shows persona selection section identical to create form
2. **Pre-selection**: Personas currently assigned to crawl job appear as checked
3. **Modification**: Users can check/uncheck personas to add/remove assignments  
4. **Persistence**: Changes are saved to `crawl_job_personas` table
5. **UI Consistency**: Edit form matches create form functionality

## 📚 Technical Details

### Template Fix:
```html
<!-- Before: Type mismatch (integer vs string) -->
{{ 'checked' if persona.id in current_persona_ids else '' }}

<!-- After: Proper string comparison -->
{{ 'checked' if persona.id|string in current_persona_ids else '' }}
```

### Route Enhancement:
```python
# Collects persona IDs from form
persona_ids = request.form.getlist('persona_ids')

# Removes existing assignments and adds new ones
CrawlJobPersona.query.filter_by(crawl_job_id=crawl_job.id).delete()
for persona_id in persona_ids:
    if persona_id:
        crawl_job_persona = CrawlJobPersona(
            crawl_job_id=crawl_job.id,
            persona_id=int(persona_id)
        )
        db.session.add(crawl_job_persona)
```

## 🔄 Rollback Plan (if needed)
```bash
# If something goes wrong, restore from backup
cd ~/personamapper
rm -rf app
mv app_backup_[date] app
# Then reload web app in PythonAnywhere dashboard
```

---
**✅ This deployment adds complete persona edit functionality to match the create form behavior.**