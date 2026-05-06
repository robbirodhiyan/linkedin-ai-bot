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
        print("OPENAI_API_KEY not found. Using fallback post.")
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
        print(f"OpenAI failed, using fallback post. Error: {error}")
        return random.choice(fallback_posts)


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
            raise RuntimeError("Post submit button not found.")

        print("Publishing post...")
        submit_button.click()
        page.wait_for_timeout(8000)

        page.screenshot(path="debug_after_post.png", full_page=True)

        browser.close()


def save_post_log(content):
    with open("post_history.txt", "a", encoding="utf-8") as file:
        file.write(f"\n[{datetime.now()}]\n")
        file.write(content)
        file.write("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    generated_content = generate_ai_post()

    print("Generated LinkedIn post:")
    print(generated_content)

    save_post_log(generated_content)
    post_to_linkedin(generated_content)

    print("Success posted at", datetime.now())