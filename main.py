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

        print("Opening LinkedIn feed using saved session...")

        try:
            page.goto(
                "https://www.linkedin.com/feed/",
                wait_until="domcontentloaded",
                timeout=60000
            )
        except Exception as error:
            print(f"Feed page load warning: {error}")

        page.wait_for_timeout(10000)

        print("Current URL:", page.url)
        print("Page title:", page.title())

        page.screenshot(path="debug_feed.png", full_page=True)

        if "login" in page.url or "checkpoint" in page.url or "challenge" in page.url:
            page.screenshot(path="debug_session_invalid.png", full_page=True)
            browser.close()
            raise RuntimeError(
                "LinkedIn session tidak valid / expired / kena checkpoint. "
                "Buat ulang linkedin_state.json lewat save_session.py, lalu update secret LINKEDIN_STORAGE_STATE."
            )

        start_post = page.locator(
            'button:has-text("Start a post"), '
            'button:has-text("Mulai posting"), '
            'button:has-text("Buat postingan")'
        ).first

        if start_post.count() == 0:
            page.screenshot(path="debug_start_post_not_found.png", full_page=True)
            browser.close()
            raise RuntimeError(
                f"Start post button not found. Current URL: {page.url}, title: {page.title()}"
            )

        print("Opening post modal...")
        start_post.click()
        page.wait_for_timeout(4000)

        page.screenshot(path="debug_post_modal.png", full_page=True)

        editor = page.locator('div[role="textbox"]').first

        if editor.count() == 0:
            page.screenshot(path="debug_editor_not_found.png", full_page=True)
            browser.close()
            raise RuntimeError("Post editor textbox not found.")

        print("Filling post content...")
        editor.fill(content)
        page.wait_for_timeout(2000)

        submit_button = page.locator(
            'button:has-text("Post"), '
            'button:has-text("Posting"), '
            'button:has-text("Kirim")'
        ).last

        if submit_button.count() == 0:
            page.screenshot(path="debug_post_button_not_found.png", full_page=True)
            browser.close()
            raise RuntimeError("Post submit button not found.")

        print("Publishing post...")
        submit_button.click()
        page.wait_for_timeout(8000)

        page.screenshot(path="debug_after_post.png", full_page=True)

        browser.close()