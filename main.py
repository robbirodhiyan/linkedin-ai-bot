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
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        page.fill('input[name="session_key"]', email)
        page.fill('input[name="session_password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_timeout(8000)

        current_url = page.url

        if "checkpoint" in current_url or "challenge" in current_url:
            browser.close()
            raise RuntimeError(
                "LinkedIn meminta verifikasi login/checkpoint. "
                "Solusi berikutnya: pakai saved cookies/session."
            )

        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        page.wait_for_timeout(7000)

        post_button = page.locator('button:has-text("Start a post")').first
        post_button.click()
        page.wait_for_timeout(3000)

        editor = page.locator('div[role="textbox"]').first
        editor.fill(content)
        page.wait_for_timeout(2000)

        submit_button = page.locator('button:has-text("Post")').last
        submit_button.click()
        page.wait_for_timeout(5000)

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