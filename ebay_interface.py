from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError
import yaml
import json
import database as db

class EbayAPIInterface:
    def __init__(self):
        try:
            with open("ebay.yaml", "r") as file:
                self.config = yaml.safe_load(file)

        except FileNotFoundError:
            print("eBay configuration file not found. Please ensure 'ebay_config.yaml' exists.")
            self.config = None


    def calculate_price(self, rm_price):
        def round_to_nearest(num, base=5):
            # Format of ###.95
            return (base * round(num / base)) - 0.02
        
        total = rm_price + 0.3  # 30 cent transaction fee
        if total < 75:
            total += 7

        if total < 25:
            total = (total + 5) / 0.88
        elif total <= 50:
            total = (total + 10) / 0.88
        elif total <= 100:
            total = (total * 1.3) / 0.88
        elif total <= 200:
            total = (total * 1.35) / 0.88
        elif total > 200:
            total = (total * 1.4) / 0.88

        total = round_to_nearest(total, 5)

        return total
            

    def make_update_list(self):
        with open("ebay_listings.json", "r") as file:
            data = json.load(file)
        update_list = []

        for item in data:
            part_id = item.get('ItemID')
            mpn = item.get('ItemSpecifics', [])[0] if item.get('ItemSpecifics') else None
            our_price = item.get('Price', {}).get('Value', 0)

            row = db.get_part(mpn=mpn)
            rm_price = row[2]
            total = self.calculate_price(rm_price)
            if total != our_price:
                update_list.append((part_id, total))
                print(f"ItemID: {part_id}, MPN: {mpn}, RM Price: {rm_price}\n eBay Price: {our_price}\n New Price: {total}")

        return update_list


    def update_ebay_listings(self, change_list: list):
        errorlist = []
        for item in change_list:
            if not isinstance(item, tuple) or len(item) != 2:
                print(f"Invalid item format: {item}. Expected (ItemID, new_price).")
                return

            itemID, new_price = item
            if not isinstance(itemID, str) or not isinstance(new_price, (int, float)):
                print(f"Invalid item data: {item}. ItemID should be a string and new_price should be a number.")
                return

        for itemID, new_price in change_list:
            try:
                api = Trading(
                    appid=self.config["appid"],
                    devid=self.config["devid"],
                    certid=self.config["certid"],
                    token=self.config["token"],
                    config_file=None,
                    siteid="0"
                )

                request = {
                    'Item': {
                        'ItemID': itemID,
                        'StartPrice': new_price
                    }
                }

                response = api.execute('ReviseFixedPriceItem', request).dict()
                print(f"Updated ItemID {itemID} to new price: {new_price}")

            except ConnectionError as e:
                print(f"Failed to connect to eBay API: {e}")
                errorlist.append(itemID)
                api = None
                if "Auction ended" in str(e):
                    continue
                else:
                    return

            except Exception as e:
                print(f"Error with {itemID}: {e}")
                api = None
                errorlist.append(itemID)
                continue

        if errorlist:
            print()
            print(f"Error List:")
            for item in errorlist:
                print(item)


    def get_all_active_listings(self):
        try:
            api = Trading(
                appid=self.config["appid"],
                devid=self.config["devid"],
                certid=self.config["certid"],
                token=self.config["token"],
                config_file=None,
                siteid="0"
            )

            request = {
                'ActiveList': {
                    'Include': True,
                    'Pagination': {
                        'EntriesPerPage': 100,
                        'PageNumber': 1
                    }
                },
                'DetailLevel': 'ReturnAll'
            }

            listings_data = []
            page_num = 1

            while True:
                request['ActiveList']['Pagination']['PageNumber'] = page_num
                response = api.execute('GetMyeBaySelling', request).dict()

                # Check if ActiveList exists and has items
                if 'ActiveList' not in response or 'ItemArray' not in response['ActiveList']:
                    break

                items = response['ActiveList']['ItemArray'].get('Item', [])
                if not items:
                    break

                # Process each item
                for item in items if isinstance(items, list) else [items]:
                    item_id = item.get('ItemID', 'N/A')
                    listing_info = {
                        'ItemID': item_id,
                        'Price': {
                            'Currency': item.get('SellingStatus', {}).get('CurrentPrice', {}).get('_currencyID', 'N/A'),
                            'Value': item.get('SellingStatus', {}).get('CurrentPrice', {}).get('value', 'N/A')
                        },
                        'ItemSpecifics': []
                    }

                    # Use GetItem to get full details
                    try:
                        item_response = api.execute('GetItem', {
                            'ItemID': item_id,
                            'DetailLevel': 'ReturnAll',
                            'IncludeItemSpecifics': True
                        }).dict()

                        specifics = item_response.get('Item', {}).get('ItemSpecifics', {}).get('NameValueList', [])
                        if isinstance(specifics, dict):
                            specifics = [specifics]

                        for spec in specifics:
                            name = spec.get('Name', '').strip()
                            if name.lower() == 'manufacturer part number':
                                value = spec.get('Value', 'N/A')
                                if isinstance(value, list):
                                    value = value[0]  # just in case it's a list
                                listing_info['ItemSpecifics'].append(value)
                                break

                    except Exception as e:
                        print(f"Failed to fetch details for ItemID {item_id}: {e}")

                    listings_data.append(listing_info)

                # Check for more pages
                pagination = response['ActiveList'].get('PaginationResult', {})
                total_pages = int(pagination.get('TotalNumberOfPages', 1))
                if page_num >= total_pages:
                    break
                page_num += 1

            with open("ebay_listings.json", "w") as outfile:
                json.dump(listings_data, outfile, indent=4)

            print(f"eBay listings data saved to ebay_listings.json")

        except ConnectionError as e:
            print(f"Failed to connect to eBay API: {e}")
            api = None

    def update_ids(self):
        with open("ebay_listings.json", "r") as file:
            data = json.load(file)

        for item in data:
            part_id = item.get('ItemID')
            mpn = item.get('ItemSpecifics', [])[0] if item.get('ItemSpecifics') else None

            try:
                db.update_ID(mpn=mpn, part_id=part_id)
            except Exception as e:
                print(f"Failed to update ID for MPN {mpn}: {str(e)}")
                continue


if __name__ == "__main__":
    ebay_api = EbayAPIInterface()
    ebay_api.get_all_active_listings()
    #ebay_api.update_ebay_listings([("167510454982", 400.00)])
    # Example usage
    # ebay_api.update_ebay_listings([("1234567890", 19.99), ("0987654321", 29.99)])

# For security reasons, this script will not work because a key is required to access
# eBay's APIs. However, I can explain how it works.
# The script uses the ebaysdk library to interact with eBay's Trading API.
# It retrieves all active listings from the user's eBay account and saves them to a JSON file.
# It is able to read the json file and update the parts in the database (the 'ID' part) so that
# the information in the database can be linked directly to the eBay listings on your store.
# The script also includes a function to calculate the price based on Rocky Mountain pricing,
# including transaction fees and shipping costs. This includes the desired margin of profit.
