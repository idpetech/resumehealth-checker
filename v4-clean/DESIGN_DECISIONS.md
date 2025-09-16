# Design & UI Decisions Documentation

## Purpose
This document captures critical design decisions, UI patterns, and implementation choices to prevent regressions and maintain consistency across sprints.

## Core UI/UX Principles

### 1. Export Functionality Standards
**Decision**: All export functions (PDF, DOCX) must capture complete content regardless of current UI state.

**Implementation Requirements**:
- Interview templates: Auto-expand all questions during export, then restore original state
- Resume rewrite templates: Exclude analysis sections from resume exports
- All templates: Hide interactive elements (buttons, expand icons) during capture
- State restoration: Always restore original DOM state in success AND error cases

**Files Affected**: `app/static/index.html` (exportToPDFClient, exportToWord, copyToClipboard functions)

### 2. JavaScript Scoping Pattern
**Decision**: AJAX-loaded template JavaScript functions must be available in global scope.

**Implementation**:
- Critical functions defined in main `index.html` rather than embedded templates
- Template-specific functions (toggleQuestion, toggleAllQuestions, exportToWord, copyToClipboard) moved to global scope
- Use feature detection to determine template type and apply appropriate logic

**Rationale**: AJAX-loaded content script tags don't execute properly, causing ReferenceErrors

### 3. Interview Question Interaction Pattern
**Decision**: Expand All button uses `.every()` logic, not `.some()` logic.

**Implementation**:
```javascript
const allExpanded = Array.from(allDetails).every(detail => 
    detail.style.display === 'block'
);
```

**Rationale**: Users expect "Expand All" to mean ALL questions, not just checking if ANY are expanded

### 4. Resume Export Content Separation
**Decision**: Resume exports contain ONLY resume content, never analysis metadata.

**Implementation**:
- PDF Export: Temporarily hide `.analysis-section` during capture
- DOCX Export: Remove `.analysis-section` from cloned content
- Page breaks: Analysis stays on separate pages when displayed in UI

## Technical Implementation Patterns

### 1. State Management for Exports
```javascript
// Pattern: Store original states before modification
let originalStates = [];
elements.forEach((element, index) => {
    originalStates[index] = element.style.display;
    element.style.display = 'desired_state';
});

// Pattern: Always restore in finally blocks
try {
    // export logic
} finally {
    // restore original states
    elements.forEach((element, index) => {
        element.style.display = originalStates[index];
    });
}
```

### 2. Template Detection Pattern
```javascript
// Pattern: Feature detection over hardcoded checks
const isInterviewTemplate = document.querySelectorAll('[id^="details-"]').length > 0;
const isResumeRewrite = document.querySelector('.analysis-section') !== null;

if (isInterviewTemplate) {
    // interview-specific logic
} else if (isResumeRewrite) {
    // resume-specific logic
}
```

### 3. Error Handling Pattern
```javascript
// Pattern: Consistent error handling across all export functions
try {
    // main logic
} catch (error) {
    console.error('Function error:', error);
    alert('❌ Error message: ' + error.message);
    // restoration logic here too
}
```

## File Organization Standards

### 1. JavaScript Function Location
- **Global functions**: `app/static/index.html` - for functions called from AJAX content
- **Template-specific functions**: Keep in templates only if they're never called from other contexts
- **Shared utilities**: Consider extracting to separate JS file if functions grow large

### 2. CSS Class Naming Conventions
- **Functional classes**: `.analysis-section` - semantic, describes purpose
- **State classes**: `.expanded` - describes current state
- **Interactive classes**: `.expand-all-btn` - describes user interaction

### 3. Template Structure Standards
- **Page break elements**: Use `style="page-break-before: always;"` for PDF export control
- **Export exclusion**: Wrap analysis content in `.analysis-section` for easy removal
- **Interactive elements**: Always use consistent classes for buttons and controls

## Testing Requirements

### 1. Export Function Testing
Before any release, verify:
- [ ] Interview PDF export shows all questions expanded
- [ ] Interview DOCX export shows all questions expanded  
- [ ] Resume PDF export excludes analysis section
- [ ] Resume DOCX export excludes analysis section
- [ ] UI state is restored after export (collapsed questions stay collapsed)
- [ ] Error cases don't leave DOM in broken state

### 2. JavaScript Function Testing
Before any release, verify:
- [ ] toggleAllQuestions works from interview templates
- [ ] exportToWord works from all templates that have the button
- [ ] exportToPDFClient works from all templates that have the button
- [ ] No ReferenceError exceptions in browser console

### 3. Cross-Template Consistency
Before any release, verify:
- [ ] All templates use consistent button classes and onclick handlers
- [ ] All templates load required JavaScript libraries (jsPDF, html2canvas)
- [ ] All templates follow the same styling patterns

## Sprint Handoff Checklist

### For Next Developer/Sprint:
1. **Read this document first** - understand existing decisions before making changes
2. **Test existing functionality** - run the testing checklist above
3. **Update this document** - when making new design decisions, add them here
4. **Preserve patterns** - follow established patterns rather than creating new ones
5. **Document deviations** - if you must break a pattern, document why

### Before Making Changes:
1. **Impact assessment** - will this change affect other templates?
2. **Pattern consistency** - does this follow established patterns?
3. **Testing plan** - how will you verify the change doesn't break existing functionality?
4. **Documentation update** - what needs to be added to this document?

## Common Pitfalls to Avoid

### 1. ❌ Don't: Move JavaScript functions back to templates
**Why**: AJAX-loaded content causes ReferenceErrors
**Do**: Keep functions in global scope in `index.html`

### 2. ❌ Don't: Change export logic without considering all template types
**Why**: A change for interviews might break resume exports
**Do**: Use template detection and type-specific logic

### 3. ❌ Don't: Skip state restoration in error cases
**Why**: Leaves UI in broken state for users
**Do**: Always restore in both success and error paths

### 4. ❌ Don't: Hardcode template assumptions
**Why**: Breaks when new templates are added
**Do**: Use feature detection (check for specific elements/classes)

### 5. ❌ Don't: Forget to move ALL called functions to global scope
**Why**: Free analysis buttons will break (copyToClipboard, exportToPDFClient, etc.)
**Do**: When moving functions to global scope, grep for ALL onclick handlers in ALL templates

## Version History

### v4.1.0 (2025-09-16) - Export Function Standardization
- Established export content standards
- Fixed interview question expansion during exports
- Fixed resume/analysis content separation
- Standardized JavaScript scoping for AJAX content
- **CRITICAL FIX**: Added copyToClipboard to global scope (fixes free analysis buttons)
- Created this documentation

### Future Versions
- Add automated testing for export functions
- Consider extracting large JavaScript functions to separate files
- Implement automated regression testing

---

**Remember**: This document is living documentation. Update it when you make significant design decisions or changes to UI patterns.