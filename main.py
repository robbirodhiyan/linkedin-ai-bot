import os
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
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing from GitHub Secrets.")

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


def post_to_linkedin(content):
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email:
        raise RuntimeError("LINKEDIN_EMAIL is missing from GitHub Secrets.")

    if not password:
        raise RuntimeError("LINKEDIN_PASSWORD is missing from GitHub Secrets.")

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

        print("Opening LinkedIn login page...")
        page.goto("https://www.linkedin.com/login", wait_until="networkidle", timeout=60000)

        print("Current URL after open login:", page.url)
        print("Page title:", page.title())

        # Simpan screenshot untuk debugging kalau gagal
        page.screenshot(path="debug_login_page.png", full_page=True)

        # Kadang LinkedIn tampilkan halaman cookie/consent
        try:
            accept_button = page.locator(
                'button:has-text("Accept"), button:has-text("Agree"), button:has-text("Allow")'
            ).first
            if accept_button.count() > 0:
                accept_button.click(timeout=5000)
                page.wait_for_timeout(2000)
        except Exception as cookie_error:
            print("No cookie button clicked:", cookie_error)

        email_input = page.locator('input[name="session_key"], input#username, input[type="email"]').first
        password_input = page.locator('input[name="session_password"], input#password, input[type="password"]').first

        if email_input.count() == 0:
            page.screenshot(path="debug_login_missing_email.png", full_page=True)
            raise RuntimeError(
                f"LinkedIn email input not found. Current URL: {page.url}, title: {page.title()}"
            )

        print("Filling email and password...")
        email_input.fill(email)
        password_input.fill(password)

        login_button = page.locator(
            'button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")'
        ).first
        login_button.click()

        page.wait_for_timeout(10000)

        print("Current URL after login:", page.url)
        print("Page title after login:", page.title())
        page.screenshot(path="debug_after_login.png", full_page=True)

        if "checkpoint" in page.url or "challenge" in page.url:
            raise RuntimeError(
                "LinkedIn meminta verifikasi login/checkpoint. "
                "Solusi berikutnya: gunakan saved cookies/session."
            )

        print("Opening feed...")
        page.goto("https://www.linkedin.com/feed/", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(7000)
        page.screenshot(path="debug_feed.png", full_page=True)

        start_post = page.locator(
            'button:has-text("Start a post"), button:has-text("Mulai posting"), '
            'button:has-text("Buat postingan")'
        ).first

        if start_post.count() == 0:
            raise RuntimeError(
                f"Start post button not found. Current URL: {page.url}, title: {page.title()}"
            )

        print("Opening post modal...")
        start_post.click()
        page.wait_for_timeout(4000)

        editor = page.locator('div[role="textbox"]').first
        editor.fill(content)
        page.wait_for_timeout(2000)

        submit_button = page.locator(
            'button:has-text("Post"), button:has-text("Posting"), button:has-text("Kirim")'
        ).last

        print("Publishing post...")
        submit_button.click()
        page.wait_for_timeout(5000)

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