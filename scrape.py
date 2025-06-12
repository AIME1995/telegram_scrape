import json
import os
import re
import sqlite3
import pandas as pd
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import PeerChannel
from telethon.tl.types import ChannelParticipantsSearch
from telethon.errors import FloodWaitError
import time

# === CONFIG ===
api_id = 22052131
api_hash = '***********'
phone = '+3******'
DB_PATH = "messages.db"

# === GROUPES CIBLÉS ===
TARGET_GROUPS = {
    -1001173843767: "Cryptoast",
    -1001405351363: "Cointribune",
    -1002136723929: "Journal Du Coin",
    -1001643878294: "Hasheur | Owen Simonin",
    -1002253495059: "Futures Analysen Signals (Ai)",
    -1001273074420: "CoinAcademy - News",
    -1002057004088: "Foufi : Analyses & actualités",
    -1001621325374: "Julien Roman",
    -1001151783486: "The Cryptomath",
    -1001335840533: "Paul Cryptoformation",
    -1002166051333: "Enter The Crypto Matrix",
    -1002266411318: "ThibautCrypto",
    -1002530741739: "GLOBAL CONNECT",
    1150321216: "[SUPPORT] ThibautCrypto"
}

# === TELEGRAM CLIENT ===
client = TelegramClient('session_name', api_id, api_hash)
client.start(phone)

# === DB INIT ===
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        group_id INTEGER,
        group_name TEXT,
        message_id INTEGER,
        date TEXT,
        sender_id INTEGER,
        first_name TEXT,
        last_name TEXT,
        username TEXT,
        message TEXT,
        media_type TEXT,
        media_path TEXT,
        reply_to INTEGER
    )
''')
conn.commit()

# === SCRAPE MESSAGES ===
def scrape_messages(entity, group_id, group_name, limit=100):
    all_messages = []
    offset_id = 0
    while True:
        history = client(GetHistoryRequest(
            peer=entity,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))
        if not history.messages:
            break

        for message in history.messages:
            data = {
                'id': None,
                'group_id': group_id,
                'group_name': group_name,
                'message_id': message.id,
                'date': str(message.date),
                'sender_id': message.from_id.user_id if message.from_id else None,
                'first_name': getattr(message.sender, 'first_name', None),
                'last_name': getattr(message.sender, 'last_name', None),
                'username': getattr(message.sender, 'username', None),
                'message': message.message,
                'media_type': type(message.media).__name__ if message.media else None,
                'media_path': None,
                'reply_to': message.reply_to_msg_id if message.reply_to_msg_id else None
            }
            all_messages.append(data)

            c.execute('''
                INSERT OR IGNORE INTO messages
                (group_id, group_name, message_id, date, sender_id, first_name, last_name, username, message, media_type, media_path, reply_to)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['group_id'], data['group_name'], data['message_id'], data['date'],
                data['sender_id'], data['first_name'], data['last_name'], data['username'],
                data['message'], data['media_type'], data['media_path'], data['reply_to']
            ))

        conn.commit()
        offset_id = history.messages[-1].id
        if len(history.messages) < limit:
            break

    return all_messages

# === SCRAPE MEMBERS ===
def scrape_members(entity):
    all_participants = []
    offset = 0
    limit = 100
    while True:
        try:
            participants = client.iter_participants(entity, limit=limit, offset=offset)
            batch = list(participants)
            if not batch:
                break
            for user in batch:
                user_data = {
                    "user_id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username
                }
                all_participants.append(user_data)
            offset += len(batch)
        except FloodWaitError as e:
            print(f"Flood wait, sleeping for {e.seconds} seconds...")
            time.sleep(e.seconds)
        except Exception as e:
            print(f"Error scraping members: {e}")
            break
    return all_participants

# === SCRAPE & EXPORT JSON ===
all_data = []

for group_id, group_name in TARGET_GROUPS.items():
    try:
        entity = client.get_entity(PeerChannel(group_id))
        full = client(GetFullChannelRequest(entity))
        member_count = full.full_chat.participants_count

        print(f"Scraping : {group_name} (ID: {group_id}) - {member_count} members")

        messages = scrape_messages(entity, group_id, group_name, limit=100)
        members = scrape_members(entity)

        group_data = {
            'group_name': group_name,
            'group_id': group_id,
            'member_count': member_count,
            'messages': messages,
            'members': members
        }

        all_data.append(group_data)

        # Export JSON individuel (avec écrasement)
        safe_name = re.sub(r'[^\w\s-]', '_', group_name)
        filename = f"{safe_name}_messages.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(group_data, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Erreur avec {group_name}: {e}")

# Export global JSON
with open("all_crypto_groups_messages.json", 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print("Export JSON terminé.")
