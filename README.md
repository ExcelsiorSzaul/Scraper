# Scraper
This is a project I am rewriting in my personal time to improve my abilities. It is based on a program I made, unprompted, to solve an issue at my job. It is currently being improved upon with the incorporation of a database. Still a work in progress, but I am quite happy with it so far.

Here are the notes for each script:

database.py
# This showcases that the database's functionality through a 
# series of operations: creating the database, adding parts, updating parts,
# retrieving parts, and deleting all parts. The script is designed to be run
# as a standalone program, and it will create a database file named "parts_database.db"
# The numbers here are example values and don't actually work with the scraper.

part_finder.py
# This script is designed to scrape data from 'rockymountainatvmc.com' and add it to a database.
# It uses Playwright for web scraping and customtkinter for the GUI.
# The script is structured to run the GUI and scraping in separate threads to keep the UI responsive.
# The main function initializes the browser, starts the GUI, and handles the scraping logic.
# The script is designed to be run as a standalone application.
# It will open a browser window and a GUI window, allowing the user to find and enter a part number and scrape data from the website.
# Steps are: Run the script, click through a brand and choose random things in the dropdowns until you are
# brought to a schematic page. Highlight a part number, copy it, and paste it into the entry box of the GUI
# and click the scrape button. The part number will be added to the database.

scraper.py
# This code is designed to accept a list of instructions created by the database script.
# If you want to test this code, you should use the 'part_finder.py' script to add some parts
# to the database first, as it captures the instructions needed for the scraper to get to the 
# correct page. I am unable to use URL's to get to parts because the website is dynamic and the URL's
# change periodically.
# This script will gather the in-stock status and price of the parts in the database, and attempt to 
# update part numbers that are superceded by other part numbers.

ebay_interface.py
# For security reasons, this script will not work because a key is required to access
# eBay's APIs. However, I can explain how it works.
# The script uses the ebaysdk library to interact with eBay's Trading API.
# It retrieves all active listings from the user's eBay account and saves them to a JSON file.
# It is able to read the json file and update the parts in the database (the 'ID' part) so that
# the information in the database can be linked directly to the eBay listings on your store.
# The script also includes a function to calculate the price based on Rocky Mountain pricing,
# including transaction fees and shipping costs. This includes the desired margin of profit.

Thank you for stopping by!
