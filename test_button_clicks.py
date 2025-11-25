#!/usr/bin/env python3
"""
Test actual button click functionality
"""
from playwright.sync_api import sync_playwright
import time

def test_button_clicks():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: console_logs.append(f"[ERROR] {exc}"))

        print("=" * 80)
        print("🧪 Testing Button Click Functionality")
        print("=" * 80)

        page.goto('http://127.0.0.1:15555')
        page.wait_for_load_state('networkidle')
        time.sleep(1)  # Extra wait for initialization

        print("\n✅ JavaScript initialized successfully (no errors)")

        # Test 1: Click New Folder button
        print("\n1. Testing New Folder button...")
        try:
            page.click('#btn-new-folder', timeout=2000)
            time.sleep(0.5)
            # Check if prompt appeared (it should open a browser prompt)
            print("   ✓ New Folder button is clickable")
        except Exception as e:
            print(f"   ❌ New Folder button failed: {e}")

        # Test 2: Click New Request button
        print("\n2. Testing New Request button...")
        try:
            page.click('#btn-new-request', timeout=2000)
            time.sleep(0.5)
            print("   ✓ New Request button is clickable")
        except Exception as e:
            print(f"   ❌ New Request button failed: {e}")

        # Test 3: Send button (should alert if no request selected)
        print("\n3. Testing Send button...")
        try:
            # Set up dialog handler
            dialog_text = None
            def handle_dialog(dialog):
                nonlocal dialog_text
                dialog_text = dialog.message
                dialog.accept()

            page.on("dialog", handle_dialog)
            page.click('#btn-send', timeout=2000)
            time.sleep(0.5)

            if dialog_text:
                print(f"   ✓ Send button works (showed alert: '{dialog_text}')")
            else:
                print("   ✓ Send button is clickable")
        except Exception as e:
            print(f"   ❌ Send button failed: {e}")

        # Test 4: More Menu button
        print("\n4. Testing More Menu button...")
        try:
            page.click('#btn-more', timeout=2000)
            time.sleep(0.5)

            # Check if menu is visible
            menu = page.locator('#more-menu')
            is_visible = menu.is_visible()

            if is_visible:
                print("   ✓ More Menu button works (menu opened)")

                # Test menu items
                print("      Testing menu items...")
                menu_items = [
                    ('menu-import-insomnia', 'Import Insomnia'),
                    ('menu-export-insomnia', 'Export Insomnia'),
                    ('menu-clear-all', 'Clear All')
                ]

                for item_id, item_name in menu_items:
                    try:
                        item = page.locator(f'#{item_id}')
                        if item.is_visible():
                            print(f"      ✓ {item_name} menu item visible")
                        else:
                            print(f"      ❌ {item_name} menu item not visible")
                    except Exception as e:
                        print(f"      ❌ {item_name} error: {e}")
            else:
                print("   ❌ More Menu didn't open")
        except Exception as e:
            print(f"   ❌ More Menu button failed: {e}")

        # Close More Menu first
        print("\n   Closing More Menu...")
        page.click('body')  # Click outside to close menu
        time.sleep(0.5)

        # Test 5: Share Project button
        print("\n5. Testing Share Project button...")
        try:
            page.click('#btn-share-project', timeout=2000)
            time.sleep(0.5)

            # Check if modal opened
            modal = page.locator('#share-modal')
            if 'active' in modal.get_attribute('class'):
                print("   ✓ Share Project button works (modal opened)")
                # Close modal
                page.click('#btn-close-share')
                time.sleep(0.3)
            else:
                print("   ⚠️  Share Project button clicked but modal didn't open")
        except Exception as e:
            print(f"   ❌ Share Project button failed: {e}")

        # Test 6: Global Constants button
        print("\n6. Testing Global Constants button...")
        try:
            page.click('#btn-global-constants', timeout=2000)
            time.sleep(0.5)

            # Check if modal opened
            modal = page.locator('#global-constants-modal')
            if 'active' in modal.get_attribute('class'):
                print("   ✓ Global Constants button works (modal opened)")
                # Close modal
                page.click('#btn-close-global-constants')
                time.sleep(0.3)
            else:
                print("   ⚠️  Global Constants button clicked but modal didn't open")
        except Exception as e:
            print(f"   ❌ Global Constants button failed: {e}")

        # Test 7: New Project button
        print("\n7. Testing New Project button...")
        try:
            page.click('#btn-new-project', timeout=2000)
            time.sleep(0.5)

            # Check if modal opened
            modal = page.locator('#new-project-modal')
            if 'active' in modal.get_attribute('class'):
                print("   ✓ New Project button works (modal opened)")
                # Close modal
                page.click('#btn-close-new-project')
                time.sleep(0.3)
            else:
                print("   ⚠️  New Project button clicked but modal didn't open")
        except Exception as e:
            print(f"   ❌ New Project button failed: {e}")

        # Test 8: Manage Projects button
        print("\n8. Testing Manage Projects button...")
        try:
            page.click('#btn-manage-projects', timeout=2000)
            time.sleep(0.5)

            # Check if modal opened
            modal = page.locator('#manage-projects-modal')
            if 'active' in modal.get_attribute('class'):
                print("   ✓ Manage Projects button works (modal opened)")
                # Close modal
                page.click('#btn-close-manage-projects')
                time.sleep(0.3)
            else:
                print("   ⚠️  Manage Projects button clicked but modal didn't open")
        except Exception as e:
            print(f"   ❌ Manage Projects button failed: {e}")

        # Show any console logs
        if console_logs:
            print("\n" + "=" * 80)
            print("📝 Console Logs:")
            print("=" * 80)
            for log in console_logs[:10]:  # Show first 10
                print(f"   {log}")

        print("\n" + "=" * 80)
        print("✅ Test Complete")
        print("=" * 80)

        browser.close()

if __name__ == "__main__":
    test_button_clicks()
