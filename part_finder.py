import customtkinter as ctk
from playwright.sync_api import sync_playwright
import threading
import database

# Global variables
browser = None
page = None
playwright = None
entry_box = None
scrape_event = None

def open_browser():
    global browser, page, playwright
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.rockymountainatvmc.com/oem-parts")
    return page

def scrape_data():
    global entry_box
    instructions = []

    # Get entry box content
    entry_text = entry_box.get().strip()
    if not entry_text:
        print("No entry provided.")
        return instructions

    # Scrape data
    titles = ["First Choice", "Second Choice", "Third Choice", "Fourth Choice", "Fifth Choice", "Sixth Choice", "Parts Schematic"]

    for title in titles:
        selector = f"select[title='{title}']"
        try:
            if title == "First Choice":
                value = page.locator(selector).evaluate("element => element.options[element.selectedIndex].text", timeout = 500)
                if value == "Arctic Cat":
                    value = "Arctic-Cat"
            else:
                value = page.locator(selector).evaluate("element => element.value", timeout = 500)

            if value:
                print(f"Scraped {title}: {value}")
                instructions.append(value)
            else:
                print(f"No value found for {title}")

        except Exception as e:
            print(f"Error scraping {title}: {e}")
            continue

    # Append entry box content and clear it
    instructions.append(entry_text)
    entry_box.delete(0, "end")

    return instructions

def add_to_database(instructions):
    MPN = instructions[-1]
    brand = instructions[0]
    instructions = instructions[0:-1]
    
    print(f"Adding part '{MPN}' to database...")
    try:
        database.add_part(mpn=MPN, in_stock=1, price=0.00, brand=brand, instructions=instructions, part_id=None)
        print(f"Part {MPN} successfully added to database.")

    except Exception as e:
        print(f"Failed to add part {MPN} to database: {str(e)}")
        return

def click_button():
    # Signal the main thread to scrape data
    scrape_event.set()

def create_gui():
    global entry_box
    root = ctk.CTk()
    root.title("Scraper GUI")
    root.geometry("300x200")
    root.resizable(False, False)

    # Create entry box
    entry_box = ctk.CTkEntry(master=root, placeholder_text="Enter MPN", width=200)
    entry_box.pack(pady=(50, 10))

    # Create scrape button
    scrape_button = ctk.CTkButton(master=root, text="Scrape Data", command=click_button)
    scrape_button.pack(pady=(10, 50))

    root.mainloop()

def main():
    global scrape_event
    scrape_event = threading.Event()

    # Open browser in main thread
    open_browser()

    # Start GUI in a separate thread
    gui_thread = threading.Thread(target=create_gui)
    gui_thread.daemon = True
    gui_thread.start()

    try:
        # Main thread loop: check for scrape event
        while True:
            if scrape_event.is_set():
                instructions = scrape_data()
                if instructions:
                    add_to_database(instructions)
                scrape_event.clear()  # Reset event for next click
            page.wait_for_timeout(100)  # Short timeout to stay responsive

    except KeyboardInterrupt:
        print("Closing browser...")
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
        print("Browser closed.")

if __name__ == "__main__":
    main()
# This script is designed to scrape data from 'rockymountainatvmc.com' and add it to a database.
# It uses Playwright for web scraping and customtkinter for the GUI.
# The script is structured to run the GUI and scraping in separate threads to keep the UI responsive.
# The main function initializes the browser, starts the GUI, and handles the scraping logic.
# The script is designed to be run as a standalone application.
# It will open a browser window and a GUI window, allowing the user to find and enter a part number and scrape data from the website.
# Steps are: Run the script, click through a brand and choose random things in the dropdowns until you are
# brought to a schematic page. Highlight a part number, copy it, and paste it into the entry box of the GUI
# and click the scrape button. The part number will be added to the database.