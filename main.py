def post_to_linkedin(content):
    storage_state_json = os.getenv("LINKEDIN_STORAGE_STATE")

    if not storage_state_json:
        raise RuntimeError(
            "LINKEDIN_STORAGE_STATE is missing from GitHub Secrets. "
            "Login lokal dulu pakai save_session.py, lalu paste isi linkedin_state.json ke secret LINKEDIN_STORAGE_STATE."
        )

    try:
        storage_state = json.loads(storage_state_json)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "LINKEDIN_STORAGE_STATE is not valid JSON. "
            "Pastikan isi secret adalah full isi file linkedin_state.json."
        ) from error

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1366,768",
            ],
        )

        context = browser.new_context(
            storage_state=storage_state,
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )

        page = context.new_page()
        page.set_default_timeout(60000)

        try:
            print("Opening LinkedIn feed using saved session...", flush=True)

            try:
                page.goto(
                    "https://www.linkedin.com/feed/",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
            except Exception as error:
                print(f"Feed load warning: {error}", flush=True)

            page.wait_for_timeout(12000)

            print("Current URL:", page.url, flush=True)
            print("Page title:", page.title(), flush=True)

            page.screenshot(path="debug_feed.png", full_page=True)

            if "login" in page.url or "checkpoint" in page.url or "challenge" in page.url:
                page.screenshot(path="debug_session_invalid.png", full_page=True)
                raise RuntimeError(
                    "LinkedIn session tidak valid / expired / kena checkpoint. "
                    "Buat ulang linkedin_state.json lewat save_session.py, lalu update secret LINKEDIN_STORAGE_STATE."
                )

            print("Searching start post button...", flush=True)

            start_post_selectors = [
                'button:has-text("Start a post")',
                'button:has-text("Mulai posting")',
                'button:has-text("Buat postingan")',
                'button.share-box-feed-entry__trigger',
                '[data-control-name="share.sharebox_focus"]',
                'button[aria-label*="Start a post"]',
                'button[aria-label*="Mulai posting"]',
                'button[aria-label*="Buat postingan"]',
            ]

            start_post = None

            for selector in start_post_selectors:
                locator = page.locator(selector).first
                try:
                    if locator.count() > 0 and locator.is_visible(timeout=5000):
                        start_post = locator
                        print(f"Start post button found using selector: {selector}", flush=True)
                        break
                except Exception:
                    pass

            if start_post is None:
                page.screenshot(path="debug_start_post_not_found.png", full_page=True)
                raise RuntimeError(
                    f"Start post button not found. Current URL: {page.url}, title: {page.title()}"
                )

            print("Opening post modal...", flush=True)
            start_post.click(force=True)
            page.wait_for_timeout(5000)

            page.screenshot(path="debug_post_modal.png", full_page=True)

            print("Searching editor textbox...", flush=True)

            editor_selectors = [
                'div[role="textbox"]',
                '.ql-editor',
                'div[contenteditable="true"]',
                'div.share-creation-state__text-editor div[role="textbox"]',
            ]

            editor = None

            for selector in editor_selectors:
                locator = page.locator(selector).first
                try:
                    if locator.count() > 0 and locator.is_visible(timeout=5000):
                        editor = locator
                        print(f"Editor found using selector: {selector}", flush=True)
                        break
                except Exception:
                    pass

            if editor is None:
                page.screenshot(path="debug_editor_not_found.png", full_page=True)
                raise RuntimeError("Post editor textbox not found.")

            print("Filling post content...", flush=True)
            editor.click(force=True)
            page.wait_for_timeout(1000)

            # Lebih stabil daripada fill() untuk editor contenteditable LinkedIn
            page.keyboard.insert_text(content)
            page.wait_for_timeout(3000)

            page.screenshot(path="debug_content_filled.png", full_page=True)

            print("Searching publish button...", flush=True)

            post_button_selectors = [
                'button:has-text("Post")',
                'button:has-text("Posting")',
                'button:has-text("Kirim")',
                'button[aria-label*="Post"]',
                'button[aria-label*="Posting"]',
                'button[aria-label*="Kirim"]',
                '.share-actions__primary-action button',
            ]

            submit_button = None

            for selector in post_button_selectors:
                locators = page.locator(selector)
                try:
                    count = locators.count()
                    if count > 0:
                        for i in range(count):
                            btn = locators.nth(i)
                            if btn.is_visible(timeout=3000):
                                disabled = btn.get_attribute("disabled")
                                aria_disabled = btn.get_attribute("aria-disabled")

                                if disabled is None and aria_disabled != "true":
                                    submit_button = btn
                                    print(f"Publish button found using selector: {selector}", flush=True)
                                    break

                    if submit_button is not None:
                        break
                except Exception:
                    pass

            if submit_button is None:
                page.screenshot(path="debug_post_button_not_found.png", full_page=True)
                raise RuntimeError("Post submit button not found or still disabled.")

            print("Publishing post...", flush=True)
            submit_button.click(force=True)
            page.wait_for_timeout(10000)

            page.screenshot(path="debug_after_post.png", full_page=True)

            print("Post process finished. Check LinkedIn profile/feed.", flush=True)

        finally:
            browser.close()