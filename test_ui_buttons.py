#!/usr/bin/env python3
"""
Lumina UI Button Testing Script
Tests all buttons and captures console errors
"""
from playwright.sync_api import sync_playwright
import json
import sys

def test_lumina_ui():
    console_messages = []
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Headless mode
        context = browser.new_context()
        page = context.new_page()

        # Capture console messages
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }))

        # Capture errors
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        print("=" * 80)
        print("🧪 Lumina UI Button Testing")
        print("=" * 80)

        # Navigate to the app
        print("\n1. Loading page...")
        page.goto('http://127.0.0.1:15555')
        page.wait_for_load_state('networkidle')

        # Take initial screenshot
        page.screenshot(path='/tmp/lumina_initial.png', full_page=True)
        print("   ✓ Page loaded, screenshot saved to /tmp/lumina_initial.png")

        # Check for console errors
        if errors:
            print(f"\n   ⚠️  JavaScript Errors Found: {len(errors)}")
            for i, error in enumerate(errors, 1):
                print(f"      {i}. {error}")

        # Check for console warnings/errors
        console_errors = [m for m in console_messages if m['type'] in ['error', 'warning']]
        if console_errors:
            print(f"\n   ⚠️  Console Errors/Warnings: {len(console_errors)}")
            for i, msg in enumerate(console_errors[:5], 1):  # Show first 5
                print(f"      {i}. [{msg['type']}] {msg['text']}")

        # Test buttons
        print("\n2. Testing Buttons...")

        buttons_to_test = [
            ("btn-new-folder", "New Folder"),
            ("btn-new-request", "New Request"),
            ("btn-send", "Send"),
            ("btn-clear-response", "Clear Response"),
            ("btn-beautify-json", "Beautify JSON"),
            ("btn-toggle-preview", "Toggle Preview"),
            ("btn-more", "More Menu"),
            ("btn-copy-url", "Copy URL"),
            ("btn-delete-request", "Delete Request"),
            ("btn-share-project", "Share Project"),
            ("btn-import-md", "Import MD"),
            ("btn-global-constants", "Global Constants"),
            ("btn-new-project", "New Project"),
            ("btn-manage-projects", "Manage Projects"),
        ]

        test_results = []

        for btn_id, btn_name in buttons_to_test:
            try:
                # Check if button exists
                button = page.locator(f'#{btn_id}')
                if button.count() == 0:
                    test_results.append({
                        "button": btn_name,
                        "id": btn_id,
                        "status": "NOT_FOUND",
                        "error": "Element not found in DOM"
                    })
                    print(f"   ❌ {btn_name} (#{btn_id}) - NOT FOUND")
                    continue

                # Check if button is visible
                is_visible = button.is_visible()
                if not is_visible:
                    test_results.append({
                        "button": btn_name,
                        "id": btn_id,
                        "status": "HIDDEN",
                        "error": "Element exists but is hidden"
                    })
                    print(f"   ⚠️  {btn_name} (#{btn_id}) - HIDDEN")
                    continue

                # Check if button is enabled
                is_enabled = button.is_enabled()
                if not is_enabled:
                    test_results.append({
                        "button": btn_name,
                        "id": btn_id,
                        "status": "DISABLED",
                        "error": "Button is disabled"
                    })
                    print(f"   ⚠️  {btn_name} (#{btn_id}) - DISABLED")
                    continue

                test_results.append({
                    "button": btn_name,
                    "id": btn_id,
                    "status": "OK",
                    "error": None
                })
                print(f"   ✓ {btn_name} (#{btn_id}) - OK")

            except Exception as e:
                test_results.append({
                    "button": btn_name,
                    "id": btn_id,
                    "status": "ERROR",
                    "error": str(e)
                })
                print(f"   ❌ {btn_name} (#{btn_id}) - ERROR: {e}")

        # Test modal buttons (might not be visible initially)
        print("\n3. Checking Modal Buttons (may be hidden)...")

        modal_buttons = [
            ("btn-close-share", "Close Share Modal"),
            ("btn-close-import-share", "Close Import Share Modal"),
            ("btn-close-global-constants", "Close Global Constants Modal"),
            ("btn-close-import-insomnia", "Close Import Insomnia Modal"),
            ("btn-close-export-insomnia", "Close Export Insomnia Modal"),
        ]

        for btn_id, btn_name in modal_buttons:
            try:
                button = page.locator(f'#{btn_id}')
                exists = button.count() > 0
                status = "EXISTS" if exists else "NOT_FOUND"
                print(f"   {'✓' if exists else '❌'} {btn_name} (#{btn_id}) - {status}")
            except Exception as e:
                print(f"   ❌ {btn_name} (#{btn_id}) - ERROR: {e}")

        # Test Send button specifically (user reported it doesn't work)
        print("\n4. Testing Send Button Specifically...")
        try:
            send_btn = page.locator('#btn-send')
            if send_btn.count() > 0:
                print(f"   ✓ Send button found")
                print(f"   - Visible: {send_btn.is_visible()}")
                print(f"   - Enabled: {send_btn.is_enabled()}")
                print(f"   - Text: {send_btn.inner_text()}")

                # Check if there's onclick attribute
                onclick_attr = page.evaluate("""() => {
                    const btn = document.getElementById('btn-send');
                    return btn ? btn.onclick !== null : false;
                }""")
                print(f"   - Has onclick attribute: {onclick_attr}")
            else:
                print(f"   ❌ Send button NOT FOUND")
        except Exception as e:
            print(f"   ❌ Error testing send button: {e}")

        # Check for JavaScript initialization
        print("\n5. Checking JavaScript Initialization...")
        try:
            app_exists = page.evaluate("typeof window.app !== 'undefined'")
            print(f"   {'✓' if app_exists else '❌'} window.app exists: {app_exists}")

            if app_exists:
                app_props = page.evaluate("""() => {
                    return {
                        hasCurrentRequest: window.app.currentRequest !== null,
                        hasCurrentProject: window.app.currentProject !== null,
                        requestsCount: window.app.requests?.length || 0
                    };
                }""")
                print(f"   - Current Request: {app_props['hasCurrentRequest']}")
                print(f"   - Current Project: {app_props['hasCurrentProject']}")
                print(f"   - Requests Count: {app_props['requestsCount']}")
        except Exception as e:
            print(f"   ❌ Error checking JavaScript: {e}")

        # Summary
        print("\n" + "=" * 80)
        print("📊 Test Summary")
        print("=" * 80)

        ok_count = len([r for r in test_results if r['status'] == 'OK'])
        not_found_count = len([r for r in test_results if r['status'] == 'NOT_FOUND'])
        hidden_count = len([r for r in test_results if r['status'] == 'HIDDEN'])
        disabled_count = len([r for r in test_results if r['status'] == 'DISABLED'])
        error_count = len([r for r in test_results if r['status'] == 'ERROR'])

        print(f"✓ OK: {ok_count}")
        print(f"❌ Not Found: {not_found_count}")
        print(f"⚠️  Hidden: {hidden_count}")
        print(f"⚠️  Disabled: {disabled_count}")
        print(f"❌ Errors: {error_count}")

        if console_errors:
            print(f"\n⚠️  Console Errors: {len(console_errors)}")

        if errors:
            print(f"⚠️  JavaScript Errors: {len(errors)}")

        # Save detailed results
        with open('/tmp/lumina_test_results.json', 'w') as f:
            json.dump({
                'test_results': test_results,
                'console_messages': console_messages,
                'errors': errors
            }, f, indent=2)

        print(f"\n📝 Detailed results saved to /tmp/lumina_test_results.json")

        browser.close()

        return test_results, console_messages, errors

if __name__ == "__main__":
    try:
        test_lumina_ui()
    except KeyboardInterrupt:
        print("\n\n⏸️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
