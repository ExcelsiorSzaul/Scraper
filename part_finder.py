from playwright.sync_api import sync_playwright
import database

def open_browser(context=None):
    """Open a Playwright browser and navigate to the target site."""
    if context is None:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
    else:
        playwright = None
        browser = None
    page = context.new_page()
    page.goto("https://www.rockymountainatvmc.com/oem-parts")
    return playwright, browser, context, page

def scrape_data(page, mpn):
    """Scrape data from the page based on the provided MPN."""
    instructions = []

    if not mpn:
        print("No MPN provided.")
        return instructions

    # Scrape data
    titles = ["First Choice", "Second Choice", "Third Choice", "Fourth Choice", "Fifth Choice", "Sixth Choice", "Parts Schematic"]

    for title in titles:
        selector = f"select[title='{title}']"
        try:
            if title == "First Choice":
                value = page.locator(selector).evaluate("element => element.options[element.selectedIndex].text", timeout=500)
                if value == "Arctic Cat":
                    value = "Arctic-Cat"
            else:
                value = page.locator(selector).evaluate("element => element.value", timeout=500)

            if value:
                print(f"Scraped {title}: {value}")
                instructions.append(value)
            else:
                print(f"No value found for {title}")

        except Exception as e:
            print(f"Error scraping {title}: {e}")
            continue

    instructions.append(mpn)
    return instructions

def add_to_database(instructions):
    """Add scraped data to the database."""
    if not instructions:
        return

    MPN = instructions[-1]
    brand = instructions[0]
    instructions = instructions[:-1]

    print(f"Adding part '{MPN}' to database...")
    try:
        database.add_part(mpn=MPN, in_stock=1, price=0.00, brand=brand, instructions=instructions, part_id=None)
        print(f"Part {MPN} successfully added to database.")
    except Exception as e:
        print(f"Failed to add part {MPN} to database: {str(e)}")