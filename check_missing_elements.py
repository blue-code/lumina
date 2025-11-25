#!/usr/bin/env python3
"""
Find missing HTML elements that JavaScript is trying to access
"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://127.0.0.1:15555')
    page.wait_for_load_state('networkidle')

    # List of IDs that JavaScript tries to access (from app.js setupEventListeners)
    expected_ids = [
        'btn-send',
        'btn-new-folder',
        'btn-new-request',
        'btn-clear-response',
        'btn-beautify-json',
        'btn-toggle-preview',
        'docs-markdown',
        'btn-more',
        'menu-import-insomnia',
        'menu-export-insomnia',
        'menu-clear-all',
        'btn-copy-url',
        'btn-delete-request',
        'btn-close-insomnia-import',
        'btn-cancel-insomnia-import',
        'btn-confirm-insomnia-import',
        'btn-close-insomnia-export',
        'btn-close-insomnia-export2',
        'btn-download-insomnia',
        'btn-copy-insomnia',
        'btn-close-import-insomnia',
        'btn-cancel-import-insomnia',
        'btn-confirm-import-insomnia',
        'insomnia-import-file',
        'btn-close-export-insomnia',
        'btn-close-export-insomnia2',
        'btn-copy-export-insomnia',
        'btn-download-export-insomnia',
        'btn-share-project',
        'btn-import-md',
        'btn-close-share',
        'btn-cancel-share',
        'btn-create-share',
        'btn-copy-share',
        'btn-close-import-share',
        'btn-cancel-import-share',
        'btn-confirm-import-share',
        'btn-global-constants',
        'btn-close-global-constants',
        'btn-cancel-global-constants',
        'btn-save-global-constants',
        'btn-add-global-constant',
        'project-dropdown',
        'btn-new-project',
        'btn-manage-projects',
        'btn-close-new-project',
        'btn-cancel-new-project',
        'btn-confirm-new-project',
        'btn-close-manage-projects',
        'btn-close-manage-projects2',
        'auth-type',
        'input-url',
        'select-method',
    ]

    print("Checking for missing elements...")
    print("=" * 80)

    missing = []
    found = []

    for element_id in expected_ids:
        exists = page.evaluate(f"document.getElementById('{element_id}') !== null")
        if not exists:
            missing.append(element_id)
            print(f"❌ MISSING: {element_id}")
        else:
            found.append(element_id)

    print("=" * 80)
    print(f"✓ Found: {len(found)}")
    print(f"❌ Missing: {len(missing)}")

    if missing:
        print("\nMissing elements:")
        for mid in missing:
            print(f"  - {mid}")

    browser.close()
