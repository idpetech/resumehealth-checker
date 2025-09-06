# Premium Options Flow Diagrams

## Current Implementation Analysis

### 1. Resume Analysis (Individual Product)
```
User Journey:
1. Upload Resume → Free Analysis → Display Results
2. Select "ATS Health Report" ($10) → Single Select
3. Click "Purchase Selected" → Show Loading
4. Create Payment Session → Redirect to Mock Payment
5. Mock Payment Success → Auto-redirect to Main App
6. URL Parameters: ?premium={analysis_id}&product=resume_analysis
7. Auto-detect Premium → Call displayPremiumResults()
8. Fetch Embedded Results → Display in Right Panel
```

### 2. Job Fit Analysis (Individual Product)
```
User Journey:
1. Upload Resume → Free Analysis → Display Results
2. Select "Job Match Analysis" ($12) → Single Select
3. Job Posting Field Appears → User Enters Job Posting
4. Click "Purchase Selected" → Show Loading
5. Create Payment Session → Redirect to Mock Payment
6. Mock Payment Success → Auto-redirect to Main App
7. URL Parameters: ?premium={analysis_id}&product=job_fit_analysis
8. Auto-detect Premium → Call displayPremiumResults()
9. Fetch Embedded Results → Display in Right Panel
```

### 3. Cover Letter (Individual Product)
```
User Journey:
1. Upload Resume → Free Analysis → Display Results
2. Select "AI Cover Letter" ($8) → Single Select
3. Job Posting Field Appears → User Enters Job Posting
4. Click "Purchase Selected" → Show Loading
5. Create Payment Session → Redirect to Mock Payment
6. Mock Payment Success → Auto-redirect to Main App
7. URL Parameters: ?premium={analysis_id}&product=cover_letter
8. Auto-detect Premium → Call displayPremiumResults()
9. Fetch Embedded Results → Display in Right Panel
```

### 4. Resume Enhancer (Individual Product)
```
User Journey:
1. Upload Resume → Free Analysis → Display Results
2. Select "Resume Enhancer" ($15) → Single Select
3. Job Posting Field Appears → User Enters Job Posting
4. Click "Purchase Selected" → Show Loading
5. Create Payment Session → Redirect to Mock Payment
6. Mock Payment Success → Auto-redirect to Main App
7. URL Parameters: ?premium={analysis_id}&product=resume_enhancer
8. Auto-detect Premium → Call displayPremiumResults()
9. Fetch Embedded Results → Display in Right Panel
```

## Bundle Options

### 5. Career Boost Bundle ($18)
```
User Journey:
1. Upload Resume → Free Analysis → Display Results
2. Select "Career Boost Bundle" → Single Select
3. Job Posting Field Appears → User Enters Job Posting
4. Click "Purchase Selected" → Show Loading
5. Create Payment Session → Redirect to Mock Payment
6. Mock Payment Success → Auto-redirect to Main App
7. URL Parameters: ?premium={analysis_id}&product=resume_analysis (first product)
8. Auto-detect Premium → Call displayPremiumResults()
9. Fetch Embedded Results → Display in Right Panel
```

### 6. Job Hunter Bundle ($15)
```
User Journey:
1. Upload Resume → Free Analysis → Display Results
2. Select "Job Hunter Bundle" → Single Select
3. Job Posting Field Appears → User Enters Job Posting
4. Click "Purchase Selected" → Show Loading
5. Create Payment Session → Redirect to Mock Payment
6. Mock Payment Success → Auto-redirect to Main App
7. URL Parameters: ?premium={analysis_id}&product=resume_analysis (first product)
8. Auto-detect Premium → Call displayPremiumResults()
9. Fetch Embedded Results → Display in Right Panel
```

### 7. Complete Package ($22)
```
User Journey:
1. Upload Resume → Free Analysis → Display Results
2. Select "Complete Package" → Single Select
3. Job Posting Field Appears → User Enters Job Posting
4. Click "Purchase Selected" → Show Loading
5. Create Payment Session → Redirect to Mock Payment
6. Mock Payment Success → Auto-redirect to Main App
7. URL Parameters: ?premium={analysis_id}&product=resume_analysis (first product)
8. Auto-detect Premium → Call displayPremiumResults()
9. Fetch Embedded Results → Display in Right Panel
```

## Current Issues Identified

### Issue 1: Bundle Delivery
- **Problem**: Bundles only show the first product's results
- **Current**: Complete Package shows only Resume Analysis
- **Expected**: Should show all products in bundle (Resume Analysis + Job Fit + Cover Letter)

### Issue 2: Bundle Selection Logic
- **Problem**: Bundle selection uses first product type for payment session
- **Current**: All bundles use `resume_analysis` as product_type
- **Expected**: Should handle multiple products in bundle

### Issue 3: Premium Results Display
- **Problem**: Only one product result is displayed
- **Current**: Single product result in right panel
- **Expected**: For bundles, should show multiple results or combined view

### Issue 4: Job Posting Requirements
- **Problem**: Job posting field appears for all products that need it
- **Current**: Field appears for individual products
- **Expected**: Should also appear for bundles that include job-posting-required products

## Recommended Workflow Improvements

### For Individual Products:
1. ✅ Single select works correctly
2. ✅ Job posting field appears when needed
3. ✅ Payment flow works correctly
4. ✅ Premium results display in right panel
5. ✅ Loading indicators work correctly

### For Bundle Products:
1. ❌ Need to handle multiple products in bundle
2. ❌ Need to show all bundle results
3. ❌ Need to handle job posting for all relevant products
4. ❌ Need to create multiple premium results
5. ❌ Need to display combined or multiple results

## Technical Implementation Needed

### Backend Changes:
1. **Bundle Processing**: Modify payment session to handle multiple products
2. **Multiple Results**: Generate results for all products in bundle
3. **Bundle Storage**: Store multiple premium results for bundle purchases
4. **Bundle Display**: Create combined view for bundle results

### Frontend Changes:
1. **Bundle Selection**: Update selection logic to handle bundles properly
2. **Bundle Display**: Create UI to show multiple results
3. **Bundle Navigation**: Allow users to view different products in bundle
4. **Bundle Pricing**: Show correct bundle pricing and savings

## Next Steps

1. **Identify Bundle Requirements**: What should bundles deliver?
2. **Design Bundle UI**: How should multiple results be displayed?
3. **Implement Bundle Logic**: Backend changes for multiple products
4. **Test Bundle Flow**: End-to-end testing of bundle purchases
5. **Optimize User Experience**: Make bundle flow intuitive and clear

