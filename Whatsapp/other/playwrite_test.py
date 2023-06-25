from playwright.sync_api import sync_playwright

user_data_dir = r"C:\Users\ammar\Whatsapp Pro\Profile-2-2022-09-21-20-21-23"
playwright = sync_playwright().start()

browser = playwright.chromium.launch_persistent_context(user_data_dir, channel="chrome", no_viewport=True, args=[], headless=False)
# browser = playwright.chromium.launch(headless=False)
page = browser.pages[0]
page.goto('https://web.whatsapp.com/')

page = browser.new_page()
page.goto('https://web.whatsapp.com/')
# page.screenshot(path=f'example-{browser_type.name}.png')
# browser.close()
