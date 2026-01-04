import sqlite3
import os

db_path = r"C:/Nimrod/ai_ds_team/projects/football_betting/1_high_level_plan/planning_session.sqlite"

if not os.path.exists(db_path):
    print(f"❌ File not found at: {db_path}")
else:
    print(f"✅ File found! Size: {os.path.getsize(db_path)} bytes")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Check for stored threads
    try:
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
        threads = cursor.fetchall()
        print(f"🧵 Available Thread IDs in DB: {[t[0] for t in threads]}")
        
        # 2. Check if the 'values' actually exist
        if threads:
            last_thread = threads[-1][0]
            cursor.execute("SELECT checkpoint FROM checkpoints WHERE thread_id = ? ORDER BY step DESC LIMIT 1", (last_thread,))
            # This confirms if data is actually written or if it's just an empty table
            row = cursor.fetchone()
            if row:
                print("💎 Data found in the latest checkpoint!")
            else:
                print("⚠️ Table exists, but it appears to be empty.")
    except sqlite3.OperationalError as e:
        print(f"❌ Error reading tables: {e} (The DB might not have been initialised properly)")
    
    conn.close()