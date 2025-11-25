#!/usr/bin/env python3
"""
Test Insomnia import functionality
"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Capture console logs
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda exc: console_logs.append(f"[ERROR] {exc}"))

    print("Testing Insomnia Import...")
    page.goto('http://127.0.0.1:15555')
    page.wait_for_load_state('networkidle')
    time.sleep(1)

    # Open More Menu
    print("1. Opening More Menu...")
    page.click('#btn-more')
    time.sleep(0.5)

    # Click Import Insomnia
    print("2. Clicking Import Insomnia...")
    page.click('#menu-import-insomnia')
    time.sleep(0.5)

    # Check if modal opened
    modal = page.locator('#import-insomnia-modal')
    has_active_class = 'active' in (modal.get_attribute('class') or '')

    print(f"3. Import Insomnia Modal opened: {has_active_class}")

    if has_active_class:
        # Check modal contents
        print("4. Checking modal contents...")

        file_input = page.locator('#insomnia-import-file')
        print(f"   - File input exists: {file_input.count() > 0}")

        preview = page.locator('#import-insomnia-preview')
        print(f"   - Preview div exists: {preview.count() > 0}")

        confirm_btn = page.locator('#btn-confirm-import-insomnia')
        print(f"   - Confirm button exists: {confirm_btn.count() > 0}")
        print(f"   - Confirm button disabled: {confirm_btn.is_disabled()}")

    # Show console logs
    if console_logs:
        print("\nConsole logs:")
        for log in console_logs:
            print(f"   {log}")

    browser.close()
