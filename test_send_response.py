#!/usr/bin/env python3
"""
Test send request and check if response appears
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

    print("=" * 80)
    print("Testing Send Request and Response...")
    print("=" * 80)

    # Navigate to the app
    page.goto('http://127.0.0.1:15555')
    page.wait_for_load_state('networkidle')
    time.sleep(1)

    # Create a new request first
    print("\n1. Creating a new request...")
    try:
        page.click('#btn-new-request', timeout=5000)
        time.sleep(0.5)

        # Handle the prompt dialog
        page.on("dialog", lambda dialog: dialog.accept("Test Request"))
        page.click('#btn-new-request')
        time.sleep(1)
        print("   ✓ Request created")
    except Exception as e:
        print(f"   ⚠️  Could not create new request: {e}")

    # Check if we have a request selected
    print("\n2. Checking if request is selected...")
    try:
        url_input = page.locator('#input-url')
        if url_input.is_visible():
            print("   ✓ Request editor is visible")

            # Set a test URL
            url_input.fill('https://httpbin.org/get')
            print("   ✓ URL set to https://httpbin.org/get")
        else:
            print("   ❌ Request editor not visible")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Click Send button
    print("\n3. Clicking Send button...")
    try:
        send_btn = page.locator('#btn-send')
        if send_btn.is_visible():
            print("   ✓ Send button is visible")
            send_btn.click()
            print("   ✓ Send button clicked")

            # Wait for response
            print("\n4. Waiting for response...")
            time.sleep(5)  # Wait longer for actual HTTP request

            # Check if response panel is visible
            response_panel = page.locator('#response-panel')
            if response_panel.is_visible():
                print("   ✓ Response panel is visible")

                # Check response status
                response_status = page.locator('#response-status')
                if response_status.is_visible():
                    status_text = response_status.text_content()
                    print(f"   ✓ Response status: {status_text}")
                else:
                    print("   ❌ Response status not visible")

                # Check response body
                response_body = page.locator('#response-body')
                if response_body.is_visible():
                    body_text = response_body.text_content()
                    if body_text and len(body_text) > 0:
                        print(f"   ✓ Response body has content ({len(body_text)} chars)")
                    else:
                        print("   ⚠️  Response body is empty")
                else:
                    print("   ❌ Response body not visible")
            else:
                print("   ❌ Response panel NOT visible")

                # Check if it has 'hidden' class
                has_hidden = 'hidden' in (response_panel.get_attribute('class') or '')
                print(f"   - Has 'hidden' class: {has_hidden}")
        else:
            print("   ❌ Send button not visible")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Take screenshot
    print("\n5. Taking screenshot...")
    page.screenshot(path='/tmp/send_response_test.png', full_page=True)
    print("   ✓ Screenshot saved to /tmp/send_response_test.png")

    # Show console logs
    if console_logs:
        print("\n" + "=" * 80)
        print("Console Logs:")
        print("=" * 80)
        for log in console_logs:
            print(f"   {log}")

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

    browser.close()
