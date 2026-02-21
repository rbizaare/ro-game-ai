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


    cur.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skid TEXT UNIQUE,
        prefix TEXT,
        job_class TEXT,
        name TEXT,
        max_level INTEGER,
        skill_form TEXT,
        target TEXT,
        property TEXT,
        requirement TEXT,
        description TEXT,
        level_data TEXT
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

    import_skilldescript_lua(conn)

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


SKID_PREFIX_TO_JOB = {
    "NV": "Novice", "SM": "Swordsman", "MG": "Mage", "AL": "Acolyte",
    "MC": "Merchant", "AC": "Archer", "TF": "Thief",
    "KN": "Knight", "PR": "Priest", "WZ": "Wizard", "BS": "Blacksmith",
    "HT": "Hunter", "AS": "Assassin", "RG": "Rogue", "CR": "Crusader",
    "MO": "Monk", "SA": "Sage", "BA": "Bard", "DC": "Dancer",
    "LK": "Lord Knight", "HP": "High Priest", "HW": "High Wizard",
    "WS": "Whitesmith", "SN": "Sniper", "ASC": "Assassin Cross",
    "PA": "Paladin", "CH": "Champion", "PF": "Professor",
    "CG": "Clown/Gypsy", "BD": "Bard/Dancer Ensemble",
    "SL": "Soul Linker", "ST": "Soul Linker",
    "SG": "Star Gladiator", "TK": "Taekwon",
    "GS": "Gunslinger", "NJ": "Ninja",
    "RK": "Rune Knight", "GC": "Guillotine Cross", "RA": "Ranger",
    "NC": "Mechanic", "WM": "Minstrel/Wanderer", "SO": "Sorcerer",
    "GN": "Geneticist", "AB": "Arch Bishop", "WL": "Warlock",
    "SR": "Sura", "MI": "Minstrel", "MA": "Ranger",
    "LG": "Royal Guard", "SC": "Shadow Chaser",
    "KO": "Kagerou/Oboro", "OB": "Kagerou/Oboro", "KG": "Kagerou/Oboro",
    "RL": "Rebellion", "AM": "Alchemist",
    "GD": "Guild", "ALL": "All Classes",
    "HAMI": "Homunculus", "HFLI": "Homunculus",
    "HLIF": "Homunculus", "HVAN": "Homunculus",
    "MH": "Homunculus S", "MER": "Mercenary",
    "ML": "Mercenary", "MS": "Mercenary", "MB": "Mercenary",
    "DA": "Summoner", "EL": "Elemental",
    "WA": "Wanderer",
}

SKIP_SKILL_PREFIXES = {
    "GM", "NPC", "ITEM", "ITM", "CASH", "SKILL",
    "RETURN", "XX", "FOLLOWER", "ECLAGE", "ECL", "WE", "DE",
}


def _strip_color(text):
    return re.sub(r"\^[0-9A-Fa-f]{6}", "", text)


def _process_skill_entry(cur, skid, lines):
    parts = skid.split("_", 1)
    prefix = parts[0]

    if prefix in SKIP_SKILL_PREFIXES:
        return False

    job_class = SKID_PREFIX_TO_JOB.get(prefix, "Unknown")

    # Strip color codes from all lines
    lines = [_strip_color(l).strip() for l in lines]
    lines = [l for l in lines if l]

    if not lines:
        return False

    name = lines[0]
    max_level = None
    skill_form = None
    target = None
    prop = None
    requirement_parts = []
    description_parts = []
    level_lines = []
    in_description = False
    in_requirement = False

    for l in lines[1:]:
        lv_match = re.match(r"MAX Lv\s*:\s*(\d+)", l)
        if lv_match:
            max_level = int(lv_match.group(1))
            in_description = False
            in_requirement = False
            continue

        form_match = re.search(r"Skill Form:\s*(.+)", l)
        if form_match:
            skill_form = form_match.group(1).strip()
            in_description = False
            in_requirement = False
            continue

        target_match = re.search(r"Target:\s*(.+)", l)
        if target_match:
            target = target_match.group(1).strip()
            in_description = False
            in_requirement = False
            continue

        prop_match = re.search(r"Property:\s*(.+)", l)
        if prop_match:
            prop = prop_match.group(1).strip()
            in_description = False
            in_requirement = False
            continue

        # Skill Requirement (may have leading digit like "2Skill Requirement")
        req_match = re.search(r"(?:\d+)?Skill Requirement\s*:\s*(.+)", l)
        if req_match:
            requirement_parts.append(req_match.group(1).strip())
            in_description = False
            in_requirement = True
            continue

        # Level data
        lv_data_match = re.match(r"\[Lv(?:el)?\s*\d+\]\s*:?\s*(.*)", l)
        if lv_data_match:
            level_lines.append(l)
            in_description = False
            in_requirement = False
            continue

        desc_match = re.search(r"Description:\s*(.+)", l)
        if desc_match:
            description_parts = [desc_match.group(1).strip()]
            in_description = True
            in_requirement = False
            continue

        # Continuation lines
        if in_requirement:
            requirement_parts.append(l)
        elif in_description:
            description_parts.append(l)

    requirement = " ".join(requirement_parts).rstrip(",").strip() if requirement_parts else None
    # Clean up double spaces and trailing commas from multi-line requirements
    if requirement:
        requirement = re.sub(r"\s+", " ", requirement).rstrip(",").strip()
    description = " ".join(description_parts) if description_parts else None
    level_data = "\n".join(level_lines) if level_lines else None

    cur.execute("""
        INSERT OR REPLACE INTO skills
        (skid, prefix, job_class, name, max_level, skill_form,
         target, property, requirement, description, level_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (skid, prefix, job_class, name, max_level, skill_form,
          target, prop, requirement, description, level_data))
    return True


def import_skilldescript_lua(conn):
    cur = conn.cursor()
    lua_path = Path("../data/skilldescript.lua")

    if not lua_path.exists():
        print("skilldescript.lua not found.")
        return

    print("Importing skills from skilldescript.lua...")

    count = 0
    current_skid = None
    current_lines = []

    with open(lua_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            entry_match = re.match(r'\s*\[SKID\.(\w+)\]\s*=\s*\{', line)
            if entry_match:
                if current_skid and current_lines:
                    if _process_skill_entry(cur, current_skid, current_lines):
                        count += 1
                current_skid = entry_match.group(1)
                current_lines = []
                continue

            if re.match(r'\s*\},?\s*$', line) and current_skid:
                if current_lines:
                    if _process_skill_entry(cur, current_skid, current_lines):
                        count += 1
                current_skid = None
                current_lines = []
                continue

            if current_skid:
                text_matches = re.findall(r'"(.*?)"', line)
                current_lines.extend(text_matches)

    # Handle last entry
    if current_skid and current_lines:
        if _process_skill_entry(cur, current_skid, current_lines):
            count += 1

    conn.commit()
    print(f"Imported {count} skills from skilldescript.lua.")


if __name__ == "__main__":
    import_data()
    print("Monster database imported successfully!")
