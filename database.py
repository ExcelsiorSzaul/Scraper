import sqlite3
from datetime import date
import json

"""
This script manages a SQLite database for parts inventory.
It includes functions to create the database, add parts, update parts, remove parts,
retrieve parts, and delete all parts.
"""

def create_database():
    # Connect to the database (creates a new file if it doesn’t exist)
    conn = sqlite3.connect("parts_database.db")
    cursor = conn.cursor()

    # Create the table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parts (
            MPN TEXT PRIMARY KEY,
            "In-Stock" INTEGER NOT NULL,  -- 0 for False, 1 for True
            Price REAL NOT NULL,
            Brand TEXT NOT NULL,
            Instructions TEXT NOT NULL,  -- Stores JSON string of list, e.g., "[1,2,3]"
            ID INTEGER DEFAULT NULL,
            Date TEXT NOT NULL
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Database and table created successfully!")


def update_ID(mpn, part_id):
    try:
        conn = sqlite3.connect("parts_database.db")
        cursor = conn.cursor()

        # Update the ID for the part with the given MPN
        cursor.execute('''
            UPDATE parts SET ID = ? WHERE MPN = ?
        ''', (part_id, mpn))

        # Check if any rows were affected
        if cursor.rowcount == 0:
            raise Exception(f"No part found with MPN {mpn}")

        conn.commit()
        conn.close()

        print(f"ID for part {mpn} updated to {part_id} successfully!")
        
    except Exception as e:
        print(f"Failed to update ID for {mpn}: {str(e)}")
        raise


def update_part(mpn: str, in_stock: int = None, price: float = None, new_mpn: str = None):
    """
    Update a part's In-Stock, Price, Date, and optionally MPN in the database.
    
    Args:
        mpn: Current MPN of the part.
        in_stock: 1 for True, 0 for False, None to skip.
        price: New price, None to skip.
        new_mpn: New MPN if the part number has changed, None to skip.
    """
    try:
        conn = sqlite3.connect("parts_database.db")
        cursor = conn.cursor()

        # Get current date
        today = date.today().strftime("%Y-%m-%d")

        if new_mpn and new_mpn != mpn:
            # Copy existing record to new MPN with updated Date, then delete old record
            cursor.execute("""
                INSERT INTO parts (MPN, "In-Stock", Price, Brand, Instructions, ID, Date)
                SELECT ?, "In-Stock", Price, Brand, Instructions, ID, ?
                FROM parts WHERE MPN = ?
            """, (new_mpn, today, mpn))
            cursor.execute("DELETE FROM parts WHERE MPN = ?", (mpn,))
            mpn = new_mpn  # Update mpn for further updates

        updates = ["Date = ?"]  # Always update Date
        values = [today]
        if in_stock is not None:
            updates.append('"In-Stock" = ?')
            values.append(in_stock)
        if price is not None:
            updates.append('Price = ?')
            values.append(price)

        if updates:
            query = f'UPDATE parts SET {", ".join(updates)} WHERE MPN = ?'
            values.append(mpn)
            cursor.execute(query, values)

        conn.commit()
        conn.close()

        print(f"Part {mpn} updated successfully!")
        
    except Exception as e:
        print(f"Database update failed for {mpn}: {str(e)}")
        raise


def add_part(mpn, in_stock, price, brand, instructions, part_id):
    # Connect to the database
    conn = sqlite3.connect("parts_database.db")
    cursor = conn.cursor()

    # Get today's date
    today = date.today().strftime("%Y-%m-%d")

    # Convert instructions list to JSON string
    instructions_json = json.dumps(instructions)

    # Insert the part into the table
    cursor.execute('''
        INSERT INTO parts (MPN, "In-Stock", Price, Brand, Instructions, ID, Date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (mpn, in_stock, price, brand, instructions_json, part_id, today))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print(f"Part {mpn} added successfully!")


def remove_part(mpn):
    # Connect to the database
    conn = sqlite3.connect("parts_database.db")
    cursor = conn.cursor()

    # Delete the part from the table
    cursor.execute('''
        DELETE FROM parts WHERE MPN = ?
    ''', (mpn,))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print(f"Part {mpn} removed successfully!")


def get_all_parts():
    # Connect to the database
    conn = sqlite3.connect("parts_database.db")
    cursor = conn.cursor()

    # Retrieve all parts from the table
    cursor.execute('SELECT * FROM parts')
    parts = cursor.fetchall()

    # Close the connection
    conn.close()

    # Convert Instructions JSON string to list
    parsed_parts = []
    for part in parts:
        try:
            instructions = json.loads(part[4])  # Parse JSON string to list
        except json.JSONDecodeError:
            instructions = []  # Fallback to empty list on error
        parsed_parts.append((part[0], part[1], part[2], part[3], instructions, part[5], part[6]))
    
    return parsed_parts


def get_part(mpn):
    # Connect to the database
    conn = sqlite3.connect("parts_database.db")
    cursor = conn.cursor()

    # Retrieve the part from the table
    cursor.execute('SELECT * FROM parts WHERE MPN = ?', (mpn,))
    part = cursor.fetchone()

    # Close the connection
    conn.close()

    # Parse Instructions JSON string to list
    if part:
        try:
            instructions = json.loads(part[4])  # Parse JSON string to list
        except json.JSONDecodeError:
            instructions = []  # Fallback to empty list on error
        return (part[0], part[1], part[2], part[3], instructions, part[5], part[6])
    
    return None


def make_parts_list():
    # Connect to the database
    conn = sqlite3.connect("parts_database.db")
    cursor = conn.cursor()

    # Retrieve all parts from the table
    cursor.execute('SELECT * FROM parts')
    parts = cursor.fetchall()

    # Close the connection
    conn.close()

    # Create a list of dictionaries for each part
    parts_list = []
    for part in parts:
        try:
            instructions = json.loads(part[4])  # Parse JSON string to list
        except json.JSONDecodeError:
            instructions = []  # Fallback to empty list on error
        part_dict = {
            "MPN": part[0],
            "In-Stock": bool(part[1]),  # Convert to boolean
            "Price": part[2],
            "Brand": part[3],
            "Instructions": instructions,  # Store as list
            "ID": part[5],
            "Date": part[6]
        }
        parts_list.append(part_dict)

    return parts_list


def delete_all_parts():
    # Connect to the database
    conn = sqlite3.connect("parts_database.db")
    cursor = conn.cursor()

    # Delete all parts from the table
    cursor.execute('DELETE FROM parts')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("All parts removed successfully!")

if __name__ == "__main__":
    create_database()
    add_part("0470-877", 1, 19.99, "Arctic-Cat", ['Arctic-Cat', "14138", "14987", "15033", "7133"], None)
    add_part("0470-111", 1, 19.99, "Honda", ['Honda', "23564", "18216", "18851", "84651"], None)
    print(f'All Parts In Database: {get_all_parts()}')
    update_ID("0470-877", 123456)
    print(get_part("0470-877"))
    update_part("0470-877", in_stock=0, price=99.99)
    print(get_part("0470-877"))
    delete_all_parts()
    print(f'All Parts Remaining In Database: {get_all_parts()}')
    print('Thank you for using the parts database script!') 
# This showcases that the database's functionality through a 
# series of operations: creating the database, adding parts, updating parts,
# retrieving parts, and deleting all parts. The script is designed to be run
# as a standalone program, and it will create a database file named "parts_database.db"
# The numbers here are example values and don't actually work with the scraper.