# STABLE SDLC - MANDATORY PROCESS
## STOP THE FIX-TO-BREAK CYCLE

> **CRITICAL**: This process is MANDATORY. No exceptions. No "quick fixes". No "small changes".

## THE PROBLEM

We keep breaking working functionality while fixing other issues:
- ❌ Fixed PDF exports → Broke JavaScript functions  
- ❌ Fixed interview expansion → Broke resume exports
- ❌ Fixed export functions → Broke free analysis buttons

**THIS STOPS NOW.**

## MANDATORY TESTING MATRIX

### BEFORE ANY CODE CHANGE
```bash
# 1. MANDATORY - Test ALL core user flows (5 minutes)
./test_core_flows.sh

# 2. MANDATORY - Run regression tests
python3 test_ui_regression.py

# 3. MANDATORY - Manual verification checklist
./verify_functionality.sh
```

## CORE USER FLOWS - NEVER BREAK THESE

### Flow 1: Free Analysis Journey
1. ✅ Upload resume file
2. ✅ Get free analysis results  
3. ✅ Copy analysis to clipboard (`copyToClipboard`)
4. ✅ Export analysis to PDF (`exportToPDFClient`)
5. ✅ Click upgrade button → payment flow

### Flow 2: Premium Analysis Journey  
1. ✅ Complete payment
2. ✅ Get premium analysis results
3. ✅ Export to PDF (with correct content)
4. ✅ Export to DOCX (with correct content)

### Flow 3: Interview Analysis Journey
1. ✅ Complete payment for interview
2. ✅ Expand/collapse individual questions (`toggleQuestion`)
3. ✅ Expand/collapse all questions (`toggleAllQuestions`)
4. ✅ Export to PDF (all questions expanded)
5. ✅ Export to DOCX (all questions expanded)

### Flow 4: Resume Rewrite Journey
1. ✅ Complete payment for resume rewrite
2. ✅ View rewritten resume
3. ✅ Export to PDF (resume only, no analysis)
4. ✅ Export to DOCX (resume only, no analysis)

## MANDATORY PRE-COMMIT CHECKLIST

**EVERY developer MUST complete this checklist before ANY commit:**

```bash
□ Did I test the free analysis flow end-to-end?
□ Did I test ALL export functions (PDF/DOCX) for ALL products?
□ Did I test ALL JavaScript functions are accessible?
□ Did I verify no ReferenceErrors in browser console?
□ Did the automated tests pass?
□ Did I update documentation if I changed patterns?
```

**If ANY checkbox is unchecked → DO NOT COMMIT**

## AUTOMATED ENFORCEMENT

### 1. Mandatory Git Hooks
```bash
# Enable MANDATORY pre-commit testing
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

The pre-commit hook will:
- Run regression tests
- Block commits if tests fail
- Force manual verification

### 2. Core Flow Testing Script
```bash
#!/bin/bash
# test_core_flows.sh - MANDATORY before any commit

echo "🔍 Testing ALL core user flows..."

# Test 1: Free analysis flow
echo "Testing free analysis..."
if ! ./test_free_analysis.sh; then
    echo "❌ FREE ANALYSIS BROKEN - DO NOT COMMIT"
    exit 1
fi

# Test 2: Premium exports
echo "Testing premium exports..."
if ! ./test_premium_exports.sh; then
    echo "❌ PREMIUM EXPORTS BROKEN - DO NOT COMMIT" 
    exit 1
fi

# Test 3: JavaScript functions
echo "Testing JavaScript functions..."
if ! ./test_javascript_functions.sh; then
    echo "❌ JAVASCRIPT FUNCTIONS BROKEN - DO NOT COMMIT"
    exit 1
fi

echo "✅ All core flows working - safe to commit"
```

## CHANGE MANAGEMENT RULES

### Rule 1: NO DIRECT FUNCTION MOVES
**NEVER** move JavaScript functions without testing ALL templates that call them.

**Process**:
1. Grep for ALL onclick handlers: `grep -r "onclick.*=" app/templates/`
2. List ALL functions called by templates
3. Move ALL functions to global scope TOGETHER
4. Test ALL templates that use those functions

### Rule 2: NO TEMPLATE CHANGES WITHOUT CROSS-TEMPLATE TESTING
When changing one template, test ALL templates of the same type.

**Example**: If changing interview template, test:
- All interview exports
- All interview interactions  
- Resume exports still work
- Free analysis still works

### Rule 3: MANDATORY DOCUMENTATION UPDATES
Any change to UI patterns MUST update:
- `DESIGN_DECISIONS.md`
- `test_ui_regression.py`
- This SDLC document

## INCIDENT RESPONSE

### When Something Breaks (Again)
1. **STOP** - Don't make more changes
2. **ASSESS** - What broke? What flows are affected?
3. **FIX** - Fix the specific issue
4. **TEST** - Run ALL core flows
5. **DOCUMENT** - Update prevention measures
6. **COMMIT** - Only after everything passes

### When Tests Fail
1. **DO NOT BYPASS** tests with `--no-verify`
2. **FIX THE ISSUE** that's causing test failure
3. **RE-RUN TESTS** until they pass
4. **THEN COMMIT**

## EMERGENCY PROCEDURES

### Production Hotfix Process
1. **Assess impact** - What's broken in production?
2. **Create hotfix branch** from last known good commit
3. **Make MINIMAL fix** - Only the specific issue
4. **Test fix** - Run ALL core flows on hotfix
5. **Deploy hotfix**
6. **Post-mortem** - Why did this reach production?

### Rollback Criteria
**Immediate rollback if**:
- Free analysis stops working
- Payment flow breaks
- Any export function returns errors
- JavaScript ReferenceErrors in production

## TOOLS NEEDED

### Create These Scripts (URGENT)
```bash
# 1. Core flow testing
./create_test_scripts.sh

# 2. Function dependency mapping  
./map_function_dependencies.sh

# 3. Template cross-reference
./create_template_matrix.sh
```

## SUCCESS METRICS

### SDLC is working when:
- ✅ No new issues introduced in last 3 commits
- ✅ All tests pass consistently  
- ✅ Zero production hotfixes needed
- ✅ Developers follow checklist 100% of time

### SDLC is failing when:
- ❌ New issues appear after "fixes"
- ❌ Tests are bypassed or ignored
- ❌ Production requires emergency fixes
- ❌ Same issues reoccur

## COMMITMENT

**Every developer working on this codebase commits to**:
1. Following this SDLC process completely
2. Never bypassing tests or checklists
3. Testing ALL affected functionality before committing
4. Updating documentation when changing patterns
5. Stopping the fix-to-break cycle permanently

**This is not optional. This is how we work now.**

---

**Remember**: 5 minutes of testing prevents 5 hours of debugging broken production systems.