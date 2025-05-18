import scraper
import database as db
import part_finder as pf
import ebay_interface
import customtkinter as ctk
import threading
from playwright.sync_api import sync_playwright

class App:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.geometry("400x350")
        self.root.title("Part Scraper")
        
        # Initialize Variables
        self.scraper = scraper.Scraper()
        self.database = 'parts_database.db'
        self.interface = ebay_interface.EbayAPIInterface()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Create GUI Elements
        self.create_gui()

    def create_gui(self):
        self.entry_box = ctk.CTkEntry(master=self.root, placeholder_text="Enter MPN", width=200)
        self.entry_box.pack(pady=(50, 10))
        self.find_button = ctk.CTkButton(master=self.root, text="Find Part", command=self.find_part)
        self.find_button.pack(pady=10)
        self.update_button = ctk.CTkButton(master=self.root, text="Run Update", command=self.run_update)
        self.update_button.pack(pady=10)
        self.status_label = ctk.CTkLabel(master=self.root, text="Status: Ready")
        self.status_label.pack(pady=(10, 50))
        self.add_button = ctk.CTkButton(master=self.root, text="Add Parts", command=self.add_parts_button)
        self.add_button.pack(pady=10, side="left", padx=(50, 10))
        self.scrape_button = ctk.CTkButton(master=self.root, text="Scrape Data", command=self.scrape_and_add)
        self.scrape_button.pack(pady=10, side="left", padx=(10, 50))

    def add_parts_button(self):
        try:
            self.status_label.configure(text="Status: Opening browser...")
            self.root.update()
            self.open_browser()
            self.status_label.configure(text="Status: Browser Opened Successfully")
            self.root.update()
        except Exception as e:
            self.status_label.configure(text=f"Status: Error - {str(e)}")
            print(f"Error in add_parts_button: {str(e)}")

    def open_browser(self):
        if not self.page:
            self.playwright, self.browser, self.context, self.page = pf.open_browser()
        else:
            self.page.goto("https://www.rockymountainatvmc.com/oem-parts")

    def scrape_and_add(self):
        try:
            self.status_label.configure(text="Status: Scraping...")
            self.root.update()
            mpn = self.entry_box.get().strip()
            if not mpn:
                self.status_label.configure(text="Status: Error - No MPN provided")
                self.root.update()
                return
            if not self.page:
                self.status_label.configure(text="Status: Error - Browser not open")
                self.root.update()
                return
            instructions = pf.scrape_data(self.page, mpn)
            if instructions:
                pf.add_to_database(instructions)
                self.status_label.configure(text=f"Status: Part {mpn} Added Successfully")
                self.entry_box.delete(0, "end")
            else:
                self.status_label.configure(text="Status: No Data Scraped")
            self.root.update()
        except Exception as e:
            self.status_label.configure(text=f"Status: Error - {str(e)}")
            print(f"Error in scrape_and_add: {str(e)}")
            self.root.update()

    def find_part(self):
        try:
            self.status_label.configure(text="Status: Finding part...")
            self.root.update()
            part = db.get_part(mpn=self.entry_box.get())
            if part:
                in_stock = "In Stock" if part[1] == 1 else "Out of Stock"
                price = part[2]
                self.status_label.configure(text=f"Status: Part Found - {in_stock}, ${price}")
            else:
                self.status_label.configure(text="Status: Part Not Found")
            self.root.update()
        except Exception as e:
            self.status_label.configure(text=f"Status: Error - {str(e)}")
            print(f"Error in find_part: {str(e)}")
            self.root.update()

    def run_update(self):
        threading.Thread(target=self.update_parts, daemon=True).start()

    def update_parts(self):
        try:
            self.status_label.configure(text="Status: Scraping...")
            self.root.update()
            self.scraper.collect_info()
            self.status_label.configure(text="Status: Scraping Complete - Grabbing eBay Listings...")
            self.root.update()
            self.interface.get_all_active_listings()
            self.status_label.configure(text="Status: eBay Listings Retrieved - Updating Ids...")
            self.root.update()
            self.interface.update_ids()
            self.status_label.configure(text="Status: IDs Updated - Preparing Update List...")
            self.root.update()
            update_list = self.interface.make_update_list()
            self.status_label.configure(text="Status: Update List Created - Updating eBay Listings...")
            self.root.update()
            self.interface.update_ebay_listings(update_list)
            self.status_label.configure(text="Status: eBay Listings Updated Successfully!")
            self.root.update()
            
        except Exception as e:
            self.status_label.configure(text=f"Status: Error - {str(e)}")
            print(f"Error in update: {str(e)}")
            self.root.update()

    def cleanup_playwright(self):
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"Error cleaning up Playwright: {str(e)}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    def start(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        self.cleanup_playwright()
        self.root.destroy()

if __name__ == "__main__":
    app = App()
    app.start()