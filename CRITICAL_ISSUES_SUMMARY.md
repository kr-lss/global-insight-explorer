# Critical Issues - Quick Reference

## Issue #1: BROKEN popup.js - Undefined Variables (CRITICAL)

**File:** `/home/user/global-insight-explorer/frontend/popup.js`

**Lines with undefined variables:**
- Line 90: `findSourcesBtn.disabled = true;` - ERROR: findSourcesBtn not declared
- Line 125: `findSourcesBtn.disabled = false;` - ERROR: findSourcesBtn not declared
- Line 189: `sourcesResultsDiv.innerHTML = '';` - ERROR: sourcesResultsDiv not declared
- Line 297: `sourcesResultsDiv.appendChild(resultEl);` - ERROR: sourcesResultsDiv not declared
- Line 323: `sourcesResultsDiv.appendChild(guideEl);` - ERROR: sourcesResultsDiv not declared

**Why it happens:**
- popup.html only has #factCheckResults (line 30), NOT sourcesResultsDiv
- popup.js was copied from main.js without removing fact-check functionality
- main.html has all elements (#factCheckBtn, #factCheckResults)
- popup.html only has minimal elements

**Impact:** 
User clicks "Fact-Check Selected Claims" button → JavaScript throws ReferenceError → Feature completely broken

**Fix (choose one):**

### Option A: Add missing elements to popup.html
```html
<!-- In popup.html, after line 29, add: -->
<button id="findSourcesBtn">Find Sources</button>
<div id="sourcesResultsDiv"></div>
```

### Option B: Remove fact-check from popup.js
Delete or comment out the fact-check button event listener (lines 77-127) from popup.js

---

## Issue #2: API URL Hardcoded - Won't Work in Production (HIGH)

**File:** `/home/user/global-insight-explorer/frontend/main.js`

**Lines 21-23:**
```javascript
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://127.0.0.1:8080'
  : 'http://127.0.0.1:8080'; // PROBLEM: Same URL in both branches!
```

**Problem:**
- Comment says "프로덕션 환경에서는 실제 서버 주소로 변경" but doesn't change
- Returns `http://127.0.0.1:8080` for BOTH localhost AND production
- Will fail when deployed to production server

**Fix:**
```javascript
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://127.0.0.1:8080'
  : `${window.location.protocol}//${window.location.hostname}:${window.location.port || 443}`;
```

Or use environment variable:
```javascript
const API_BASE_URL = window.API_BASE_URL || 'http://127.0.0.1:8080';
```

**Also affects:** `/home/user/global-insight-explorer/frontend/popup.js` line 13
```javascript
const API_BASE_URL = 'http://127.0.0.1:8080'; // Hard-coded, no flexibility
```

---

## Issue #3: Broken Query Selector in popup.js (HIGH)

**File:** `/home/user/global-insight-explorer/frontend/popup.js`

**Line 80:**
```javascript
const selectedClaims = Array.from(
  document.querySelectorAll('#keyClaims input:checked')  // WRONG!
).map(input => input.value);
```

**Problem:**
- Selects ALL checked inputs, not just checkboxes
- Will also select checked radio buttons
- Correct version in main.js line 139 uses: `#keyClaims input[type="checkbox"]:checked`

**Fix:**
```javascript
const selectedClaims = Array.from(
  document.querySelectorAll('#keyClaims input[type="checkbox"]:checked')
).map(input => input.value);
```

---

## Issue #4: No Input Validation on API Parameters (MEDIUM)

**File:** `/home/user/global-insight-explorer/app/routes/history.py`

**Lines 20, 43:**
```python
# Line 20 in recent_history()
limit = int(request.args.get('limit', 20))  # No max check!

# Line 43 in popular_content()
days = int(request.args.get('days', 7))  # No validation!
```

**Problem:**
- User could request `limit=999999` → Performance DoS
- User could request `days=-100` → Unexpected behavior
- No bounds enforcement

**Fix:**
```python
# In history.py routes
def recent_history():
    limit = min(int(request.args.get('limit', 20)), 100)  # Max 100
    input_type = request.args.get('type', None)
    
def popular_content():
    limit = min(int(request.args.get('limit', 10)), 100)  # Max 100
    days = max(0, int(request.args.get('days', 7)))       # Non-negative
```

---

## Issue #5: Magic Numbers in Python Code (MEDIUM)

**File:** `/home/user/global-insight-explorer/app/utils/analysis_service.py`

**Lines 74, 207:**
```python
content = content[:8000]  # Line 74 - What's special about 8000?
original_content = original_content[:4000]  # Line 207 - Why 4000?
```

**Problem:**
- No explanation for these values
- Different limits with no justification
- Hard to modify for tuning

**Fix:**
```python
# In config.py, add:
MAX_CONTENT_LENGTH_FIRST_ANALYSIS = 8000
MAX_CONTENT_LENGTH_SECOND_ANALYSIS = 4000

# In analysis_service.py:
content = content[:config.MAX_CONTENT_LENGTH_FIRST_ANALYSIS]
original_content = original_content[:config.MAX_CONTENT_LENGTH_SECOND_ANALYSIS]
```

---

## Quick Fix Priority List

### Must Fix (Blocks functionality):
1. popup.js undefined variables (CRITICAL)
2. API URL hardcoding (HIGH)
3. Query selector bug in popup.js (HIGH)

### Should Fix (Security/Performance):
4. Input validation on API parameters (MEDIUM)
5. Magic numbers in analysis_service.py (MEDIUM)

### Nice to Fix (Code quality):
6. Duplicate code between main.js and popup.js
7. Silent error handling in history loading
8. No request throttling/debouncing

---

## Testing After Fixes

```bash
# Test popup.js fixes
1. Open Chrome DevTools (F12)
2. Click "Fact-Check Selected Claims"
3. Check Console for ReferenceError - should be NONE

# Test API URL fix
1. Deploy to production domain
2. Open app
3. Check Network tab - requests should go to production API

# Test input validation fix
1. Open DevTools Console
2. Manually call: fetch('http://localhost:8080/api/history/popular?limit=999999')
3. Should limit to 100 results, not 999999
```

---

## Files Affected

### Frontend (JavaScript)
- `/home/user/global-insight-explorer/frontend/main.js` - API URL logic bug
- `/home/user/global-insight-explorer/frontend/popup.js` - Undefined variables & broken selector
- `/home/user/global-insight-explorer/frontend/popup.html` - Missing elements

### Backend (Python)
- `/home/user/global-insight-explorer/app/routes/history.py` - No input validation
- `/home/user/global-insight-explorer/app/utils/analysis_service.py` - Magic numbers
- `/home/user/global-insight-explorer/app/config.py` - Add config constants

