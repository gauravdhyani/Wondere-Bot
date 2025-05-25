from tinydb import TinyDB, Query
from datetime import datetime
import time
import asyncio
import re

db_convo = TinyDB("conversations.json")
db_memory = TinyDB("user_memory.json")

Conversation = Query()
UserMemory = Query()

def update_context(channel_id, role, content, username=None, max_messages=20):
    now = time.time()
    data = db_convo.get(Conversation.channel_id == channel_id)
    entry = {
        "role": role,
        "content": content,
        "timestamp": now,
    }
    if username:
        entry["username"] = username

    if data:
        history = data['history']
        history.append(entry)
        if len(history) > max_messages:
            history.pop(0)
        db_convo.update({"history": history, "last_active": now}, Conversation.channel_id == channel_id)
    else:
        db_convo.insert({
            "channel_id": channel_id,
            "history": [entry],
            "last_active": now
        })

def get_context(channel_id):
    data = db_convo.get(Conversation.channel_id == channel_id)
    return data['history'] if data else []

def remove_old_contexts(timeout=1800):  # 30 minutes inactivity
    now = time.time()
    old_convos = db_convo.search(Conversation.last_active < (now - timeout))
    for convo in old_convos:
        db_convo.remove(Conversation.channel_id == convo['channel_id'])

async def cleanup_loop():
    while True:
        remove_old_contexts()
        await asyncio.sleep(60)

def add_user_fact(user_id, fact):
    now = str(datetime.utcnow())
    record = db_memory.get(UserMemory.user_id == user_id)
    if record:
        facts = record.get("facts", [])
        if fact not in facts:
            facts.append(fact)
            db_memory.update({"facts": facts, "updated": now}, UserMemory.user_id == user_id)
    else:
        db_memory.insert({"user_id": user_id, "facts": [fact], "updated": now})

def get_user_facts(user_id):
    record = db_memory.get(UserMemory.user_id == user_id)
    return record["facts"] if record else []

def extract_facts(message):
    facts = []
    patterns = [
        r"my favorite (\w+) is (\w+)",
        r"i (love|like|hate) (.+)",
        r"i live in (.+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            fact = " ".join(match.groups())
            facts.append(fact)
    return facts
