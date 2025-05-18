import database as db
import re
from playwright.sync_api import sync_playwright as pw

class Scraper:
    def __init__(self):
        self.URL = "https://www.rockymountainatvmc.com/oem-parts"

    def collect_info(self):
        results = []
        with pw() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(self.URL)
            page.wait_for_timeout(1000)

            items = db.make_parts_list()

            for item in items:
                mpn = item['MPN']
                instructions = item['Instructions']

                try:
                    self.nav(page, instructions)
                    page.wait_for_timeout(1000)

                except: #Retry if navigation fails
                    self.nav(page, instructions)
                    page.wait_for_timeout(1000)

                try:
                    info = self.get_part_info(page, mpn)
                    page.wait_for_timeout(1000)

                except: #Retry if getting part info fails
                    self.nav(page, instructions)
                    page.wait_for_timeout(1000)
                    info = self.get_part_info(page, mpn)
                    page.wait_for_timeout(1000)
                
                if info:
                    results.append({
                        "mpn": mpn,
                        "in_stock": info["In-Stock"],
                        "price": info["Price"],
                        "current_mpn": info["MPN"]
                    })
                    print(f"Scraped {mpn}: In-Stock: {info['In-Stock']}, Price: {info['Price']}, Current MPN: {info['MPN']}")
                else:
                    print(f"Part {mpn} not found or no info available.")
            
        for result in results:
            try:
                db.update_part(
                    mpn=result["mpn"],
                    in_stock=1 if result["in_stock"] else 0 if result["in_stock"] is not None else None,
                    price=result["price"],
                    new_mpn=result["current_mpn"] if result["current_mpn"] != result["mpn"] else None
                )
            except Exception as e:
                    print(f"Failed to update part {result['mpn']}: {str(e)}")

    def get_part_info(self, page, mpn):            
        try:
            page.wait_for_timeout(1000)
            table = page.locator("#oemparts_tblAssmDetails")
            if not table.is_visible():
                raise Exception("Table not found")

            rows = table.locator("tbody tr").all()

            for row in rows:
                part_num_cell = row.locator("td.partNum")
                try:
                    primary_mpn = part_num_cell.locator("span").first.inner_text().strip()
                except Exception as e:
                    print(f'Failed to get primary MPN: {str(e)}')
                    continue

                replaced_mpn = None
                try:
                    second_span = part_num_cell.locator("span").nth(1)
                    replaced_text = part_num_cell.locator('p').inner_text(timeout=1000).strip()
                    if replaced_text and "replaces part #" in replaced_text:
                        match = re.search(r'replaces part #\s*([\w-]+)', replaced_text)
                        if match:
                            replaced_mpn = match.group(1)
                except Exception as e:
                    replaced_mpn = None
                
                if mpn == primary_mpn or mpn == replaced_mpn:
                    in_stock_text = row.locator("td.status").inner_text(timeout=1000).strip()
                    msrp_text = row.locator("td.regPrice").inner_text(timeout=1000).strip()
                    our_price_text = row.locator("td.ourPrice").inner_text(timeout=1000).strip()

                    in_stock = "In-Stock" in in_stock_text

                    price = None
                    if our_price_text and our_price_text != "-" and "$" in our_price_text:
                        try:
                            price = float(our_price_text.replace("$", "").replace(",", "").strip())
                        except ValueError:
                            pass
                    elif msrp_text and msrp_text != "-" and "$" in msrp_text:
                        try:
                            price = float(msrp_text.replace("$", "").replace(",", "").strip())
                        except ValueError:
                            pass
                    
                    return {
                        "In-Stock": in_stock,
                        "Price": price,
                        "MPN": primary_mpn
                    }
                
            return None
            
        except Exception as e:
            raise Exception(f"Failed to get part info: {str(e)}")

    def nav(self, page, instructions):
        choice_titles = [
            "Second Choice",
            "Third Choice",
            "Fourth Choice",
            "Fifth Choice",
            "Sixth Choice"
        ]

        try:
            brand = instructions[0]
            page.goto(self.URL + f"/{brand}")
            page.wait_for_timeout(1000)

            for i, instruction in enumerate(instructions[1:-1], start=1):
                if i > 5:
                    break
                title = choice_titles[i - 1]
                selector = f"select[title='{title}']"
                page.locator(selector).select_option(value=instruction)
                page.wait_for_timeout(500)

            if len(instructions) > 1:
                final_instruction = instructions[-1]
                schematic_selector = "select[title='Parts Schematic']"
                page.locator(schematic_selector).select_option(value=final_instruction)
                page.wait_for_timeout(500)

            return page
        
        except Exception as e:
            print(f"Navigation Failed: {str(e)}")

if __name__ == "__main__":
    s = Scraper()
    s.collect_info()
# This code is designed to accept a list of instructions created by the database script.
# If you want to test this code, you should use the 'part_finder.py' script to add some parts
# to the database first, as it captures the instructions needed for the scraper to get to the 
# correct page. I am unable to use URL's to get to parts because the website is dynamic and the URL's
# change periodically.
# This script will gather the in-stock status and price of the parts in the database, and attempt to 
# update part numbers that are superceded by other part numbers.