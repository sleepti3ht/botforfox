from lisskins_client import LisskinsClient, SearchParams
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import time

# -----------------------------
# CONFIGURATION
# -----------------------------
API_KEY = ""          # Your lis-skins API key
GAME = "dota2"

BOT_TOKEN = ""        # Telegram bot token
CHAT_ID = ""          # Your Telegram chat_id

bot = Bot(BOT_TOKEN)

# -----------------------------
# TARGET SEARCH RULES
# -----------------------------
TARGET_RULES = {
    "ITEM NAME": {
        "gem": "GEM NAME",
        "max_price": 30
    },
    "ITEM NAME": {
        "gem": "GEM NAME",
        "max_price": 30

    }
}

POLL_DELAY = 0.6
PER_PAGE = 100
MAX_PAGES = 50

# -----------------------------
# LIS-SKINS CLIENT
# -----------------------------
client = LisskinsClient(API_KEY)

# Prevent duplicate notifications during a single runtime
seen_ids = set()
seen_cursors = set()

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def extract_gem_names(item):
    gems = item.get("gems", [])
    out = []
    for g in gems:
        if isinstance(g, dict) and g.get("name"):
            out.append(g["name"])
        elif isinstance(g, str):
            out.append(g)
    return out

def extract_styles(item):
    styles = item.get("styles", {})
    if isinstance(styles, dict):
        unlocked = []
        for style_name, status in styles.items():
            if str(status).lower() in {"yes", "unlocked", "true", "1"}:
                unlocked.append(style_name)
        return unlocked
    if isinstance(styles, list):
        return [s.get("name") for s in styles if isinstance(s, dict) and s.get("name")]
    return []

def matches_rule(item, rule):
    price = float(item.get("price", 0) or 0)
    if price > float(rule.get("max_price", 0)):
        return False

    if "gem" in rule:
        return rule["gem"] in extract_gem_names(item)

    if "required_style" in rule:
        return rule["required_style"] in extract_styles(item)

    return False

# -----------------------------
# TELEGRAM NOTIFICATION
# -----------------------------
def notify(item):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📋 My Tasks", callback_data="tasks")],
        [InlineKeyboardButton("📝 Create Task", callback_data="create")],
        [InlineKeyboardButton("💰 My Balance", callback_data="balance")],
        [InlineKeyboardButton("✉️ Support", callback_data="support")],
    ])

    text = (
        f"Item Found!\n\n"
        f"Name: {item['name']}\n"
        f"Price: {item['price']}€\n"
        f"ID: {item['id']}"
    )

    bot.send_message(chat_id=CHAT_ID, text=text, reply_markup=keyboard)

# -----------------------------
# INFINITE MONITORING LOOP
# -----------------------------
try:
    while True:
        cursor = None
        page = 0
        seen_cursors.clear()

        while True:
            params = SearchParams(
                game=GAME,
                per_page=PER_PAGE,
                cursor=cursor,
                sort_by="newest",
                price_to=30
            )

            data = client.search_items(params)
            items = data.get("data", [])
            meta = data.get("meta", {})
            next_cursor = meta.get("next_cursor")

            for item in items:
                name = item.get("name")
                rule = TARGET_RULES.get(name)
                if not rule:
                    continue

                if matches_rule(item, rule):
                    item_id = item.get("id")
                    if item_id not in seen_ids:
                        seen_ids.add(item_id)
                        notify(item)

            page += 1
            if page >= MAX_PAGES:
                break

            if not next_cursor or next_cursor == cursor or next_cursor in seen_cursors:
                break

            seen_cursors.add(next_cursor)
            cursor = next_cursor
            time.sleep(POLL_DELAY)

        time.sleep(1)

finally:
    client.close()
