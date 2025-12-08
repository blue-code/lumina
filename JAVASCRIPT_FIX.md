# Quick Fix for JavaScript Errors

## Problem
The JavaScript tries to access buttons that don't exist in the HTML:
- `btn-import-md` (removed from UI)
- `btn-export-md` (not in current HTML)
- Various other import/export buttons
- History elements that may not exist

## Solution

Replace lines 50-93 in `web/static/js/app.js` with this code that uses optional chaining:

```javascript
        // Docs 변경 감지
        document.getElementById('docs-markdown').addEventListener('input', () => {
            this.saveCurrentRequest();
        });

        // Import/Export 버튼 - Using optional chaining to prevent errors
        document.getElementById('btn-import-md')?.addEventListener('click', () => this.showImportModal());
        document.getElementById('btn-export-md')?.addEventListener('click', () => this.showExportModal());

        // Import Modal
        document.getElementById('btn-close-import')?.addEventListener('click', () => this.hideImportModal());
        document.getElementById('btn-cancel-import')?.addEventListener('click', () => this.hideImportModal());
        document.getElementById('btn-confirm-import')?.addEventListener('click', () => this.importMarkdown());

        // Export Modal
        document.getElementById('btn-close-export')?.addEventListener('click', () => this.hideExportModal());
        document.getElementById('btn-close-export2')?.addEventListener('click', () => this.hideExportModal());
        document.getElementById('btn-copy-export')?.addEventListener('click', () => this.copyExportToClipboard());

        // Insomnia Import/Export 버튼
        document.getElementById('btn-import-insomnia')?.addEventListener('click', () => this.showImportInsomniaModal());
        document.getElementById('btn-export-insomnia')?.addEventListener('click', () => this.showExportInsomniaModal());

        // Import Insomnia Modal
        document.getElementById('btn-close-import-insomnia')?.addEventListener('click', () => this.hideImportInsomniaModal());
        document.getElementById('btn-cancel-import-insomnia')?.addEventListener('click', () => this.hideImportInsomniaModal());
        document.getElementById('btn-confirm-import-insomnia')?.addEventListener('click', () => this.importInsomnia());
        document.getElementById('import-insomnia-file')?.addEventListener('change', (e) => this.onInsomniaFileSelected(e));

        // Export Insomnia Modal
        document.getElementById('btn-close-export-insomnia')?.addEventListener('click', () => this.hideExportInsomniaModal());
        document.getElementById('btn-close-export-insomnia2')?.addEventListener('click', () => this.hideExportInsomniaModal());
        document.getElementById('btn-copy-export-insomnia')?.addEventListener('click', () => this.copyExportInsomniaToClipboard());
        document.getElementById('btn-download-export-insomnia')?.addEventListener('click', () => this.downloadExportInsomina());

        // Share 버튼
        document.getElementById('btn-share-project')?.addEventListener('click', () => this.showShareModal());
        document.getElementById('btn-import-share')?.addEventListener('click', () => this.showImportShareModal());

        // Share Modal
        document.getElementById('btn-close-share')?.addEventListener('click', () => this.hideShareModal());
        document.getElementById('btn-cancel-share')?.addEventListener('click', () => this.hideShareModal());
        document.getElementById('btn-create-share')?.addEventListener('click', () => this.createShare());
        document.getElementById('btn-copy-share')?.addEventListener('click', () => this.copyShareURL());

        // Import Share Modal
        document.getElementById('btn-close-import-share')?.addEventListener('click', () => this.hideImportShareModal());
        document.getElementById('btn-cancel-import-share')?.addEventListener('click', () => this.hideImportShareModal());
        document.getElementById('btn-confirm-import-share')?.addEventListener('click', () => this.importShare());
```

The key change: **Adding `?.` (optional chaining)** to all `getElementById` calls. This makes the event listener only attach if the element exists, preventing errors.

Also update lines 820-824 to add null checks:

```javascript
                const inputList = document.getElementById('history-input-list');
                const outputList = document.getElementById('history-output-list');
                
                if (inputList) {
                    inputList.innerHTML =
                        '<p class="history-empty">No history yet. Send a request to start tracking!</p>';
                }
                if (outputList) {
                    outputList.innerHTML =
                        '<p class="history-empty">No response history yet. Send a request to see responses!</p>';
                }
```

## Apply Instruction

Due to file editing issues, please manually apply these changes:

1. Open `web/static/js/app.js`
2. Find line 51 (`document.getElementById('btn-import-md').addEventListener`)
3. Add `?` after every `getElementById` call until line 93
4. Find line 820 and replace the direct `innerHTML` assignments with the null-checked version above
5. Save and refresh browser

This will fix all JavaScript errors!
