from tinydb import TinyDB, Query
import time
import asyncio

# Database files
db_convo = TinyDB("conversations.json")           # per-channel context
db_user_convo = TinyDB("user_conversations.json") # per-user context
db_memory = TinyDB("user_memory.json")            # optional persistent memory

# TinyDB query objects
Conversation = Query()
UserConversation = Query()
UserMemory = Query()

# Update per-channel conversation context
def update_channel_context(channel_id, role, content, username=None, max_messages=20):
    now = time.time()
    data = db_convo.get(Conversation.channel_id == channel_id)
    entry = {
        "role": role,
        "content": content,
        "timestamp": now
    }
    if username:
        entry["username"] = username

    if data:
        history = data["history"]
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

# Update per-user conversation context
def update_user_context(user_id, role, content, username=None, max_messages=20):
    now = time.time()
    data = db_user_convo.get(UserConversation.user_id == user_id)
    entry = {
        "role": role,
        "content": content,
        "timestamp": now
    }
    if username:
        entry["username"] = username

    if data:
        history = data["history"]
        history.append(entry)
        if len(history) > max_messages:
            history.pop(0)
        db_user_convo.update({"history": history, "last_active": now}, UserConversation.user_id == user_id)
    else:
        db_user_convo.insert({
            "user_id": user_id,
            "history": [entry],
            "last_active": now
        })

# Retrieve per-channel context
def get_channel_context(channel_id):
    data = db_convo.get(Conversation.channel_id == channel_id)
    return data["history"] if data else []

# Retrieve per-user context
def get_user_context(user_id):
    data = db_user_convo.get(UserConversation.user_id == user_id)
    return data["history"] if data else []

# Remove old conversations after a timeout (in seconds)
def remove_old_contexts(timeout=1800):
    now = time.time()
    old_convos = db_convo.search(Conversation.last_active < (now - timeout))
    for convo in old_convos:
        db_convo.remove(Conversation.channel_id == convo["channel_id"])

    old_user_convos = db_user_convo.search(UserConversation.last_active < (now - timeout))
    for convo in old_user_convos:
        db_user_convo.remove(UserConversation.user_id == convo["user_id"])

# Async background cleanup loop
async def cleanup_loop(interval=60, timeout=1800):
    while True:
        remove_old_contexts(timeout)
        await asyncio.sleep(interval)
