# File Verification Protocol

**Purpose**: Ensure AI can always access and verify GitHub repository files
**Status**: ACTIVE - Required for all file operations
**Last Updated**: 2025-11-02

---

## 🎯 THE PROBLEM WE SOLVED

Previously, AI would:
- Create files and ask user to upload
- NEVER verify it could read them back
- Assume files were accessible
- Result: Broken feedback loop

Now, AI must:
- Verify every file after upload
- Confirm it can read file contents
- Update catalog with verified status
- Document verification in prompt

---

## ✅ THE VERIFICATION METHOD

### **How It Works:**

1. **AI constructs raw GitHub URL:**
   ```
   https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/[FILE_PATH]
   ```

2. **AI posts URL and requests verification:**
   ```
   "Please paste this URL back to me:
   https://raw.githubusercontent.com/..."
   ```

3. **User pastes URL back:**
   ```
   https://raw.githubusercontent.com/...
   ```

4. **AI fetches and reads file:**
   ```
   web_fetch(url)
   ```

5. **AI confirms verification:**
   ```
   "✅ Verified! File contains X lines, Y functions..."
   ```

---

## 📋 MANDATORY VERIFICATION WORKFLOW

### **When AI Creates New File(s):**

**Step 1: AI Provides Files & Posts to Catalog**
```
AI creates the file(s) with download links
AI provides file information:
  - File name
  - Location/path
  - Purpose
  - Key contents (lines, functions, etc.)
AI immediately updates GITHUB_FILE_CATALOG.md with ⚠️ PENDING VERIFICATION status
```

**Step 2: AI Constructs & Posts URLs**
```
AI constructs raw GitHub URL(s):
  https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/[FILE_PATH]

AI posts URL(s) in chat in plain text format for easy copying
AI says: "To verify, copy these URLs and paste them back after upload:"
```

**Step 3: User Uploads & Pastes URLs Back**
```
User downloads files from chat
User uploads/updates files to GitHub in correct locations
User copies the URL(s) AI provided
User pastes URL(s) back in chat
```

**Step 4: AI Verifies Files**
```
AI uses web_fetch on each pasted URL
AI reads and confirms file contents
AI responds:
  "✅ VERIFIED: [filename]
   - [key details: lines, functions, data]
   - Status: Accessible and ready to use"

AI updates GITHUB_FILE_CATALOG.md with ✅ VERIFIED status
AI updates CURRENT_CATCHUP_PROMPT.md if needed
```

---

## 🚫 WHAT AI CANNOT DO

AI **CANNOT**:
- ❌ Directly fetch raw.githubusercontent.com URLs without user providing them first
- ❌ Use web_search to reliably find specific files in the repo
- ❌ Assume files are accessible without verification

AI **CAN**:
- ✅ Construct the URL format
- ✅ Request user to paste URL back
- ✅ Fetch URLs that user provides
- ✅ Read and verify file contents

---

## 📝 FILE CATALOG FORMAT

### **Before Verification:**
```markdown
- [backup_system.py](TBD) ⚠️ PENDING VERIFICATION
  - Purpose: Backup management
  - Status: Awaiting verification
```

### **After Verification:**
```markdown
- [backup_system.py](https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/Verified_Backtest_Data/backup_system.py) ✅ VERIFIED
  - Purpose: Backup management
  - Verified: 2025-11-02
  - Lines: 150
  - Status: Accessible
```

---

## 🔄 VERIFICATION CHECKLIST

For EVERY file created or updated:

- [ ] AI creates file(s) with download links
- [ ] AI provides file information (location, purpose, contents)
- [ ] AI updates GITHUB_FILE_CATALOG.md with ⚠️ PENDING status
- [ ] AI constructs raw GitHub URL(s)
- [ ] AI posts URL(s) in chat for user to copy
- [ ] User downloads files
- [ ] User uploads files to GitHub
- [ ] User copies URL(s) from chat
- [ ] User pastes URL(s) back in chat
- [ ] AI fetches URL(s) using web_fetch
- [ ] AI reads and confirms file contents
- [ ] AI updates GITHUB_FILE_CATALOG.md with ✅ VERIFIED status
- [ ] AI updates CURRENT_CATCHUP_PROMPT.md (if needed)

**NO EXCEPTIONS.**

---

## 📊 VERIFICATION TRACKING

Track verification status in system_state.json:

```json
{
  "file_verification": {
    "total_files": 50,
    "verified_files": 45,
    "pending_files": 5,
    "last_verification_date": "2025-11-02",
    "verification_rate": "90%"
  }
}
```

---

## 🎯 SUCCESS CRITERIA

A file verification is **SUCCESSFUL** when:

1. ✅ AI can fetch the URL
2. ✅ AI can read file contents
3. ✅ AI confirms key contents (lines, functions, data)
4. ✅ File added to catalog with verified link
5. ✅ Catch-up prompt updated with verification

A file verification is **FAILED** when:

1. ❌ AI cannot fetch URL (404, timeout, etc.)
2. ❌ AI cannot read contents (encoding issues)
3. ❌ File contents don't match expectations

---

## 🚨 CRITICAL REMINDERS

1. **NEVER assume files are accessible** - Always verify
2. **NEVER skip verification steps** - Every file, every time
3. **ALWAYS update catalog after verification** - Keep it current
4. **ALWAYS update catch-up prompt** - Future AI needs this info
5. **User must paste URL back** - AI cannot fetch directly without it

---

## 📖 EXAMPLES

### **Example 1: Verifying New Script**

**AI:**
```
I've created explosive_stock_scanner.py:
- Location: Root directory
- Purpose: Scans for 500%+ explosive stocks over 10 years
- Lines: 450
- Functions: ExplosiveStockScanner class, scan_year(), save_results()
- Data sources: Polygon API + Yahoo Finance

[Download link provided]

Updated GITHUB_FILE_CATALOG.md with pending verification.

To verify, copy this URL and paste it back after upload:

https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/explosive_stock_scanner.py
```

**User:**
```
[uploads file to GitHub]
https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/explosive_stock_scanner.py
```

**AI:**
```
✅ VERIFIED: explosive_stock_scanner.py
- 450 lines of Python
- Functions: ExplosiveStockScanner class, scan_year(), save_results()
- Data source: Polygon API + Yahoo Finance
- Status: Ready to use

Updated GITHUB_FILE_CATALOG.md with verified status.
```

### **Example 2: Verifying Data File**

**AI:**
```
I've created explosive_stocks_CLEAN.json:
- Location: /Verified_Backtest_Data/
- Purpose: Clean dataset for pattern analysis (excludes COVID-era)
- Contains: 170 explosive stocks
- Period: 2014-2019, 2022-2024
- Top gainer: ABVC (+416,567%)

[Download link provided]

Updated GITHUB_FILE_CATALOG.md with pending verification.

To verify, copy this URL and paste it back after upload:

https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/Verified_Backtest_Data/explosive_stocks_CLEAN.json
```

**User:**
```
[uploads file to GitHub]
https://raw.githubusercontent.com/cbenson85/GEM_Trading_System/refs/heads/main/Verified_Backtest_Data/explosive_stocks_CLEAN.json
```

**AI:**
```
✅ VERIFIED: explosive_stocks_CLEAN.json
- Contains: 170 explosive stocks
- Period: 2014-2019, 2022-2024 (COVID-era excluded)
- Top gainer: ABVC (+416,567%)
- Status: Ready for analysis

Updated GITHUB_FILE_CATALOG.md with verified status.
```

---

## 🔧 TROUBLESHOOTING

### **Problem: AI tries to fetch URL before user pastes it**

**Solution:** AI must wait for user to paste URL back. Cannot fetch directly.

### **Problem: URL returns 404**

**Possible causes:**
- File not uploaded yet
- Wrong file path
- Wrong branch (should be 'main')

**Solution:** 
- Verify user uploaded file
- Check file path is correct
- Confirm branch is 'main' not 'master'

### **Problem: File encoding issues**

**Solution:**
- Use UTF-8 encoding for all text files
- Binary files may not display but can be confirmed present

---

## 📈 BENEFITS

This protocol ensures:

✅ **Zero broken links** - All catalog links work
✅ **Complete visibility** - AI knows what exists
✅ **No wasted prompts** - AI doesn't search for files
✅ **Full continuity** - New AI sessions have access
✅ **Quality control** - Files are verified correct
✅ **Audit trail** - Track what was verified when

---

## 🎓 KEY PRINCIPLE

**"If AI created it, AI must verify it."**

No file is considered "uploaded" or "accessible" until:
1. User confirms upload
2. User provides URL
3. AI fetches and reads it
4. AI updates catalog
5. AI updates catch-up prompt

**This is the standard. No exceptions.**

---

**END OF FILE VERIFICATION PROTOCOL**

Status: ACTIVE and MANDATORY
Last Updated: 2025-11-02
Next Review: As needed

Status: ACTIVE and MANDATORY
Last Updated: 2025-11-02
Next Review: As needed
