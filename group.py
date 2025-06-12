from telethon.sync import TelegramClient

api_id = 22052131
api_hash = 'ead6fa3c9f9671864fac02199dfafce2'
phone = '+33755857070' # Ton numéro

client = TelegramClient('session_name', api_id, api_hash)
client.start(phone)

for dialog in client.iter_dialogs():
    print(f"{dialog.name} — ID: {dialog.id}")
