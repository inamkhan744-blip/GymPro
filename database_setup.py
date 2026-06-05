# database_setup.py - Ye file banayein aur run karein

import sqlite3

def setup_database():
    conn = sqlite3.connect('gym_pro_v3.db')
    cursor = conn.cursor()
    
    # Drop old table if exists (BACKUP PEHLE LE LEIN!)
    cursor.execute('DROP TABLE IF EXISTS members')
    
    # Create new table with correct schema
    cursor.execute('''
    CREATE TABLE members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        joining_date DATE,
        plan TEXT,
        fee_amount REAL,
        status TEXT DEFAULT 'active',
        payment_date DATE,
        next_payment_date DATE
    )
    ''')
    
    # Sample data insert karein
    sample_members = [
        ('Ali Ahmed', '03001234567', 'ali@gmail.com', '2024-01-15', 'Monthly', 3000, 'active', '2024-01-15', '2024-02-15'),
        ('Hassan Khan', '03121234567', 'hassan@gmail.com', '2024-01-10', 'Monthly', 3000, 'pending', '2024-01-10', '2024-02-10'),
        ('Sara Fatima', '03211234567', 'sara@gmail.com', '2024-01-05', 'Quarterly', 8000, 'active', '2024-01-05', '2024-04-05'),
        ('Usman Ali', '03331234567', 'usman@gmail.com', '2023-12-20', 'Monthly', 3000, 'pending', '2023-12-20', '2024-01-20'),
        ('Ayesha Siddiqui', '03451234567', 'ayesha@gmail.com', '2024-01-20', 'Yearly', 30000, 'active', '2024-01-20', '2025-01-20')
    ]
    
    cursor.executemany('''
    INSERT INTO members (name, phone, email, joining_date, plan, fee_amount, status, payment_date, next_payment_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_members)
    
    conn.commit()
    
    # Verify data
    cursor.execute('SELECT COUNT(*) FROM members')
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM members WHERE status = 'active'")
    active = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM members WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    
    print(f"✅ Database setup complete!")
    print(f"📊 Total members: {total}")
    print(f"✅ Active members: {active}")
    print(f"⏰ Pending fees: {pending}")
    
    conn.close()

if __name__ == "__main__":
    setup_database()