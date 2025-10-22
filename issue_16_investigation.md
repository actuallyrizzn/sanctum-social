# Issue #16 Investigation: Bot Detection Debugging

## Root Cause Analysis

After analyzing the bot detection code in `tools/bot_detection.py`, I've identified several potential causes for false positives:

### 1. **Handle Normalization Inconsistencies**

**Problem**: Lines 75-76 have inconsistent normalization logic:
```python
normalized_input_handles = [h.lstrip('@').strip() for h in handles]
normalized_bot_handles = [h.strip() for h in known_bot_handles]
```

**Issue**: Input handles get `@` stripped, but bot handles from parsing may still contain `@` symbols, causing mismatches.

### 2. **Parsing Logic Edge Cases**

**Problem**: Lines 67-72 have incomplete parsing logic:
```python
if line.startswith('- @'):
    handle = line[3:].split(':')[0].strip()
    known_bot_handles.append(handle)
elif line.startswith('-'):
    handle = line[1:].split(':')[0].strip().lstrip('@')
    known_bot_handles.append(handle)
```

**Issues**:
- Only handles lines starting with `- @` or `-` 
- Misses other common formats like `@handle.bsky.social` or `handle.bsky.social`
- No case-insensitive comparison
- No handling of special characters or whitespace variations

### 3. **Case Sensitivity**

**Problem**: No case-insensitive comparison in line 81:
```python
if handle in normalized_bot_handles:
```

**Issue**: `user.bsky.social` ≠ `User.bsky.social` ≠ `USER.bsky.social`

### 4. **Whitespace and Special Character Handling**

**Problem**: Insufficient whitespace normalization and no special character handling.

**Issues**:
- Handles with trailing spaces, tabs, or other whitespace
- Handles with special characters not properly normalized
- Unicode characters not handled

### 5. **Thread Handle Extraction Issues**

**Problem**: `extract_handles_from_thread()` may extract handles in different formats than expected.

**Issue**: Thread data might contain handles with different casing or formatting than the known_bots list.

## Proposed Solution

### Phase 1: Create Comprehensive Unit Tests
1. **Mock Data Testing**: Create test cases with various handle formats
2. **Edge Case Testing**: Test malformed handles, special characters, case variations
3. **Thread Data Testing**: Test handle extraction with mock thread structures

### Phase 2: Fix Normalization Logic
1. **Consistent Normalization**: Apply same normalization to both input and bot handles
2. **Case-Insensitive Comparison**: Convert all handles to lowercase for comparison
3. **Robust Parsing**: Handle multiple bot list formats
4. **Whitespace Handling**: Properly strip and normalize whitespace

### Phase 3: Enhanced Error Handling
1. **Detailed Logging**: Add debug logging for handle normalization steps
2. **Validation**: Validate handle formats before processing
3. **Fallback Logic**: Graceful handling of malformed data

### Phase 4: Testing and Validation
1. **Mock Bot Lists**: Test with various known_bots block formats
2. **Mock Thread Data**: Test with different thread structures
3. **Integration Testing**: Test full detection flow with mock data

## Implementation Plan

1. **Create `tests/unit/test_bot_detection.py`** with comprehensive test cases
2. **Refactor `check_known_bots()`** with improved normalization
3. **Add debug logging** for troubleshooting
4. **Test with mock data** to validate fixes
5. **Re-enable bot detection** in `bsky.py`

## Expected Outcome

- **Eliminate false positives** through proper handle normalization
- **Improve detection accuracy** with robust parsing logic
- **Add comprehensive test coverage** for bot detection functionality
- **Re-enable bot detection** with confidence in its accuracy

This approach allows us to debug and fix the bot detection logic without requiring live API keys or real data, using comprehensive mock testing instead.
