# Change Protection Protocol

## 🚨 CRITICAL: Pre-Change Checklist

Before making ANY changes to the codebase, I MUST:

1. **Document Current State**
   - List all existing API endpoints with `grep -n "@router\." app/api/routes.py`
   - Document current file structure with `find app/ -name "*.py" | sort`
   - Capture current git status with `git status --porcelain`

2. **Impact Analysis**
   - Identify which files will be modified
   - List all functions/endpoints that will be changed
   - Document any new dependencies or imports

3. **Backup Strategy**
   - Create a backup branch before changes: `git checkout -b backup-before-[feature-name]`
   - Tag the current state: `git tag backup-$(date +%Y%m%d-%H%M%S)`

4. **Incremental Changes**
   - Make ONE change at a time
   - Test each change before proceeding
   - Never modify multiple unrelated files simultaneously

## 🛡️ Drift Prevention Rules

### Rule 1: No Wholesale Refactoring
- NEVER modify more than 3 files in a single session
- NEVER remove existing endpoints without explicit user approval
- NEVER change existing function signatures without migration plan

### Rule 2: Endpoint Protection
- Before removing ANY `@router.` endpoint, MUST show user the current list
- User must explicitly approve endpoint removal
- All removed endpoints must be documented with removal reason

### Rule 3: File Modification Limits
- Maximum 1 major file change per response
- All changes must be atomic and reversible
- Show diff before applying changes

### Rule 4: Testing Requirements
- Test all modified endpoints before marking complete
- Verify existing functionality still works
- Run basic smoke tests on critical flows

## 🔍 Change Detection Commands

### Before Starting Work:
```bash
# Document current state
echo "=== CURRENT ENDPOINTS ===" > change-log-$(date +%Y%m%d-%H%M%S).txt
grep -n "@router\." app/api/routes.py >> change-log-$(date +%Y%m%d-%H%M%S).txt
echo "=== CURRENT FILES ===" >> change-log-$(date +%Y%m%d-%H%M%S).txt
find app/ -name "*.py" | sort >> change-log-$(date +%Y%m%d-%H%M%S).txt
```

### After Each Change:
```bash
# Verify endpoints still exist
grep -n "@router\." app/api/routes.py
# Check for syntax errors
python3 -m py_compile app/api/routes.py
```

## 🚨 Emergency Recovery

If drift is detected:
1. `git checkout backup-before-[feature-name]` - Restore to backup branch
2. `git tag --delete [bad-tag]` - Remove bad tags if needed
3. Start over with smaller, incremental changes

## 📋 Required User Approvals

Before I make changes, I MUST get explicit approval for:
- [ ] Removing any existing API endpoints
- [ ] Modifying function signatures
- [ ] Changing import statements
- [ ] Adding new dependencies
- [ ] Modifying more than 2 files simultaneously

## 🎯 Success Criteria

Changes are only considered complete when:
- [ ] All existing endpoints still work
- [ ] No 404 errors in browser console
- [ ] Payment flow works end-to-end
- [ ] Promotional codes work correctly
- [ ] All tests pass
- [ ] No new linting errors

---

**Remember**: It's better to make 10 small, safe changes than 1 large, risky change.
