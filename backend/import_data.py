import sqlite3
import yaml
import re
import os
from pathlib import Path

DB_PATH = "game.db"


def create_tables(conn):
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS monsters (
        id INTEGER PRIMARY KEY,
        aegis_name TEXT,
        name TEXT,
        level INTEGER,
        race TEXT,
        element TEXT,
        element_level INTEGER,
        base_exp INTEGER,
        job_exp INTEGER,
        hp INTEGER,
        size TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS drops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monster_id INTEGER,
        item_name TEXT,
        rate INTEGER,
        FOREIGN KEY(monster_id) REFERENCES monsters(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        aegis_name TEXT,
        name TEXT,
        type TEXT,
        subtype TEXT,
        item_class TEXT,
        buy INTEGER,
        sell INTEGER,
        weight INTEGER,
        atk INTEGER,
        def INTEGER,
        weapon_level INTEGER,
        equip_level_min INTEGER,
        refineable INTEGER,
        slots INTEGER,
        equip_locations TEXT,
        jobs TEXT,
        description TEXT,
        script TEXT
    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS monster_spawn (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        map_name TEXT,
        monster_id INTEGER,
        monster_name TEXT,
        amount INTEGER,
        FOREIGN KEY(monster_id) REFERENCES monsters(id)
    )
    """)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS npc_shops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        npc_name TEXT,
        map_name TEXT,
        x INTEGER,
        y INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS npc_shop_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_id INTEGER,
        item_id INTEGER,
        price_override INTEGER,
        FOREIGN KEY(shop_id) REFERENCES npc_shops(id),
        FOREIGN KEY(item_id) REFERENCES items(id)
    )
    """)


    conn.commit()


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def import_spawn_files(conn):
    cur = conn.cursor()
    spawn_base_path = Path("../data")

    total_spawn = 0

    for folder in ["fields", "dungeons"]:
        folder_path = spawn_base_path / folder

        if not folder_path.exists():
            continue

        for file in folder_path.glob("*.txt"):

            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:

                    if "\tmonster\t" not in line:
                        continue

                    try:
                        parts = line.strip().split("\t")

                        map_part = parts[0]
                        map_name = map_part.split(",")[0]

                        monster_name = parts[2].strip()

                        id_amount = parts[3].split(",")
                        monster_id = int(id_amount[0])
                        amount = int(id_amount[1])

                        cur.execute("""
                            INSERT INTO monster_spawn
                            (map_name, monster_id, monster_name, amount)
                            VALUES (?, ?, ?, ?)
                        """, (map_name, monster_id, monster_name, amount))

                        total_spawn += 1

                    except:
                        continue

    print(f"✅ Imported {total_spawn} spawn entries.")


def import_data():
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    cur = conn.cursor()

    # ----------------
    # Import Monsters
    # ----------------
    mob_data = load_yaml("../data/mob_db.yml")
    monsters = mob_data["Body"]

    for m in monsters:
        cur.execute("""
        INSERT OR REPLACE INTO monsters
        (id, aegis_name, name, level, race, element, element_level, base_exp, job_exp, hp, size)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m.get("Id"),
            m.get("AegisName"),
            m.get("Name"),
            m.get("Level"),
            m.get("Race"),
            m.get("Element"),
            m.get("ElementLevel"),
            m.get("BaseExp"),
            m.get("JobExp"),
            m.get("Hp"),
            m.get("Size"),
        ))

        for d in m.get("Drops", []):
            cur.execute("""
            INSERT INTO drops (monster_id, item_name, rate)
            VALUES (?, ?, ?)
            """, (
                m.get("Id"),
                d.get("Item"),
                d.get("Rate"),
            ))

    # ----------------
    # Import Items
    # ----------------

    item_files = [
        "../data/item_db_etc.yml",
        "../data/item_db_equip.yml",
        "../data/item_db_usable.yml",
    ]

    for file in item_files:
        data = load_yaml(file)
        items = data["Body"]

        for it in items:
            # --- Extract Equipment Fields Safely ---

            atk = it.get("Atk") or it.get("Attack")
            defense = it.get("Def") or it.get("Defense")
            weapon_level = it.get("WeaponLevel")
            equip_level_min = it.get("EquipLevelMin")
            subtype = it.get("SubType")
            if not equip_level_min:
                equip_level = it.get("EquipLevel")
                if isinstance(equip_level, dict):
                    equip_level_min = equip_level.get("Min")
            refineable = 1 if it.get("Refineable") else 0
            slots = it.get("Slots", 0)

            # Equip Locations (flatten dict)
            locations = it.get("Locations")
            equip_locations = None
            if isinstance(locations, dict):
                equip_locations = ", ".join([k for k, v in locations.items() if v])

            # Applicable Jobs (flatten dict)
            jobs_data = it.get("Jobs")
            jobs = None
            if isinstance(jobs_data, dict):
                jobs = ", ".join([k for k, v in jobs_data.items() if v])

            # Description (some files use "Desc", some use "Description")
            description = it.get("Desc") or it.get("Description")

            cur.execute("""
            INSERT OR REPLACE INTO items
            (id, aegis_name, name, type, subtype, item_class,
            buy, sell, weight,
            atk, def, weapon_level, equip_level_min,
            refineable, slots,
            equip_locations, jobs, description, script)
            VALUES (?, ?, ?, ?, ?, 
                    ?, ?, ?, ?, 
                    ?, ?, ?, ?, 
                    ?, ?, ?, ?, ?, ?)
            """, (
                it.get("Id"),
                it.get("AegisName"),
                it.get("Name"),
                it.get("Type"),
                subtype,
                it.get("Class"),
                it.get("Buy"),
                it.get("Sell"),
                it.get("Weight"),
                atk,
                defense,
                weapon_level,
                equip_level_min,
                refineable,
                slots,
                equip_locations,
                jobs,
                description,
                it.get("Script"),
            ))


    # ----------------
    # Import Spawn Data
    # ----------------
    import_spawn_files(conn)

    # ----------------
    # Import itemInfo.lua descriptions
    # ----------------
    import_item_info_lua(conn)

    import_shops(conn)

    conn.commit()
    conn.close()

def import_item_info_lua(conn):
    cur = conn.cursor()
    lua_path = Path("../data/itemInfo.lua")

    if not lua_path.exists():
        print("❌ itemInfo.lua not found.")
        return

    print("📘 Importing descriptions from itemInfo.lua...")

    updated = 0
    current_id = None
    inside_desc = False
    desc_lines = []

    with open(lua_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:

            # Detect item ID
            id_match = re.match(r"\s*\[(\d+)\]\s*=\s*\{", line)
            if id_match:
                current_id = int(id_match.group(1))
                continue

            # Detect start of identified description
            if "identifiedDescriptionName" in line:
                inside_desc = True
                desc_lines = []
                continue

            # Collect description lines
            if inside_desc:
                if "}" in line:
                    # End of description block
                    cleaned = []
                    for l in desc_lines:
                        l = re.sub(r"\^[0-9A-Fa-f]{6}", "", l)
                        l = l.strip()
                        if l:
                            cleaned.append(l)

                    description = "\n".join(cleaned)

                    if current_id:
                        cur.execute("""
                            UPDATE items
                            SET description = ?
                            WHERE id = ?
                        """, (description, current_id))
                        updated += 1

                    inside_desc = False
                    continue

                # Extract quoted text
                text_matches = re.findall(r'"(.*?)"', line)
                desc_lines.extend(text_matches)

    conn.commit()
    print(f"✅ Updated {updated} item descriptions from itemInfo.lua.")

def import_shops(conn):
    cur = conn.cursor()
    shop_path = Path("../data/shops.txt")

    if not shop_path.exists():
        print("❌ shops.txt not found.")
        return

    print("🛒 Importing NPC shops...")

    shop_count = 0
    item_count = 0

    with open(shop_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:

            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("//"):
                continue

            if "\tshop\t" not in line:
                continue

            try:
                parts = line.split("\t")

                # Left part: map,x,y,dir
                map_data = parts[0].split(",")
                map_name = map_data[0]
                x = int(map_data[1])
                y = int(map_data[2])

                npc_name = parts[2]

                # Insert shop
                cur.execute("""
                    INSERT INTO npc_shops (npc_name, map_name, x, y)
                    VALUES (?, ?, ?, ?)
                """, (npc_name, map_name, x, y))

                shop_id = cur.lastrowid
                shop_count += 1

                # Items list
                item_data = parts[3].split(",")

                for entry in item_data[1:]:  # skip sprite id
                    item_id_str, price_str = entry.split(":")
                    item_id = int(item_id_str)
                    price_override = int(price_str)

                    if price_override == -1:
                        price_override = None

                    cur.execute("""
                        INSERT INTO npc_shop_items (shop_id, item_id, price_override)
                        VALUES (?, ?, ?)
                    """, (shop_id, item_id, price_override))

                    item_count += 1

            except:
                continue

    conn.commit()
    print(f"✅ Imported {shop_count} shops with {item_count} items.")


if __name__ == "__main__":
    import_data()
    print("✅ Monster database imported successfully!")
