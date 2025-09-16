# Deployment Checklist - Resume Health Checker

## Pre-Deployment Testing (Required)

### 1. 🧪 Automated Tests
```bash
# Run the UI regression test suite
python3 test_ui_regression.py
```
**Status**: ✅ Must pass before deployment

### 2. 🎯 Manual UI Testing
Test each template type with real data:

#### Interview Templates
- [ ] Expand All button works (uses .every() logic)
- [ ] Individual question expand/collapse works
- [ ] PDF export shows ALL questions expanded (even if UI shows collapsed)
- [ ] DOCX export shows ALL questions expanded
- [ ] UI state restored after export (collapsed questions stay collapsed)

#### Resume Rewrite Templates  
- [ ] PDF export contains ONLY resume content (no analysis section)
- [ ] DOCX export contains ONLY resume content (no analysis section)
- [ ] Analysis section still visible in UI after export
- [ ] Page break styling works (analysis on separate page in UI)

#### All Templates
- [ ] PDF export buttons work without ReferenceError
- [ ] DOCX export buttons work without ReferenceError
- [ ] Export files download successfully
- [ ] Export files open correctly in respective applications

### 3. 🔍 Browser Testing
Test in multiple browsers:
- [ ] Chrome/Chromium
- [ ] Safari
- [ ] Firefox
- [ ] Mobile Safari (if mobile-supported)

### 4. 🌐 Cross-Template Consistency
- [ ] All templates use consistent button classes
- [ ] All templates load required JavaScript libraries
- [ ] No console errors in any template
- [ ] Consistent styling and behavior

## Git Workflow

### 1. 🔒 Pre-Commit Hook Setup
```bash
# Enable the pre-commit hook
git config core.hooksPath .githooks
```

The pre-commit hook will automatically run `test_ui_regression.py` before each commit.

### 2. 📝 Commit Standards
When making UI changes, use these commit message prefixes:
- `fix(ui):` - Bug fixes in UI functionality
- `feat(ui):` - New UI features
- `refactor(ui):` - UI code refactoring
- `test(ui):` - UI test updates
- `docs(ui):` - UI documentation updates

Example:
```bash
git commit -m "fix(ui): preserve interview question expansion state during PDF export"
```

## Production Deployment Steps

### 1. 🚀 Pre-Deploy Verification
- [ ] All tests passing locally
- [ ] No console errors in browser
- [ ] Server running without errors
- [ ] Database migrations applied (if any)

### 2. 🔄 Deployment Process
```bash
# 1. Final test run
python3 test_ui_regression.py

# 2. Commit changes
git add .
git commit -m "descriptive message"

# 3. Push to production branch
git push origin main

# 4. Verify Railway deployment
# Check Railway dashboard for successful build
```

### 3. 🎯 Post-Deploy Verification
Test on production environment:
- [ ] Upload a test resume
- [ ] Complete a premium purchase flow
- [ ] Test interview export functionality
- [ ] Test resume rewrite export functionality
- [ ] Verify no JavaScript errors in production

## Rollback Plan

If issues are discovered after deployment:

### 1. 🚨 Immediate Issues
```bash
# Revert to previous working commit
git revert HEAD
git push origin main
```

### 2. 📊 Monitor for 24 Hours
- Check error logs
- Monitor user feedback
- Verify export functionality works for real users

## Documentation Updates

### 1. 📚 Required Updates After Changes
- [ ] Update `DESIGN_DECISIONS.md` with new patterns
- [ ] Update `CLAUDE.md` with new functionality
- [ ] Update this checklist if new testing requirements emerge

### 2. 🎓 Knowledge Transfer
For next developer/sprint:
- [ ] Review `DESIGN_DECISIONS.md` first
- [ ] Run `test_ui_regression.py` to understand current functionality
- [ ] Test manually before making any changes

## Emergency Contacts

### 🆘 If Issues Arise
1. **Check server logs**: Look for JavaScript errors or export failures
2. **Run local tests**: `python3 test_ui_regression.py`
3. **Test specific functionality**: Follow manual testing checklist above
4. **Rollback if necessary**: Use rollback plan above

### 📞 Escalation Path
1. Check Railway deployment logs
2. Review browser console for errors
3. Test with different resume files
4. Check Stripe payment flow (if affected)

## Success Criteria

### ✅ Deployment Successful When:
- All automated tests pass
- Manual testing checklist complete
- No increase in error rates
- Export functionality works for all template types
- No user complaints about broken functionality

### ❌ Rollback Required When:
- Automated tests fail
- Users report broken export functionality
- JavaScript ReferenceErrors in production
- Export files are corrupted or incomplete

---

**Remember**: It's better to delay deployment and fix issues than to deploy broken functionality to paying customers.