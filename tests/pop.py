from playwright.sync_api import sync_playwright


def open_popup():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        # Open a new page (tab) in popup mode
        page = context.new_page()
        page.evaluate("() => window.open('https://web.whatsapp.com/', 'popup', 'width=320,height=240')")
        # Close the initial tab
        context.pages[0].close()
        try:
            while True:
                pass
        except KeyboardInterrupt:
            pass

        browser.close()


open_popup()
