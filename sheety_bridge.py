import sqlite3
import requests

SHEETY_URL = "https://api.sheety.co/a55ee390e32ce641fdcf7198fce48745/lifeFitnessGym/members"

def sync_data():
    conn = sqlite3.connect("gym-app/gym_pro.db")
    cursor = conn.cursor()

    # Junk data ko filter karne ke liye specific query
    # Sirf wahi records lein jahan 'name' mein 'headcount' na ho
    cursor.execute("SELECT name, email, phone FROM members WHERE name NOT LIKE '%headcount%' AND name NOT LIKE '%member%'") 
    rows = cursor.fetchall()
    print(f"Total valid members found: {len(rows)}")

    for row in rows:
        name = row[0]
        email = row[1] if row[1] else ""
        phone = row[2] if row[2] else ""

        # Sirf tabhi sync karein agar naam valid ho
        if name and len(name) > 2:
            member_data = {
                "member": {
                    "firstName": name,
                    "email": email,
                    "phone": phone
                }
            }

            response = requests.post(SHEETY_URL, json=member_data)
            print(f"Syncing {name}... Status: {response.status_code}")

    conn.close()

if __name__ == "__main__":
    sync_data()
