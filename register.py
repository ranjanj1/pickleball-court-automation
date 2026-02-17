#!/usr/bin/env python3
"""
Court Reserve Auto-Registration Script
Automatically registers for pickleball open play sessions
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, expect
from config import Config

# Setup logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"registration_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

def log(message, level="INFO"):
    """Log message to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    with open(log_file, "a") as f:
        f.write(log_line + "\n")

def login(page: Page):
    """Login to Court Reserve"""
    log("Navigating to login page...")
    page.goto(Config.LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

    # Wait for email field to be visible
    page.wait_for_selector("input[placeholder='Enter Your Email']", timeout=10000)

    log("Entering credentials...")
    page.fill("input[placeholder='Enter Your Email']", Config.USERNAME)
    page.fill("input[placeholder='Enter Your Password']", Config.PASSWORD)

    log("Submitting login...")
    page.click("button:has-text('Continue')")

    # Wait for navigation after login
    page.wait_for_timeout(3000)  # Give it time to process login

    # Verify login success
    if "login" in page.url.lower():
        log("Login failed! Still on login page.", "ERROR")
        return False

    log("Login successful!", "SUCCESS")
    return True

def navigate_to_events(page: Page):
    """Navigate directly to events page"""
    log("Navigating to events page...")
    page.goto(Config.EVENTS_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)  # Wait for page to load
    log("Loaded events page")

def apply_filters(page: Page, target_date: datetime, dry_run=False):
    """Apply filters for skill level, time, and price"""
    log(f"Applying filters for {target_date.strftime('%Y-%m-%d')}...")

    time_filter = Config.get_time_filter(target_date)

    log(f"  - Target date: {target_date.strftime('%A, %B %d, %Y')}")
    log(f"  - Time preference: {time_filter}")
    log(f"  - Skill level: {Config.SKILL_LEVEL}")

    page.wait_for_timeout(2000)

    # 1. Check skill level in Tags section
    try:
        log(f"  Checking {Config.SKILL_LEVEL} tag...")

        # Find all tag checkboxes and their associated labels
        tag_containers = page.locator('[data-testid="tags-checkbox"]').all()
        log(f"  Found {len(tag_containers)} tag checkboxes")

        found = False
        for container in tag_containers:
            # Get the parent div to access both checkbox and label
            parent = container.locator('xpath=ancestor::div[contains(@class, "custom-checkbox")]')
            # Find the badge label
            label = parent.locator('label.badge.custom-badge')

            if label.count() > 0:
                label_text = label.inner_text().strip()
                # Match skill level (handle variations in spacing/text)
                if "intermediate" in label_text.lower():
                    # Click the badge label instead of the checkbox (Kendo UI overlay issue)
                    label.click(force=True)
                    log(f"  ✓ {label_text} checked")
                    page.wait_for_timeout(2000)
                    found = True
                    break

        if not found:
            log(f"  ⚠ Could not find Intermediate tag", "WARNING")
    except Exception as e:
        log(f"  ⚠ Error checking skill level: {e}", "WARNING")

    # 2. Select Date filter (This Month if applicable, otherwise skip)
    try:
        from datetime import datetime
        now = datetime.now()

        # Check if target date is in the current month
        if target_date.month == now.month and target_date.year == now.year:
            log("  Setting date filter to 'This Month'...")
            this_month_radio = page.locator('[data-testid="this-month-checkbox"]')
            if this_month_radio.count() > 0:
                this_month_radio.click(force=True)
                log("  ✓ 'This Month' selected")
                page.wait_for_timeout(2000)
            else:
                log("  ⚠ Could not find 'This Month' radio", "WARNING")
        else:
            log(f"  Skipping date filter (target is in {target_date.strftime('%B %Y')})")
    except Exception as e:
        log(f"  ⚠ Error setting date filter: {e}", "WARNING")

    # 2b. Select Day of Week
    try:
        day_name = target_date.strftime("%A")  # e.g., "Sunday"
        log(f"  Selecting day of week: {day_name}...")

        # Map day names to data-testid or checkbox IDs
        # Find checkbox by label text
        day_checkbox = page.locator(f'label:has-text("{day_name}")').locator('xpath=preceding-sibling::input[@type="checkbox"]').first

        if day_checkbox.count() > 0:
            day_checkbox.check(force=True)
            log(f"  ✓ {day_name} selected")
            page.wait_for_timeout(2000)
        else:
            log(f"  ⚠ Could not find {day_name} checkbox", "WARNING")
    except Exception as e:
        log(f"  ⚠ Error setting day of week: {e}", "WARNING")

    # 3. Check Time of Day
    try:
        log(f"  Checking {time_filter} time...")

        # Map time filter to data-testid
        time_mapping = {
            "Morning": "time-of-day-morning",
            "Afternoon": "time-of-day-afternoon",
            "Evening": "time-of-day-evening"
        }

        testid = time_mapping.get(time_filter)
        if testid:
            time_checkbox = page.locator(f'[data-testid="{testid}"]')
            if time_checkbox.count() > 0:
                time_checkbox.check(force=True)
                log(f"  ✓ {time_filter} checked")
                page.wait_for_timeout(2000)
            else:
                log(f"  ⚠ Could not find {time_filter} checkbox", "WARNING")
        else:
            log(f"  ⚠ Unknown time filter: {time_filter}", "WARNING")
    except Exception as e:
        log(f"  ⚠ Error setting time filter: {e}", "WARNING")

    # 4. Set Price Range to $0 (FREE events only)
    try:
        log("  Setting price range to $0 (FREE only)...")

        # Use JavaScript to set slider values directly
        page.evaluate("""
            const slider = document.getElementById('eventFilterPriceRange');
            if (slider) {
                // Move both slider handles to the left (value 0)
                const handles = slider.querySelectorAll('.ui-slider-handle');
                handles.forEach(handle => {
                    handle.style.left = '0%';
                });

                // Update the range bar
                const range = slider.querySelector('.ui-slider-range');
                if (range) {
                    range.style.left = '0%';
                    range.style.width = '0%';
                }

                // Trigger change event to update the page
                const event = new Event('slidechange');
                slider.dispatchEvent(event);
            }
        """)

        page.wait_for_timeout(2000)
        log("  ✓ Price range set to $0")
    except Exception as e:
        log(f"  ⚠ Error setting price range: {e}", "WARNING")

    log("Filters applied!")

    # Pause to verify filters
    # log("Pausing for verification... Press Continue in Playwright Inspector")
    # page.pause()

def find_and_register_events(page: Page, target_date: datetime, dry_run=False):
    """Find matching FREE events and register"""
    log(f"Looking for FREE events on {target_date.strftime('%b %d, %Y')}...")

    # Wait for events to load after filters
    page.wait_for_timeout(2000)

    # Find all visible event cards
    events = page.locator("article, [class*='event'], [class*='program']").all()

    if not events:
        log("No events found on page", "WARNING")
        return []

    log(f"Found {len(events)} events, filtering for target date...")

    registered = []

    for i, event in enumerate(events):
        try:
            # Get event title
            title_elem = event.locator("h1, h2, h3, h4").first
            if title_elem.count() == 0:
                continue
            title = title_elem.inner_text().strip()

            # Get date/time
            date_time_elem = event.locator("text=/[A-Z][a-z]{2}, [A-Z][a-z]{2}/").first
            if date_time_elem.count() == 0:
                continue
            date_time = date_time_elem.inner_text().strip()

            # Filter by target date (e.g., "Sun, Mar 8th")
            target_date_str = target_date.strftime("%a, %b %-d")  # e.g., "Sun, Mar 8"
            # Handle "8th", "21st", etc. - just check if date_time starts with day and month
            if not (target_date_str in date_time or
                    target_date.strftime("%a, %b %-dst") in date_time or
                    target_date.strftime("%a, %b %-dnd") in date_time or
                    target_date.strftime("%a, %b %-drd") in date_time or
                    target_date.strftime("%a, %b %-dth") in date_time):
                continue  # Skip events not on target date

            # Check if FREE (skip paid events)
            price_elem = event.locator("text=/FREE/i")
            if price_elem.count() == 0:
                log(f"  Skipping (paid): {title}")
                continue

            log(f"\n✓ Found FREE event:")
            log(f"  Title: {title}")
            log(f"  Date/Time: {date_time}")

            # Check availability
            if event.locator("text=/FULL/i").count() > 0:
                log("  Status: FULL")

                if dry_run:
                    log("  [DRY RUN] Would join waitlist")
                    registered.append({"title": title, "date": date_time, "status": "would join waitlist"})
                else:
                    waitlist_btn = event.locator("button:has-text('Join Waitlist')")
                    if waitlist_btn.count() > 0:
                        waitlist_btn.click()
                        page.wait_for_timeout(1000)
                        log("  ✓ Joined waitlist!", "SUCCESS")
                        registered.append({"title": title, "date": date_time, "status": "waitlisted"})
                    else:
                        log("  ⚠ No waitlist button", "WARNING")
            else:
                # Check for available spots
                spots_elem = event.locator("text=/\\d+ of \\d+ spots? remaining/i")
                if spots_elem.count() > 0:
                    spots = spots_elem.inner_text()
                    log(f"  Status: {spots}")

                if dry_run:
                    log("  [DRY RUN] Would register")
                    registered.append({"title": title, "date": date_time, "status": "would register"})
                else:
                    # Try finding Register button within event first
                    register_btn = event.locator("button:has-text('Register'), a:has-text('Register')")

                    # If not found, try finding all buttons on page and match by index
                    if register_btn.count() == 0:
                        all_register_btns = page.locator("button:has-text('Register'), a:has-text('Register')").all()
                        if i < len(all_register_btns):
                            register_btn = all_register_btns[i]
                        else:
                            log("  ⚠ No register button found", "WARNING")
                            continue

                    # Click the register button (goes to details page)
                    if register_btn.count() > 0:
                        register_btn.first.click()
                        page.wait_for_timeout(3000)  # Wait for details page to load

                        # Pause to verify details page
                        # log("On event details page. Verify and press Continue...")
                        # page.pause()

                        # On details page, click Register button using data-testid
                        final_register_btn = page.locator('[data-testid="register-btn"]')

                        if final_register_btn.count() > 0:
                            final_register_btn.click()
                            page.wait_for_timeout(3000)  # Wait for confirmation page

                            # Click "Finalize Registration" button on confirmation page
                            finalize_btn = page.locator('button:has-text("Finalize Registration")')
                            if finalize_btn.count() > 0:
                                finalize_btn.click()
                                page.wait_for_timeout(10000)  # Wait for success page to load

                                # Take screenshot of confirmation page
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                screenshot_path = f"logs/registration_success_{timestamp}.png"
                                page.screenshot(path=screenshot_path)
                                log(f"  📸 Screenshot saved: {screenshot_path}")

                                log("  ✓ Successfully registered!", "SUCCESS")
                                registered.append({"title": title, "date": date_time, "status": "registered"})
                            else:
                                log("  ⚠ Could not find Finalize Registration button", "WARNING")
                        else:
                            log("  ⚠ Could not find Register button on details page", "WARNING")
                    else:
                        log("  ⚠ No register button found", "WARNING")

        except Exception as e:
            log(f"  Error processing event {i}: {str(e)}", "ERROR")
            continue

    if not registered:
        log("\nNo events registered", "WARNING")

    return registered

def main():
    parser = argparse.ArgumentParser(description="Auto-register for Court Reserve pickleball sessions")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be registered without actually registering")
    parser.add_argument("--date", help="Specific date to check (YYYY-MM-DD), defaults to 21 days from now")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")

    args = parser.parse_args()

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        log(str(e), "ERROR")
        log("Please copy .env.example to .env and fill in your credentials", "ERROR")
        sys.exit(1)

    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        target_date = Config.get_target_date()

    log("=" * 60)
    log("Court Reserve Auto-Registration")
    log("=" * 60)
    log(f"Target date: {target_date.strftime('%A, %B %d, %Y')}")
    log(f"Skill level: {Config.SKILL_LEVEL}")
    log(f"Price filter: FREE only")
    log(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    log("=" * 60)

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context()
        page = context.new_page()

        # Set default timeout to 60 seconds
        page.set_default_timeout(60000)

        try:
            # Login
            if not login(page):
                log("Exiting due to login failure", "ERROR")
                sys.exit(1)

            # Navigate to Events page
            navigate_to_events(page)

            # Apply filters
            apply_filters(page, target_date, args.dry_run)

            # Find and register for events
            registered = find_and_register_events(page, target_date, args.dry_run)

            # Summary
            log("\n" + "=" * 60)
            log("REGISTRATION SUMMARY")
            log("=" * 60)

            if registered:
                for event in registered:
                    log(f"✓ {event['status'].upper()}: {event['title']}")
                    log(f"  {event['date']}")
            else:
                log("No events were registered")

            log(f"\nLog file: {log_file}")

        except Exception as e:
            log(f"Unexpected error: {str(e)}", "ERROR")
            # Take screenshot for debugging
            screenshot_path = LOG_DIR / f"error_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
            page.screenshot(path=str(screenshot_path))
            log(f"Screenshot saved: {screenshot_path}", "ERROR")
            sys.exit(1)

        finally:
            browser.close()

if __name__ == "__main__":
    main()



