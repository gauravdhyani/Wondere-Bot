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

import re

def extract_facts(message):
    facts = []
    patterns = [
        # Personal info
        r"my name is (.+)",
        r"i am (\d+) years? old",
        r"i was born in (.+)",
        r"my birthday is (.+)",
        r"i am from (.+)",
        r"i live in (.+)",
        r"i currently reside in (.+)",
        r"i moved to (.+)",
        
        # Work and education
        r"i work as a[n]? (.+)",
        r"i am a[n]? (.+)",
        r"i study (.+)",
        r"i go to (.+)",
        r"i graduated from (.+)",
        
        # Preferences & hobbies
        r"my favorite (\w+) is (.+)",
        r"i (love|like|enjoy|hate) (.+)",
        r"i like to (.+)",
        r"my (?:hobby|hobbies) (?:are|is) (.+)",
        r"i spend my free time (.+)",
        r"i prefer (.+)",
        
        # Family and pets
        r"i have (\d+) (brothers|sisters|siblings|children|pets)",
        r"i have a (son|daughter|brother|sister|dog|cat) named (.+)",
        r"my pet's name is (.+)",
        
        # Skills & languages
        r"i speak (.+)",
        r"i can (.+)",
        r"i know how to (.+)",
        r"i play (.+)",
        
        # Travel & locations
        r"i have been to (.+)",
        r"i want to visit (.+)",
        r"i travel to (.+) often",
        
        # Food and drink
        r"my favorite food is (.+)",
        r"my favorite drink is (.+)",
        r"i like to eat (.+)",
        r"i don't like (.+)",
        
        # Relationships
        r"i am (single|married|divorced|engaged|in a relationship)",
        r"my partner's name is (.+)",
        
        # Media & entertainment
        r"my favorite movie is (.+)",
        r"my favorite song is (.+)",
        r"my favorite book is (.+)",
        r"i watch (.+)",
        r"i listen to (.+)",
        
        # Sports & fitness
        r"i play (.+)",
        r"i support (.+)",
        r"i exercise by (.+)",
        
        # Technology & gaming
        r"i use (.+)",
        r"i play the game (.+)",
        
        # Miscellaneous
        r"i have a (.+)",
        r"i believe in (.+)",
        r"i fear (.+)",
        r"i dream of (.+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            fact = " ".join(match.groups())
            facts.append(fact)
    
    return facts

