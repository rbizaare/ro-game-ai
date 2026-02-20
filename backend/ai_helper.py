print("### AI_HELPER LOADED FROM:", __file__)

import os
import sqlite3
import re
from dotenv import load_dotenv
from openai import OpenAI


# ----------------------
# CONFIG
# ----------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "game.db")

ITEM_CACHE = None
SUBTYPE_CACHE = None
MONSTER_CACHE = None
ARMOR_LOCATION_CACHE = None

sort_keywords = [
            "attack speed",
            "aspd",
            "attack",
            "atk",
            "defense",
            "def",
            "weight"
        ]

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


# ----------------------
# DB CONNECTION
# ----------------------

def get_db():
    return sqlite3.connect(DB_PATH)

# Loaders
def load_item_cache():
    global ITEM_CACHE
    if ITEM_CACHE is None:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT name, aegis_name, slots FROM items")
        ITEM_CACHE = cur.fetchall()
        conn.close()
    return ITEM_CACHE

def load_subtypes():
    global SUBTYPE_CACHE
    if SUBTYPE_CACHE is None:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT subtype FROM items WHERE subtype IS NOT NULL")
        SUBTYPE_CACHE = [row[0] for row in cur.fetchall() if row[0]]
        conn.close()
    return SUBTYPE_CACHE

def load_monster_cache():
    global MONSTER_CACHE
    if MONSTER_CACHE is None:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT name FROM monsters")
        MONSTER_CACHE = [row[0] for row in cur.fetchall()]
        conn.close()
    return MONSTER_CACHE

def load_armor_locations():
    global ARMOR_LOCATION_CACHE
    if ARMOR_LOCATION_CACHE is None:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT equip_locations 
            FROM items 
            WHERE lower(type) = 'armor'
        """)
        ARMOR_LOCATION_CACHE = [row[0] for row in cur.fetchall() if row[0]]
        conn.close()
    return ARMOR_LOCATION_CACHE


# ----------------------
# HELPER FUNCTIONS
# ----------------------

def detect_effect_keywords(question):
    q = question.lower()

    effect_registry = {
        "agi": ["agi", "agility"],
        "str": ["str", "strength"],
        "vit": ["vit", "vitality"],
        "int": ["int", "intelligence"],
        "dex": ["dex", "dexterity"],
        "luk": ["luk", "luck"],

        "atk": ["atk", "attack"],
        "matk": ["matk", "magic attack"],
        "def": ["def", "defense"],
        "mdef": ["mdef", "magic defense"],
        "aspd": ["aspd", "attack speed"],
        "hit": ["hit"],
        "flee": ["flee", "dodge"],
        "crit": ["crit", "critical"],

        "demihuman": ["demihuman"],
        "demon": ["demon"],
        "undead": ["undead"],
        "brute": ["brute"],
        "angel": ["angel"],
        "dragon": ["dragon"],
        "insect": ["insect"],
        "fish": ["fish"],
        "plant": ["plant"],
        "formless": ["formless"],

        # Elements
        "fire": ["fire"],
        "water": ["water"],
        "wind": ["wind"],
        "earth": ["earth"],
        "holy": ["holy"],
        "shadow": ["shadow"],
        "ghost": ["ghost"],
        "poison": ["poison"],
        "neutral": ["neutral"],

        # Status effects
        "stun": ["stun"],
        "freeze": ["freeze", "frozen"],
        "sleep": ["sleep"],
        "silence": ["silence"],
        "blind": ["blind"],
        "curse": ["curse"],
        "stone": ["stone curse", "petrif"],

    }

    matched_variants = []

    for key, variants in effect_registry.items():
        for word in variants:
            if re.search(rf"\b{re.escape(word)}\b", q):
                matched_variants.append(key)
                break


    return sorted(set(matched_variants))


def find_monsters_by_race_db(race, sort_by_exp=False):
    conn = get_db()
    cur = conn.cursor()

    if sort_by_exp:
        order_clause = "ORDER BY base_exp DESC"
    else:
        order_clause = "ORDER BY level DESC"

    query = f"""
        SELECT DISTINCT name, level, base_exp, job_exp
        FROM monsters
        WHERE trim(lower(race)) = trim(lower(?))
        AND base_exp > 0
        {order_clause}
        LIMIT 50
    """

    cur.execute(query, (race,))
    rows = cur.fetchall()
    conn.close()
    return rows


def find_monsters_by_element_db(element, sort_by_exp=False):
    conn = get_db()
    cur = conn.cursor()

    if sort_by_exp:
        order_clause = "ORDER BY base_exp DESC"
    else:
        order_clause = "ORDER BY level DESC"

    query = f"""
        SELECT DISTINCT name, level, base_exp, job_exp, element, element_level
        FROM monsters
        WHERE lower(element) LIKE lower(?) || '%'
        AND base_exp > 0
        {order_clause}
        LIMIT 50
    """

    cur.execute(query, (element,))
    rows = cur.fetchall()
    conn.close()
    return rows


def find_monsters_by_size_db(size, sort_by_exp=False):
    conn = get_db()
    cur = conn.cursor()

    if sort_by_exp:
        order_clause = "ORDER BY base_exp DESC"
    else:
        order_clause = "ORDER BY level DESC"

    query = f"""
        SELECT DISTINCT name, level, base_exp, job_exp, size
        FROM monsters
        WHERE trim(lower(size)) = trim(lower(?))
        AND base_exp > 0
        {order_clause}
        LIMIT 50
    """

    cur.execute(query, (size,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_top_monsters_by_exp(limit=20):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, level, base_exp, job_exp, race, element
        FROM monsters
        ORDER BY base_exp DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


def extract_monster_filters(question: str):
    q = question.lower()

    races = [
        "formless", "undead", "brute", "plant",
        "insect", "fish", "demon",
        "demihuman", "angel", "dragon", "demi-human", "demi human"
    ]

    elements = [
        "neutral", "water", "earth", "fire",
        "wind", "poison", "holy", "shadow",
        "ghost", "undead", "dark"
    ]

    sizes = ["small", "medium", "large"]

    filters = {
        "race": None,
        "element": None,
        "size": None
    }

    for race in races:
        if re.search(rf"\b{race}\b", q):
            filters["race"] = race


    for element in elements:
        if re.search(rf"\b{element}\b", q):
            filters["element"] = element


    for size in sizes:
        if re.search(rf"\b{size}\b", q):
            filters["size"] = size.capitalize()

    return filters


def find_monsters_with_filters(filters, sort_by_exp=False):
    conn = get_db()
    cur = conn.cursor()

    conditions = []
    params = []

    if filters["race"]:
        conditions.append("trim(lower(race)) = trim(lower(?))")
        params.append(filters["race"])

    if filters["element"]:
        conditions.append("lower(element) LIKE lower(?) || '%'")
        params.append(filters["element"])

    if filters["size"]:
        conditions.append("trim(lower(size)) = trim(lower(?))")
        params.append(filters["size"])

    conditions.append("base_exp > 0")

    where_clause = " AND ".join(conditions)

    if sort_by_exp:
        order_clause = "ORDER BY base_exp DESC"
    else:
        order_clause = "ORDER BY level DESC"

    query = f"""
        SELECT DISTINCT name, level, base_exp, job_exp, race, element, size
        FROM monsters
        WHERE {where_clause}
        {order_clause}
        LIMIT 50
    """

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def find_item_from_question(question):
    items = load_item_cache()

    q = question.lower()

    # Detect slot pattern like [3]
    slot_match = re.search(r"\[(\d+)\]", q)
    slot_requested = int(slot_match.group(1)) if slot_match else None

    matches = []

    for name, aegis, slots in items:
        if name and re.search(rf"\b{re.escape(name.lower())}\b", q):
            matches.append((name, aegis, slots))

    if not matches:
        return None

    # Sort longest match first (avoid partial collisions)
    matches.sort(key=lambda x: len(x[0]), reverse=True)

    # If user explicitly requested slot
    if slot_requested is not None:
        for name, aegis, slots in matches:
            if slots == slot_requested:
                return {
                    "name": name,
                    "aegis": aegis,
                    "slots": slots
                }

        # If requested slot not found
        return None

    # 🔥 IMPORTANT CHANGE:
    # If NO slot specified, return item WITHOUT forcing a slot
    name, aegis, _ = matches[0]

    return {
        "name": name,
        "aegis": aegis,
        "slots": None   # ← THIS IS THE FIX
    }


def find_monster_from_question(question: str):

    q = question.lower().strip()
    monsters = load_monster_cache()

    matches = []

    for name in monsters:
        if name and re.search(rf"\b{re.escape(name.lower().strip())}\b", q):
            matches.append(name)

    if not matches:
        return None

    matches.sort(key=len, reverse=True)
    return matches[0]


def find_item_sources_db(item):
    conn = get_db()
    cur = conn.cursor()

    # If specific slot requested
    if item.get("slots") is not None:
        cur.execute("""
            SELECT m.name, m.level, d.rate, i.slots
            FROM drops d
            JOIN monsters m ON d.monster_id = m.id
            JOIN items i ON d.item_name = i.aegis_name
            WHERE trim(lower(i.name)) = trim(lower(?))
            AND i.slots = ?
            AND m.base_exp > 0
            ORDER BY d.rate DESC
        """, (item["name"], item["slots"]))
    else:
        # No slot specified → return all slot variants
        cur.execute("""
            SELECT m.name, m.level, d.rate, i.slots
            FROM drops d
            JOIN monsters m ON d.monster_id = m.id
            JOIN items i ON d.item_name = i.aegis_name
            WHERE trim(lower(i.name)) = trim(lower(?))
            AND m.base_exp > 0
            ORDER BY i.slots DESC, d.rate DESC
        """, (item["name"],))

    rows = cur.fetchall()
    conn.close()

    return rows


def find_best_monster_for_item(item_name):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            m.name,
            m.level,
            m.base_exp,
            d.rate
        FROM drops d
        JOIN monsters m ON d.monster_id = m.id
        JOIN items i ON d.item_name = i.aegis_name
        WHERE trim(lower(i.name)) = trim(lower(?))
        AND m.base_exp > 0
        ORDER BY d.rate DESC
        LIMIT 5
    """, (item_name,))

    results = cur.fetchall()
    conn.close()
    return results


def find_best_map_for_item(item_name):
    conn = get_db()
    cur = conn.cursor()

    # Step 1: Get top 5 maps by total score
    cur.execute("""
        SELECT 
            s.map_name,
            SUM(d.rate * s.amount) AS total_score
        FROM drops d
        JOIN monsters m ON d.monster_id = m.id
        JOIN items i ON d.item_name = i.aegis_name
        JOIN monster_spawn s ON s.monster_id = m.id
        WHERE trim(lower(i.name)) = trim(lower(?))
        AND m.base_exp > 0
        GROUP BY s.map_name
        ORDER BY total_score DESC
        LIMIT 5
    """, (item_name,))

    top_maps = cur.fetchall()

    results = []

    # Step 2: For each map, get contributing monsters
    for map_name, total_score in top_maps:

        cur.execute("""
            SELECT 
                m.name,
                m.level,
                d.rate,
                s.amount,
                (d.rate * s.amount) AS contribution
            FROM drops d
            JOIN monsters m ON d.monster_id = m.id
            JOIN items i ON d.item_name = i.aegis_name
            JOIN monster_spawn s ON s.monster_id = m.id
            WHERE trim(lower(i.name)) = trim(lower(?))
            AND s.map_name = ?
            AND m.base_exp > 0
            ORDER BY contribution DESC
        """, (item_name, map_name))

        monsters = cur.fetchall()

        results.append((map_name, total_score, monsters))

    conn.close()
    return results

def find_best_map_by_race(race_name):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            s.map_name,
            SUM(s.amount) AS total_spawn
        FROM monster_spawn s
        JOIN monsters m ON s.monster_id = m.id
        WHERE trim(lower(m.race)) = trim(lower(?))
        AND m.base_exp > 0
        GROUP BY s.map_name
        ORDER BY total_spawn DESC
        LIMIT 5
    """, (race_name,))

    top_maps = cur.fetchall()

    results = []

    for map_name, total_spawn in top_maps:

        cur.execute("""
            SELECT 
                m.name,
                m.level,
                s.amount
            FROM monster_spawn s
            JOIN monsters m ON s.monster_id = m.id
            WHERE s.map_name = ?
            AND trim(lower(m.race)) = trim(lower(?))
            AND m.base_exp > 0
            ORDER BY s.amount DESC
        """, (map_name, race_name))

        monsters = cur.fetchall()

        results.append((map_name, total_spawn, monsters))

    conn.close()
    return results


def find_best_map_by_element(element_name):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            s.map_name,
            SUM(s.amount) AS total_spawn
        FROM monster_spawn s
        JOIN monsters m ON s.monster_id = m.id
        WHERE lower(m.element) LIKE lower(?) || '%'
        AND m.base_exp > 0
        GROUP BY s.map_name
        ORDER BY total_spawn DESC
        LIMIT 5
    """, (element_name,))

    top_maps = cur.fetchall()

    results = []

    for map_name, total_spawn in top_maps:

        cur.execute("""
            SELECT 
                m.name,
                m.level,
                s.amount
            FROM monster_spawn s
            JOIN monsters m ON s.monster_id = m.id
            WHERE s.map_name = ?
            AND lower(m.element) LIKE lower(?) || '%'
            AND m.base_exp > 0
            ORDER BY s.amount DESC
        """, (map_name, element_name))

        monsters = cur.fetchall()

        results.append((map_name, total_spawn, monsters))

    conn.close()
    return results


def find_best_map_by_filters(filters):
    conn = get_db()
    cur = conn.cursor()

    conditions = []
    params = []

    if filters["race"]:
        conditions.append("trim(lower(m.race)) = trim(lower(?))")
        params.append(filters["race"])

    if filters["element"]:
        conditions.append("lower(m.element) LIKE lower(?) || '%'")
        params.append(filters["element"])

    if filters["size"]:
        conditions.append("trim(lower(m.size)) = trim(lower(?))")
        params.append(filters["size"])

    conditions.append("m.base_exp > 0")

    where_clause = " AND ".join(conditions)

    # Top 5 maps
    query = f"""
        SELECT 
            s.map_name,
            SUM(s.amount) AS total_spawn
        FROM monster_spawn s
        JOIN monsters m ON s.monster_id = m.id
        WHERE {where_clause}
        GROUP BY s.map_name
        ORDER BY total_spawn DESC
        LIMIT 5
    """

    cur.execute(query, params)
    top_maps = cur.fetchall()

    results = []

    for map_name, total_spawn in top_maps:

        query_detail = f"""
            SELECT 
                m.name,
                m.level,
                s.amount
            FROM monster_spawn s
            JOIN monsters m ON s.monster_id = m.id
            WHERE s.map_name = ?
            AND {where_clause}
            ORDER BY s.amount DESC
        """

        cur.execute(query_detail, [map_name] + params)
        monsters = cur.fetchall()

        results.append((map_name, total_spawn, monsters))

    conn.close()
    return results


def find_drops_from_monster_db(monster_name):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT i.name, d.rate
        FROM drops d
        JOIN monsters m ON d.monster_id = m.id
        JOIN items i ON d.item_name = i.aegis_name
        WHERE trim(lower(m.name)) = trim(lower(?))
        AND m.base_exp > 0
        AND EXISTS (
            SELECT 1
            FROM monster_spawn s
            WHERE s.monster_id = m.id
        )
        ORDER BY d.rate DESC
        LIMIT 50
    """, (monster_name,))


    rows = cur.fetchall()
    conn.close()

    return rows


def find_monster_spawn_maps(monster_name):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.map_name, s.amount
        FROM monster_spawn s
        JOIN monsters m ON s.monster_id = m.id
        WHERE trim(lower(m.name)) = trim(lower(?))
        ORDER BY s.amount DESC
    """, (monster_name,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_obtainable_slots(item_name):
    """Returns set of slot counts for variants obtainable via drops or NPC shops."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT i.slots
        FROM items i
        WHERE trim(lower(i.name)) = trim(lower(?))
        AND (
            EXISTS (
                SELECT 1 FROM drops d
                JOIN monsters m ON d.monster_id = m.id
                JOIN items i2 ON d.item_name = i2.aegis_name
                WHERE trim(lower(i2.name)) = trim(lower(?))
                AND i2.slots = i.slots
                AND m.base_exp > 0
            )
            OR EXISTS (
                SELECT 1 FROM npc_shop_items si
                JOIN items i2 ON si.item_id = i2.id
                WHERE trim(lower(i2.name)) = trim(lower(?))
                AND i2.slots = i.slots
            )
        )
    """, (item_name, item_name, item_name))

    rows = cur.fetchall()
    conn.close()
    return {row[0] for row in rows}


def get_item_details_db(item_name):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            name,
            type,
            subtype,
            item_class,
            buy,
            sell,
            weight,
            atk,
            def,
            weapon_level,
            equip_level_min,
            refineable,
            slots,
            equip_locations,
            jobs,
            description
        FROM items
        WHERE trim(lower(name)) = trim(lower(?))
        ORDER BY slots DESC
    """, (item_name,))

    rows = cur.fetchall()
    conn.close()

    return rows


def find_npc_sellers(item_name):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            s.npc_name,
            s.map_name,
            s.x,
            s.y,
            i.id,
            i.buy,
            si.price_override
        FROM npc_shop_items si
        JOIN npc_shops s ON si.shop_id = s.id
        JOIN items i ON si.item_id = i.id
        WHERE trim(lower(i.name)) = trim(lower(?))
    """, (item_name,))

    rows = cur.fetchall()
    conn.close()

    return rows


def list_equipment_sorted(question, sort_field):
    conn = get_db()
    cur = conn.cursor()

    sort_map = {
        "attack": "atk",
        "atk": "atk",
        "defense": "def",
        "def": "def",
        "weight": "weight"
    }

    column = sort_map.get(sort_field.lower(), "def")

    category_type, category_value = detect_equipment_category(question)
    effect_keywords = detect_effect_keywords(question)

    # Remove only the actual sort field from effect keywords (not all sort-related words)
    _sort_effect_aliases = {
        "attack":       {"atk", "attack"},
        "atk":          {"atk", "attack"},
        "defense":      {"def", "defense"},
        "def":          {"def", "defense"},
        "weight":       {"weight"},
        "aspd":         {"aspd", "attack speed"},
        "attack speed": {"aspd", "attack speed"},
    }
    if sort_field:
        _to_remove = _sort_effect_aliases.get(sort_field.lower(), {sort_field.lower()})
        effect_keywords = [kw for kw in effect_keywords if kw not in _to_remove]

    if not category_type:
        conn.close()
        return [], []

    # -------------------------
    # WEAPON EXACT (1hSword)
    # -------------------------
    if category_type == "weapon_exact":
        condition = "lower(subtype) = lower(?)"
        params = (category_value,)

    # -------------------------
    # WEAPON FAMILY (Sword → 1hSword + 2hSword)
    # -------------------------
    elif category_type == "weapon_family":
        condition = "lower(subtype) LIKE lower(?)"
        params = (f"%{category_value}%",)

    # -------------------------
    # ARMOR SLOT (Left_Hand, Shoes, Garment)
    # -------------------------
    elif category_type == "armor_slot":
        condition = "lower(type) = 'armor' AND lower(equip_locations) LIKE lower(?)"
        params = (f"%{category_value}%",)

    elif category_type == "armor_slot_family":
        condition = "lower(type) = 'armor' AND lower(equip_locations) LIKE lower(?)"
        params = (f"%{category_value.lower()}%",)

    elif category_type == "type_exact":
        condition = "lower(type) = lower(?)"
        params = (category_value,)

    else:
        conn.close()
        return [], []

    # Detect if this is a headgear-related query
    is_headgear = (
        category_type in ["armor_slot", "armor_slot_family"]
        and (
            "head" in question.lower()
            or "headgear" in question.lower()
            or "head gear" in question.lower()
        )
    )

    # SQLite expression that returns description text before any combo section.
    # Strips at \n_\n (underscore-separator combo format) first,
    # then at [ (bracket combo format), giving only the card's own effects.
    _PRE_COMBO = (
        "CASE "
        "WHEN instr(description, char(10) || '_' || char(10)) > 0 "
        "THEN substr(description, 1, instr(description, char(10) || '_' || char(10)) - 1) "
        "WHEN instr(description, '[') > 0 "
        "THEN substr(description, 1, instr(description, '[') - 1) "
        "ELSE description END"
    )

    # Maps effect keys → all terms that might appear in item descriptions
    _desc_search_terms = {
        "aspd":    ["aspd", "attack speed"],
        "matk":    ["matk", "magic attack"],
        "mdef":    ["mdef", "magic defense"],
        "crit":    ["crit", "critical"],
        "flee":    ["flee", "dodge"],
        "freeze":  ["freeze", "frozen"],
        "stone":   ["stone curse", "petrif"],
    }

    effect_filter = ""
    effect_params = ()

    if effect_keywords:
        like_clauses = []
        params_extra = []

        for keyword in effect_keywords:

            if keyword in ["agi", "str", "vit", "int", "dex", "luk"]:
                _d = f"lower({_PRE_COMBO})"
                like_clauses.append(
                    f"({_d} LIKE lower(?) OR {_d} LIKE lower(?) OR {_d} LIKE lower(?))"
                )
                params_extra.extend([
                    f"%{keyword}+%",
                    f"%{keyword} +%",
                    f"%increase {keyword}%",
                ])


            else:
                terms = _desc_search_terms.get(keyword, [keyword])
                _d = f"lower({_PRE_COMBO})"
                or_parts = " OR ".join(f"{_d} LIKE lower(?)" for _ in terms)
                like_clauses.append(f"({or_parts})")
                params_extra.extend(f"%{t}%" for t in terms)


        if like_clauses:
            effect_filter = ""
            for clause in like_clauses:
                effect_filter += f" AND ({clause}) "
            effect_params = tuple(params_extra)
        else:
            effect_filter = ""
            effect_params = ()


    obtainable_filter = """
        AND (
            EXISTS (
                SELECT 1 FROM drops d
                JOIN monsters m ON d.monster_id = m.id
                WHERE d.item_name = items.aegis_name
                AND m.base_exp > 0
            )
            OR EXISTS (
                SELECT 1 FROM npc_shop_items si
                WHERE si.item_id = items.id
            )
        )
    """

    if is_headgear:

        query = f"""
            SELECT
                name,
                MAX(atk) AS max_atk,
                MAX(def) AS max_def,
                MAX(weight) AS max_weight,
                MAX(description) AS description,
                MIN(
                    (
                        (CASE WHEN equip_locations LIKE '%Head_Top%' THEN 1 ELSE 0 END) +
                        (CASE WHEN equip_locations LIKE '%Head_Mid%' THEN 1 ELSE 0 END) +
                        (CASE WHEN equip_locations LIKE '%Head_Low%' THEN 1 ELSE 0 END)
                    )
                ) AS slot_count
            FROM items
            WHERE {condition}
            AND type IS NOT NULL
            AND name NOT LIKE '%+%'
            {obtainable_filter}
            {effect_filter}
            GROUP BY name
            ORDER BY {column} DESC, slot_count ASC
            LIMIT 50
        """

    else:

        query = f"""
            SELECT name, MAX(atk), MAX(def), MAX(weight), MAX(description)
            FROM items
            WHERE {condition}
            AND type IS NOT NULL
            AND name NOT LIKE '%+%'
            {obtainable_filter}
            {effect_filter}
            GROUP BY name
            ORDER BY {column} DESC
            LIMIT 50
        """

    cur.execute(query, params + effect_params)
    rows = cur.fetchall()
    conn.close()

    return rows, effect_keywords


def detect_equipment_category(question):

    q = question.lower()

    # 1 Check weapon subtypes dynamically
    subtypes = load_subtypes()

    normalized_q = q

    # Detect hand qualifier
    hand_prefix = None

    if re.search(r"\bone\s*hand\b", q) or re.search(r"\b1h\b", q):
        hand_prefix = "1h"
    elif re.search(r"\btwo\s*hand\b", q) or re.search(r"\b2h\b", q):
        hand_prefix = "2h"

    # Extract possible base weapon keyword from user input
    weapon_bases = set()

    for subtype in subtypes:
        subtype_lower = subtype.lower()
        base = subtype_lower.replace("1h", "").replace("2h", "")
        weapon_bases.add(base)

    matched_base = None

    for base in sorted(weapon_bases, key=len, reverse=True):
        if base and re.search(rf"\b{re.escape(base)}s?\b", normalized_q):
            matched_base = base
            break

    if matched_base:

        # If specific hand requested
        if hand_prefix:
            expected_subtype = f"{hand_prefix}{matched_base}"

            for subtype in subtypes:
                if subtype.lower() == expected_subtype:
                    return ("weapon_exact", subtype)

        # Otherwise return family
        return ("weapon_family", matched_base)
    

    # 2 Check headgear first (special handling)

    if re.search(r"\bheadgear\b", q) or re.search(r"\bhead gear\b", q) or re.search(r"\bhead\b", q):

        if re.search(r"\bupper\b", q) or re.search(r"\btop\b", q):
            return ("armor_slot", "Head_Top")

        elif re.search(r"\bmiddle\b", q) or re.search(r"\bmid\b", q):
            return ("armor_slot", "Head_Mid")

        elif re.search(r"\blower\b", q) or re.search(r"\blow\b", q):
            return ("armor_slot", "Head_Low")

        else:
            # Generic headgear → match all head slots
            return ("armor_slot_family", "Head_")


    # 3a Explicit user-facing aliases (DB names don't match natural language)
    location_aliases = {
        "shield":      "Left_Hand",
        "accessory":   "Both_Accessory",
        "accessories": "Both_Accessory",
    }
    for alias, loc in location_aliases.items():
        if re.search(rf"\b{re.escape(alias)}\b", q):
            return ("armor_slot", loc)

    # 3b Check armor slots dynamically
    locations = load_armor_locations()


    for loc in locations:
        # Normalize location naming
        normalized = loc.lower().replace("_", " ")
        if re.search(rf"\b{re.escape(normalized)}\b", q):
            return ("armor_slot", loc)

        
    # 4 Check cards
    if re.search(r"\bcards?\b", q):
        return ("type_exact", "Card")

    return (None, None)


# ----------------------
# INTENT DETECTION
# ----------------------


def detect_intent(question: str):
    item_match = find_item_from_question(question)
    monster_match = find_monster_from_question(question)

    q = question.lower()

    race_keywords = [
        "insect", "demon", "undead",
        "demihuman", "demi-human", "demi human",
        "brute", "plant",
        "angel", "dragon", "formless", "fish"
    ]

    element_keywords = [
        "fire", "water", "wind", "earth",
        "holy", "shadow", "ghost", "poison",
        "neutral", "undead", "dark"
    ]

    size_keywords = ["small", "medium", "large"]

    best_location_pattern = (
        r"\b(best map|best place|best spot|best location|best area|"
        r"where to farm|where to hunt|where to grind|where can i farm|"
        r"where should i farm|good map|good place)\b"
    )

    # PRIORITY 1 — Best Map By Combined Filters
    if (
        re.search(best_location_pattern, q)
        and (
            any(
                re.search(rf"\b{re.escape(word)}\b", q)
                for word in size_keywords + race_keywords + element_keywords
            )
            or monster_match
        )
        and not item_match
    ):
        return "best_filtered_map"

    # PRIORITY 4 — Best Map By Item
    if re.search(best_location_pattern, q) and item_match:
        return "best_map"

    # PRIORITY 5 — Best Monster By Item
    if (
        item_match
        and re.search(r"\bbest\b", q)
        and any(
            re.search(rf"\b{word}\b", q)
            for word in ["farm", "farming", "drop", "drops", "hunt", "monster", "kill"]
        )
    ):
        return "best_farm"
    
    # PRIORITY — Comparison queries
    if re.search(r"\b(compare|vs|versus)\b", q):
        return "compare"

    # PRIORITY 5.5 — Monster List By Filters
    monster_list_triggers = ["list", "show", "display", "find"]
    if (
        any(re.search(rf"\b{re.escape(t)}\b", q) for t in monster_list_triggers)
        and re.search(r"\bmonsters?\b", q)
        and any(
            re.search(rf"\b{re.escape(word)}\b", q)
            for word in race_keywords + element_keywords + size_keywords
        )
    ):
        return "monster_list"

    # PRIORITY 6 — Equipment Listing With Sort
    equipment_trigger_words = [
        "list", "show", "display", "what", "which", "find", "give me"
    ]
    equipment_type_words = [
        "card",
        "sword", "dagger", "axe", "spear", "staff",
        "shield", "armor", "headgear", "head gear",
        "garment", "shoes", "accessory",
        "mace", "bow", "katar", "whip", "instrument",
        "rod", "book", "knuckle", "fist",
    ]
    if (
        any(re.search(rf"\b{re.escape(trigger)}\b", q) for trigger in equipment_trigger_words)
        and any(re.search(rf"\b{re.escape(word)}s?\b", q) for word in equipment_type_words)
    ):
        return "equipment_list"


    # PRIORITY 7 — EXP listing (Monster EXP only)
    _exp_item_words = [
        "card", "weapon", "armor", "headgear",
        "shield", "sword", "dagger", "axe", "staff"
    ]
    if (
        (re.search(r"\bexp\b", q) or re.search(r"\bexperience\b", q))
        and any(
            re.search(rf"\b{word}\b", q)
            for word in ["highest", "top", "most", "best", "fastest", "fast", "good", "high"]
        )
        and not any(re.search(rf"\b{word}\b", q) for word in _exp_item_words)
    ):
        return "exp"

    if (
        re.search(r"\bwhere (to|can i|should i) (level|grind|exp farm)\b", q)
        and not any(re.search(rf"\b{word}\b", q) for word in _exp_item_words)
    ):
        return "exp"

    
    # PRIORITY 8 — Item Detail
    if any(
        re.search(rf"\b{re.escape(keyword)}\b", q)
        for keyword in [
            "details of",
            "item info",
            "describe",
            "stats of",
            "tell me about",
            "info about",
            "info on",
            "what is",
            "about",
        ]
    ) and item_match:

        return "item_detail"
    
    # PRIORITY 9 — Where to Buy
    if any(
        re.search(rf"\b{re.escape(phrase)}\b", q)
        for phrase in [
            "where can i buy", "where to buy",
            "how much is", "how much does", "price of",
            "cost of", "can i buy", "npc sell", "npc price",
        ]
    ) and item_match:
        return "buy"

    # PRIORITY 10 — Item farming
    if item_match:
        return "farm"

    # Monster spawn location
    if any(
        re.search(rf"\b{re.escape(phrase)}\b", q)
        for phrase in [
            "where is", "where can i find", "location of",
            "found in", "where do i find", "spawn location",
            "where does", "where do", "spawns in",
        ]
    ):
        if monster_match:
            return "monster_location"

    # Monster detail
    if (
        any(
            re.search(rf"\b{re.escape(kw)}\b", q)
            for kw in ["what is", "tell me about", "info about", "describe", "stats of", "info on"]
        )
        and monster_match
        and not item_match
    ):
        return "monster_detail"

    return "general"


# ----------------------
# LLM DECISION LAYER
# ----------------------

def should_use_llm(question: str, intent: str) -> bool:
    q = question.lower()

    # Always use LLM for compare — the deterministic output is raw data that needs analysis
    if intent == "compare":
        return True

    # Never use LLM for pure data responses
    if intent in [
        "farm",
        "best_map",
        "best_farm",
        "buy",
        "exp",
        "equipment_list",
        "best_filtered_map",
        "monster_list",
        "monster_location",
        "monster_detail",
    ]:
        return False

    # Use LLM for reasoning / comparison / advice
    if any(re.search(rf"\b{word}\b", q) for word in [
        "compare",
        "vs",
        "versus",
        "better",
        "best for",
        "recommend",
        "suggest",
        "why",
        "should i",
        "worth it",
        "explain"
    ]):
        return True

    return False


def enhance_with_llm(question: str, deterministic_answer: str) -> str:

    if not client:
        print("LLM SKIPPED: No OPENAI_API_KEY configured")
        return deterministic_answer + "\n\n(AI comparison unavailable — API key not configured)"

    prompt = f"""
You are assisting a Ragnarok Online farming AI.

User Question:
{question}

Deterministic Engine Output:
{deterministic_answer}

STRICT RULES:
- Do NOT invent stats.
- Do NOT modify any numeric values.
- Do NOT shorten or summarize job lists.
- Do NOT remove any fields.
- You must preserve all data exactly as written.
- You may reorganize formatting for clarity.
- You may add strategic comparison or explanation AFTER the full data is preserved.

If comparing items:
1. First display the full original data for both items exactly as provided.
2. Then provide analysis below it.
3. Never replace detailed lists with vague summaries.

If no reasoning is needed, return the deterministic output unchanged.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Ragnarok Online assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        llm_reply = response.choices[0].message.content.strip()

        return llm_reply

    except Exception as e:
        print("LLM ERROR:", e)
        return deterministic_answer


# ----------------------
# MAIN ROUTER
# ----------------------
def ask_ai(question: str):

    intent = detect_intent(question)
    print("INTENT:", intent)

    # ----------------------
    # BEST MAP BY COMBINED FILTERS
    # ----------------------
    if intent == "best_filtered_map":

        filters = extract_monster_filters(question)

        # Normalize Dark/Shadow
        if filters["element"] and filters["element"].lower() == "shadow":
            filters["element"] = "dark"

        if not any(filters.values()):
            return "No valid filters detected."

        results = find_best_map_by_filters(filters)

        if not results:
            return "No maps found for given filters."

        label_parts = []
        if filters["size"]:
            label_parts.append(filters["size"])
        if filters["element"]:
            label_parts.append(filters["element"])
        if filters["race"]:
            label_parts.append(filters["race"])

        label = " ".join(label_parts)

        output = [f"Top 5 farming maps for {label} monsters:\n"]

        for idx, (map_name, total_spawn, monsters) in enumerate(results, start=1):

            output.append(
                f"{idx}. Map: {map_name}\n"
                f"   Total Spawn: {total_spawn}"
            )

            for m in monsters:
                name, level, amount = m
                output.append(
                    f"      - {name} (Lv{level}) - Spawn: {amount}"
                )

            output.append("")

        return "\n".join(output)

    # ----------------------
    # BEST MAP FOR ITEM
    # ----------------------
    if intent == "best_map":

        item = find_item_from_question(question)

        if not item:
            return "Item not found."

        results = find_best_map_for_item(item["name"])

        if not results:
            return "No farmable map found for this item."

        output = [f"Top 5 farming maps for {item['name']}:\n"]

        for idx, (map_name, total_score, monsters) in enumerate(results, start=1):

            output.append(
                f"{idx}. Map: {map_name}\n"
                f"   Total Farm Score: {int(total_score)}"
            )

            for m in monsters:
                name, level, rate, amount, contribution = m

                output.append(
                    f"      - {name} (Lv{level}) "
                    f"- Drop: {rate / 100:g}% "
                    f"- Spawn: {amount} "
                    f"- Contribution: {int(contribution)}"
                )

            output.append("")

        return "\n".join(output)

    # ----------------------
    # BEST MONSTER FOR ITEM
    # ----------------------
    if intent == "best_farm":

        item = find_item_from_question(question)

        if not item:
            return "Item not found."

        results = find_best_monster_for_item(item["name"])

        if not results:
            return "No farmable monster found for this item."

        output = [f"Top 5 monsters to farm {item['name']}:\n"]

        for idx, row in enumerate(results, start=1):
            name, level, base_exp, rate = row

            output.append(
                f"{idx}. {name} (Lv{level})\n"
                f"   Drop Rate: {rate / 100:g}%\n"
                f"   Base EXP: {base_exp}\n"
            )

        return "\n".join(output)


    # ----------------------
    # EXP LISTING
    # ----------------------
    if intent == "exp":

        filters = extract_monster_filters(question)

        if any(filters.values()):
            rows = find_monsters_with_filters(filters, sort_by_exp=True)

            if not rows:
                return "No monsters found with those filters."

            label_parts = [v for v in [filters["size"], filters["element"], filters["race"]] if v]
            label = " ".join(label_parts)

            output = [f"Top monsters ({label}) by EXP:\n"]
            for r in rows:
                name, level, base_exp, job_exp, race, element, size = r
                output.append(
                    f"{name} Lv{level} BaseEXP:{base_exp} JobEXP:{job_exp} "
                    f"Race:{race} Element:{element} Size:{size}"
                )
            return "\n".join(output)

        result = get_top_monsters_by_exp(20)

        return "\n".join([
            f"{r[0]} Lv{r[1]} "
            f"BaseEXP:{r[2]} JobEXP:{r[3]} "
            f"Race:{r[4]} Element:{r[5]}"
            for r in result
        ])

    # ----------------------
    # MONSTER DETAIL
    # ----------------------
    if intent == "monster_detail":

        monster_name = find_monster_from_question(question)

        if not monster_name:
            return "Monster not found."

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT name, level, race, element, element_level, base_exp, job_exp, hp, size
            FROM monsters
            WHERE trim(lower(name)) = trim(lower(?))
        """, (monster_name,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return f"No data found for {monster_name}."

        name, level, race, element, element_level, base_exp, job_exp, hp, size = row
        return (
            f"{name}\n"
            f"  Level: {level} | Size: {size}\n"
            f"  HP: {hp}\n"
            f"  Race: {race} | Element: {element} Lv{element_level}\n"
            f"  BaseEXP: {base_exp} | JobEXP: {job_exp}"
        )

    # ----------------------
    # MONSTER SPAWN LOCATION
    # ----------------------
    if intent == "monster_location":

        monster_name = find_monster_from_question(question)

        if not monster_name:
            return "Monster not found."

        maps = find_monster_spawn_maps(monster_name)

        if not maps:
            return f"{monster_name} has no known spawn locations in the database."

        output = [f"{monster_name} spawns in:\n"]
        for map_name, amount in maps:
            output.append(f"  - {map_name} (Spawn: {amount})")

        return "\n".join(output)

    # ----------------------
    # MONSTER LIST BY FILTERS
    # ----------------------
    if intent == "monster_list":

        filters = extract_monster_filters(question)
        q_lower = question.lower()
        sort_by_exp = any(
            re.search(rf"\b{word}\b", q_lower)
            for word in ["exp", "experience"]
        )

        rows = find_monsters_with_filters(filters, sort_by_exp=sort_by_exp)

        if not rows:
            return "No monsters found with those filters."

        label_parts = [v for v in [filters["size"], filters["element"], filters["race"]] if v]
        label = " ".join(label_parts) if label_parts else "all"
        sort_label = "EXP" if sort_by_exp else "Level"

        output = [f"Monsters ({label}), sorted by {sort_label}:\n"]

        for r in rows:
            name, level, base_exp, job_exp, race, element, size = r
            output.append(
                f"{name} Lv{level} | BaseEXP:{base_exp} | JobEXP:{job_exp} | "
                f"Race:{race} | Element:{element} | Size:{size}"
            )

        return "\n".join(output)

    # ----------------------
    # MONSTER → ITEM DROPS
    # ----------------------
    if intent == "general":

        q = question.lower()

        _drop_phrases = [
            "what items", "what does", "drops from",
            "what drop", "what drops", "loot from",
            "what can i get from", "what do i get from",
            "items from", "drops of",
        ]

        monster_name = find_monster_from_question(question)

        if any(re.search(rf"\b{re.escape(phrase)}\b", q) for phrase in _drop_phrases) or (
            monster_name and re.search(r"\bdrops?\b", q)
        ):

            if not monster_name:
                return "Monster not found."

            drops = find_drops_from_monster_db(monster_name)

            if not drops:
                return f"No items found dropping from {monster_name}."

            return "\n".join([
                f"{r[0]} - {r[1] / 100:g}%"
                for r in drops
            ])

        return "I didn't understand that. Try asking about an item, monster, map, or equipment."

    # ----------------------
    # ITEM DETAILS
    # ----------------------
    if intent == "item_detail":

        item = find_item_from_question(question)

        if not item:
            return "Item not found."

        rows = get_item_details_db(item["name"])

        # Filter to obtainable variants only (dropped or sold by NPC)
        obtainable = get_obtainable_slots(item["name"])
        if obtainable:
            rows = [r for r in rows if r[12] in obtainable]

        if not rows:
            return "No item data found."

        output = []

        for index, row in enumerate(rows):

            (
                name, type_, subtype, item_class, buy, sell, weight,
                atk, def_, weapon_level, equip_level_min,
                refineable, slots, equip_locations,
                jobs, description
            ) = row

            output.append(f"{name} [{slots}]")
            output.append(f"Type: {type_}")

            if type_ and type_.lower() == "weapon" and subtype:
                display_class = subtype
            elif item_class:
                display_class = item_class
            else:
                display_class = subtype

            if display_class:
                output.append(f"Class: {display_class}")

            if atk is not None:
                output.append(f"ATK: {atk}")

            if def_ is not None:
                output.append(f"DEF: {def_}")

            if weapon_level is not None:
                output.append(f"Weapon Level: {weapon_level}")

            if equip_level_min is not None:
                output.append(f"Required Level: {equip_level_min}")

            if weight is not None:
                output.append(f"Weight: {weight / 10:g}")

            if buy is not None:
                output.append(f"Buy: {buy}")

            base_sell = sell

            # If Sell is NULL, compute from Buy
            if base_sell is None and buy is not None:
                base_sell = buy // 2

            if base_sell is not None:
                output.append(f"Sell: {base_sell}")

                # Merchant Overcharge Lv10 (+24%)
                overcharge_sell = int(base_sell * 1.24)
                output.append(f"Sell (Overcharge Lv10): {overcharge_sell}")


            output.append(f"Refineable: {'Yes' if refineable else 'No'}")

            if equip_locations:
                output.append(f"Equip Location: {equip_locations}")

            if jobs:
                output.append(f"Jobs: {jobs}")

            if description:
                raw_description = description.strip()
                desc_lines = raw_description.split("\n")

                clean_desc_lines = []

                for line in desc_lines:
                    line = line.strip()

                    # Remove duplicated stat lines
                    if re.match(r"^(Attack|Weight|Weapon Level|Level Requirement|Jobs|Class)\s*:", line):
                        continue

                    if line:
                        clean_desc_lines.append(line)


                clean_description = "\n".join(clean_desc_lines)

                output.append("Description:")
                output.append(clean_description)

            if index < len(rows) - 1:
                output.append("")
                output.append("----------------------------------------")
                output.append("")

        return "\n".join(output)
    
    # ----------------------
    # WHERE TO BUY ITEM
    # ----------------------
    if intent == "buy":

        item = find_item_from_question(question)

        if not item:
            return "Item not found."

        sellers = find_npc_sellers(item["name"])

        if not sellers:
            return f"{item['name']} is not sold by any NPC."

        output = [f"{item['name']} can be purchased from:\n"]

        for idx, (npc, map_name, x, y, item_id, buy_price, price_override) in enumerate(sellers, start=1):

            final_price = price_override if price_override is not None else buy_price

            output.append(
                f"{idx}. {npc}\n"
                f"   Location: {map_name} ({x}, {y})\n"
                f"   Price: {final_price} zeny\n"
            )

        return "\n".join(output)
    
    # COMPARE ITEMS
    if intent == "compare":

        q = question.lower()
        items = []

        for name, aegis, slots in load_item_cache():
            if name and re.search(rf"\b{re.escape(name.lower())}\b", q):
                items.append(name)

        # Remove duplicates
        items = list(dict.fromkeys(items))

        if len(items) >= 2:
            data = []
            for item_name in items[:2]:
                detail = ask_ai(f"describe {item_name}")
                data.append(detail)

            combined = "\n\n".join(data)
            return combined

        return "Please specify two items to compare."

    
    # ----------------------
    # EQUIPMENT LIST + SORT
    # ----------------------
    if intent == "equipment_list":

        # Detect sort field
        

        sort_field = None
        q_lower = question.lower()
        for word in sort_keywords:
            # Only treat as sort when user explicitly asks for ordering,
            # not when the keyword appears as an effect ("gives aspd")
            if re.search(
                rf"\b(sorted by|order by|by|highest|most)\s+{re.escape(word)}\b",
                q_lower
            ):
                sort_field = word
                break

        if not sort_field:
            sort_field = "def"  # default fallback

        results, effect_keywords = list_equipment_sorted(question, sort_field)

        if not results:
            return "No results found."

        pretty_sort = {
            "atk": "Attack",
            "attack": "Attack",
            "def": "Defense",
            "defense": "Defense",
            "weight": "Weight"
        }.get(sort_field.lower(), sort_field)

        if effect_keywords:
            effect_label = ", ".join(effect_keywords).upper()
            output = [f"Listing items affecting {effect_label} sorted by {pretty_sort}:\n"]
        else:
            output = [f"Listing sorted by {pretty_sort}:\n"]


        for row in results:

            name = row[0]
            atk = row[1]
            defense = row[2]
            weight = row[3]
            description = row[4]
            slot_count = row[5] if len(row) > 5 else None

            display = name

            if sort_field in ["attack", "atk"] and atk is not None:
                display += f" | ATK: {atk}"
            elif sort_field in ["defense", "def"] and defense is not None:
                display += f" | DEF: {defense}"
            elif sort_field == "weight" and weight is not None:
                display += f" | Weight: {weight / 10:g}"

            if slot_count is not None:
                display += f" | SlotCount:{slot_count}"

            if description:
                # Strip combo section (underscore separator or bracket format)
                has_combo = False
                if "\n_\n" in description:
                    pre_combo = description[:description.index("\n_\n")]
                    has_combo = True
                elif "[" in description:
                    pre_combo = description[:description.index("[")]
                    has_combo = True
                else:
                    pre_combo = description

                _meta_re = re.compile(
                    r"^(Class|Compound on|Weight|Level Requirement|Jobs|"
                    r"Attack|Defense|Position|Refinable|Weapon Level)\s*:",
                    re.IGNORECASE
                )
                effect_lines = [
                    line.strip() for line in pre_combo.split("\n")
                    if line.strip()
                    and not re.match(r"^[_\-=]+$", line.strip())
                    and not _meta_re.match(line.strip())
                ]

                if effect_lines:
                    display += "\n   " + "\n   ".join(effect_lines)
                if has_combo:
                    display += "\n   [Has combo bonus]"

            output.append(display)

        return "\n".join(output)


    # ----------------------
    # ITEM → MONSTER DROPS
    # ----------------------
    if intent == "farm":

        item = find_item_from_question(question)

        if not item:
            return "No results found."

        results = find_item_sources_db(item)

        if not results:
            return "No monster drops found."

        output = []

        for monster, level, rate, slots in results:
            slot_label = f"{item['name']}[{slots}]" if slots is not None else item["name"]
            output.append(
                f"{monster} (Level {level}) drops {slot_label} with rate {rate / 100:g}%"
            )

        return "\n".join(output)
    

# ----------------------
# HYBRID ENTRY POINT
# ----------------------

def ask_ai_hybrid(question: str) -> str:

    deterministic_answer = ask_ai(question)
    intent = detect_intent(question)

    if should_use_llm(question, intent):
        return enhance_with_llm(question, deterministic_answer)

    return deterministic_answer
