from tinydb import TinyDB, Query
import time
import asyncio

db = TinyDB("conversations.json")
Conversation = Query()

def update_context(channel_id, role, content):
    now = time.time()
    data = db.get(Conversation.channel_id == channel_id)
    if data:
        history = data['history']
        history.append({"role": role, "content": content})
        if len(history) > 10:
            history.pop(0)
        db.update({"history": history, "last_active": now}, Conversation.channel_id == channel_id)
    else:
        db.insert({"channel_id": channel_id, "history": [{"role": role, "content": content}], "last_active": now})

def get_context(channel_id):
    data = db.get(Conversation.channel_id == channel_id)
    return data['history'] if data else []

def remove_old_contexts(timeout=300):  # 5 minutes inactivity
    now = time.time()
    old_conversations = db.search(Conversation.last_active < (now - timeout))
    for convo in old_conversations:
        db.remove(Conversation.channel_id == convo['channel_id'])

async def cleanup_loop():
    while True:
        remove_old_contexts()
        await asyncio.sleep(60)  # check every minute
