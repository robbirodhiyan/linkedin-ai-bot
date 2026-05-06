import os
import json
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
from openai import OpenAI


TOPICS = [
    "Laravel Development",
    "ERP Integration",
    "SAP Automation",
    "Business Process Digitalization",
    "IT Leadership",
    "Fullstack Engineering",
    "Software Automation",
    "Internal Dashboard Development",
]


def generate_ai_post():
    api_key = os.getenv("OPENAI_API_KEY")

    fallback_posts = [
        """Automation is not about replacing people.

It is about removing repetitive work so people can focus on decisions, improvement, and business impact.

In many companies, the biggest productivity gap is not the lack of people.
It is too many manual processes that should have been automated years ago.

#Automation #DigitalTransformation #ITLeadership #SoftwareEngineering""",

        """A good internal system is not only about features.

It must be fast, stable, easy to maintain, and aligned with real business processes.

That is why understanding users, database structure, and operational flow is as important as writing code.

#Laravel #ERP #FullstackDevelopment #BusinessProcess""",

        """ERP integration is not just sending data from one system to another.

The real challenge is data validation, error handling, retry logic, logging, and making sure business users can trust the result.

Reliable integration is built from small details.

#ERPIntegration #SAP #BackendDevelopment #Automation""",
    ]

    if not api_key:
        print("OPENAI_API_KEY not found. Using fallback post.", flush=True)
        return random.choice(fallback_posts)

    try:
        client = OpenAI(api_key=api_key)

        topic = random.choice(TOPICS)

        prompt = f"""
Write one professional LinkedIn post in English for an experienced IT Development Lead.

Topic: {topic}

Style:
- insightful
- practical
- authority-building
- not salesy
- natural human tone

Structure:
- strong hook
- short practical insight
- simple closing sentence
- 3 to 5 relevant hashtags

Max 120 words.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
        )

        return response.choices[0].message.content.strip()

    except Exception as error:
        print(f"OpenAI failed, using fallback post. Error: {error}", flush=True)
        return random.choice(fallback_posts)


def safe_screenshot(page, path):
    try:
        page.screenshot(path=path, full_page=True, timeout=15000)
        print(f"Screenshot saved: {path}", flush=True)
    except Exception as error:
        print(f"Screenshot failed ({path}): {error}", flush=True)


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
            print("Feed loaded. Continue searching start post button...", flush=True)

            safe_screenshot(page, "debug_feed.png")

            if "login" in page.url or "checkpoint" in page.url or "challenge" in page.url:
                safe_screenshot(page, "debug_session_invalid.png")
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
                'button[aria-label*="Create a post"]',
                'button[aria-label*="Buat posting"]',
            ]

            start_post = None

            for selector in start_post_selectors:
                locator = page.locator(selector).first

                try:
                    count = locator.count()

                    if count > 0 and locator.is_visible(timeout=5000):
                        start_post = locator
                        print(f"Start post button found using selector: {selector}", flush=True)
                        break

                except Exception as error:
                    print(f"Start post selector failed: {selector} | {error}", flush=True)

            if start_post is None:
                safe_screenshot(page, "debug_start_post_not_found.png")
                raise RuntimeError(
                    f"Start post button not found. Current URL: {page.url}, title: {page.title()}"
                )

            print("Opening post modal...", flush=True)
            start_post.click(force=True)
            page.wait_for_timeout(6000)

            safe_screenshot(page, "debug_post_modal.png")

            print("Searching editor textbox...", flush=True)

            editor_selectors = [
                'div[role="textbox"]',
                '.ql-editor',
                'div[contenteditable="true"]',
                'div.share-creation-state__text-editor div[role="textbox"]',
                'div[data-test-ql-editor-contenteditable="true"]',
            ]

            editor = None

            for selector in editor_selectors:
                locator = page.locator(selector).first

                try:
                    count = locator.count()

                    if count > 0 and locator.is_visible(timeout=5000):
                        editor = locator
                        print(f"Editor found using selector: {selector}", flush=True)
                        break

                except Exception as error:
                    print(f"Editor selector failed: {selector} | {error}", flush=True)

            if editor is None:
                safe_screenshot(page, "debug_editor_not_found.png")
                raise RuntimeError("Post editor textbox not found.")

            print("Filling post content...", flush=True)

            editor.click(force=True)
            page.wait_for_timeout(1000)

            # Lebih stabil untuk contenteditable editor LinkedIn
            page.keyboard.insert_text(content)
            page.wait_for_timeout(4000)

            safe_screenshot(page, "debug_content_filled.png")

            print("Searching publish button...", flush=True)

            post_button_selectors = [
                'button:has-text("Post")',
                'button:has-text("Posting")',
                'button:has-text("Kirim")',
                'button[aria-label*="Post"]',
                'button[aria-label*="Posting"]',
                'button[aria-label*="Kirim"]',
                '.share-actions__primary-action button',
                'button.share-actions__primary-action',
            ]

            submit_button = None

            for selector in post_button_selectors:
                locators = page.locator(selector)

                try:
                    count = locators.count()

                    if count > 0:
                        for i in range(count):
                            button = locators.nth(i)

                            try:
                                if button.is_visible(timeout=3000):
                                    disabled = button.get_attribute("disabled")
                                    aria_disabled = button.get_attribute("aria-disabled")

                                    if disabled is None and aria_disabled != "true":
                                        submit_button = button
                                        print(f"Publish button found using selector: {selector}", flush=True)
                                        break

                            except Exception as inner_error:
                                print(f"Publish button item failed: {selector} index {i} | {inner_error}", flush=True)

                    if submit_button is not None:
                        break

                except Exception as error:
                    print(f"Publish selector failed: {selector} | {error}", flush=True)

            if submit_button is None:
                safe_screenshot(page, "debug_post_button_not_found.png")
                raise RuntimeError("Post submit button not found or still disabled.")

            print("Publishing post...", flush=True)
            submit_button.click(force=True)
            page.wait_for_timeout(12000)

            safe_screenshot(page, "debug_after_post.png")

            print("Post process finished. Check LinkedIn profile/feed.", flush=True)

        finally:
            browser.close()


def save_post_log(content):
    with open("post_history.txt", "a", encoding="utf-8") as file:
        file.write(f"\n[{datetime.now()}]\n")
        file.write(content)
        file.write("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    print("BOT STARTED", flush=True)

    generated_content = generate_ai_post()

    print("Generated LinkedIn post:", flush=True)
    print(generated_content, flush=True)

    save_post_log(generated_content)

    print("Start posting to LinkedIn...", flush=True)
    post_to_linkedin(generated_content)

    print("Success posted at", datetime.now(), flush=True)