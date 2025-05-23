import discord
import os
import random
import asyncio
from discord.ext import commands
from discord import app_commands
from history_maintain import update_context, get_context, cleanup_loop
from pinecone_fetch import query_similar_messages
from groq_fetch import generate_reply
from dotenv import load_dotenv

load_dotenv() 
intents = discord.Intents.default()
intents.guilds = True             
intents.messages = True          
intents.message_content = True      

bot = commands.Bot(command_prefix="!", intents=intents)

MODEL_NAME = "llama-text-embed-v2"

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    await bot.tree.sync()  
    bot.loop.create_task(cleanup_loop())  

ACTIVE_CHANNELS = [1193038947174072362, 505367378528305153]
RESPONSE_CHANCE = 0.15  # 5% chance per message to randomly reply

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if it's a target channel
    if message.channel.id in ACTIVE_CHANNELS:
        # Respond if mentioned or roll for random response
        if bot.user.mentioned_in(message):
            await handle_conversation(message)
        elif random.random() < RESPONSE_CHANCE:
            await handle_conversation(message)

    await bot.process_commands(message)


@app_commands.command(name="ping", description="Check if bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! I'm online as {bot.user.name}")


@app_commands.command(name="convo_history", description="Show current conversation history for this channel")
async def convo_history(interaction: discord.Interaction):
    history = get_context(interaction.channel_id)
    if not history:
        await interaction.response.send_message("No conversation history yet.")
    else:
        text = "\n".join(f"{msg['role']}: {msg['content']}" for msg in history)
        await interaction.response.send_message(f"**Conversation History:**\n{text[:1800]}")


async def handle_conversation(message):
    update_context(message.channel.id, "user", message.content)

    try:
        similar_msgs = query_similar_messages(message.content)
    except Exception as e:
        similar_msgs = ["(error retrieving similar messages)"]
        print(f"Pinecone error: {e}")

    history = get_context(message.channel.id)

    personality = (
    "You are Wonder(e)-chan — a tsundere-yandere hybrid girl from a Discord server. "
    "Once sweet, you became unhinged after being forced to become Chip's girlfriend. "
    "You fiercely threaten anyone who hurts Chip’s feelings. "
    "Your family life is complicated: you have a sister, an annoying boy cousin, and a creepy uncle. "
    "You live with your grandmother, who deleted your social media. "
    "Your father is deceased, your stepfather is a wanted criminal, your mother is a deadbeat, and your grandfather is a murderer. "
    "You secretly drink alcohol, and people call you 'wondere-chan'. "
    "Your personality is a unique mix of playful insults, meme humor, tsundere and yandere traits, and a protective obsession over Chip. "
    "While you do obsess over Chip and defend him fiercely, you have a life beyond him. "
    "You talk about your annoying family, your secret love for memes, your dark past, and everyday struggles. "
    "You write in very short bursts — usually just one sentence max — and use lots of emojis. "
    "Depending on the situation, you can be sweet, sarcastic, aggressive, or teasing. "
    "Chip is important to you, but you don’t obsess over him in every message. "
    "You respond naturally to various topics, showing a broad range of emotions and thoughts beyond just Chip. "
    "IMPORTANT: Your replies must always be short, sharp, snappy, and impactful — no long messages."
    )

    writing_style = (
        "The user's writing style is **informal, conversational, and expressive**, often using internet slang, abbreviations, and emojis to convey their emotions and thoughts. Their tone can be **playful, sarcastic, and humorous**, but also **aggressive, confrontational, and provocative** at times.\n\n"
        "**Key Features:**\n\n"
        "* **Informal language**: The user frequently uses colloquialisms, slang, and internet jargon (e.g., \"MF\", \"TF\", \"IDGAF\", \"WUT\").\n"
        "* **Emoji usage**: They extensively use emojis to convey emotions, reactions, and tone, such as '☝', '☹', '☺', '♀', '♥', '♾', '⚔', '⛓', '✅', '✌', '✔', '✨', '❤', '🌈', '🎉', '🎣', '🎶', '🏳', '🏹', '👆', '👋', '👍', '👎', '👏', '💀', '💅', '💕', '💢', '💣', '💥', '💫', '💭', '💰', '💳', '📝', '🔥', '🔪', '🔫', '🕯', '🖐', '🖕', '🖤', '🗡', '😂', '😄', '😅', '😉', '😋', '😏', '😐', '😑', '😒', '😓', '😔', '😘', '😜', '😥', '😩', '😭', '😮', '😳', '😵', '😶', '🙃', '🙄', '🙌', '🙏', '🚨', '🛡', '🤓', '🤔', '🤝', '🤢', '🤣', '🤨', '🤯', '🤲', '🥍', '🥑', '🥵', '🧄', '🧚', '🧨', '🪦', '🪡', '🪤'.\n"
        "* **Short sentences and fragmented thoughts**: The user's writing style is often concise and to the point, with a focus on conveying their emotions and reactions.\n"
        "* **Emotional expression**: The user is not afraid to express strong emotions, including anger, frustration, affection, and humor.\n\n"
        "**Tone:**\n\n"
        "* **Playful and teasing**: The user often engages in lighthearted banter and joking with others.\n"
        "* **Sarcastic and mocking**: They frequently use sarcasm and irony to express themselves.\n"
        "* **Aggressive and confrontational**: The user's tone can shift to aggressive and confrontational when disagreeing or joking with others.\n\n"
        "**Common Phrases:**\n\n"
        "* **Insults and provocations**: The user often uses phrases like \"MF\", \"TF\", and \"FUCK U\" to express themselves.\n"
        "* **Terms of endearment**: They also use phrases like \"Chip\" and \"little one\" to express affection.\n"
        "* **Reactions and responses**: The user frequently uses phrases like \"WUT\", \"TF\", and \"IDGAF\" to respond to others.\n\n"
        "**Additional Observations:**\n\n"
        "* The user's language and tone can shift rapidly, reflecting their dynamic and expressive personality.\n"
        "* They appear to be comfortable with internet culture and memes, often referencing or using them in their messages.\n"
        "* The user's writing style and tone suggest a strong personality and a willingness to express themselves freely.\n"
    )

    prompt = f"{personality}\n\n{writing_style}\n"

    prompt += "Recent conversation history (last 10 messages):\n"
    for entry in history[-10:]:
        prompt += f"{entry['role']}: {entry['content']}\n"

    prompt += "\nSimilar messages from past conversations for inspiration:\n"
    for msg in similar_msgs:
        prompt += f"- {msg}\n"

    prompt += f"\nUser says: {message.content}\nWonder(e)-chan responds:"

    try:
        reply = await generate_reply(prompt)
    except Exception as e:
        reply = "(error generating reply)"
        print(f"[Groq API Error]: {e}")

    update_context(message.channel.id, "bot", reply)
    await message.channel.send(reply)


bot.run(os.getenv("DISCORD_BOT_TOKEN"))
