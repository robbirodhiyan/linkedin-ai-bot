from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://www.linkedin.com/login")
    print("Silakan login LinkedIn manual di browser yang terbuka.")
    print("Kalau sudah masuk feed LinkedIn, tekan ENTER di terminal...")

    input()

    context.storage_state(path="linkedin_state.json")
    print("Session berhasil disimpan ke linkedin_state.json")

    browser.close()