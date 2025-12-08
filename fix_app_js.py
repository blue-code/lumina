"""
Simple fix to add null safety checks to app.js
Run this script to apply all fixes at once
"""

import re

# Read the file
with open('web/static/js/app.js', '

r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Add optional chaining to all getElementById event listeners (lines 50-93)
# Find and replace event listener assignments
content = re.sub(
    r'document\.getElementById\(([^)]+)\)\.addEventListener',
    r'document.getElementById(\1)?.addEventListener',
    content
)

# Fix 2: Add null check to renderResponseHeaders
content = re.sub(
    r'(renderResponseHeaders\(headers\) \{[\s\r\n]+const tbody = document\.getElementById\(\'response-headers-tbody\'\);[\s\r\n]+)(tbody\.innerHTML)',
    r'\1if (!tbody) return; // Element doesn\'t exist\n        \n        \2',
    content,
    flags=re.MULTILINE
)

# Fix 3: Add null check to renderInputHistory
content = re.sub(
    r'(renderInputHistory\(history\) \{[\s\r\n]+const historyList = document\.getElementById\(\'history-input-list\'\);[\s\r\n]+)(historyList\.innerHTML)',
    r'\1if (!historyList) return; // Element doesn\'t exist\n        \n        \2',
    content,
    flags=re.MULTILINE
)

# Fix 4: Add null check to renderOutputHistory  
content = re.sub(
    r'(renderOutputHistory\(history\) \{[\s\r\n]+const historyList = document\.getElementById\(\'history-output-list\'\);[\s\r\n]+)(historyList\.innerHTML)',
    r'\1if (!historyList) return; // Element doesn\'t exist\n        \n        \2',
    content,
    flags=re.MULTILINE
)

# Write the fixed content
with open('web/static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed app.js successfully!")
print("All null safety checks added.")
