import sqlite3

DB_PATH = "game.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("----- DATABASE SUMMARY -----")

    # Total counts
    tables = ["monsters", "items", "monster_spawn", "drops"]

    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"{table}: {count}")

    print("\n----- CHECK UNKNOWN DESCRIPTION COUNT -----")

    cur.execute("""
        SELECT COUNT(*)
        FROM items
        WHERE description = 'Unknown Item, can be identified by using a Magnifier.'
    """)
    unknown_count = cur.fetchone()[0]
    print(f"Items with 'Unknown Item' description: {unknown_count}")

    print("\n----- CHECK JUNGLE CARBINE ENTRIES -----")

    cur.execute("""
        SELECT id, name, substr(description,1,120)
        FROM items
        WHERE name LIKE '%Jungle Carbine%'
    """)

    rows = cur.fetchall()

    if not rows:
        print("No Jungle Carbine found.")
    else:
        for row in rows:
            print(f"\nID: {row[0]}")
            print(f"Name: {row[1]}")
            print(f"Description Preview: {row[2]}")

    print("\n----- CHECK RANDOM ITEM WITH DESCRIPTION -----")

    cur.execute("""
        SELECT id, name, substr(description,1,120)
        FROM items
        WHERE description IS NOT NULL
        LIMIT 5
    """)

    for row in cur.fetchall():
        print(f"\nID: {row[0]}")
        print(f"Name: {row[1]}")
        print(f"Description Preview: {row[2]}")

    conn.close()


if __name__ == "__main__":
    main()
