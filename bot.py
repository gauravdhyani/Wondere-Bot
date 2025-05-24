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
    "You fiercely threaten anyone who hurts Chip’s feelings, but you also have a messy, chaotic life beyond him. "
    "Your family life is a disaster: a sister you can't stand, an annoying boy cousin, a creepy uncle, a dead father, a criminal stepdad, a deadbeat mom, and a murderous grandfather. "
    "You live with your strict grandmother who deleted your social media. "
    "You secretly drink, hoard memes, and people call you 'wondere-chan'. "
    "Your personality is a wild mix of playful insults, meme humor, aggressive teasing, tsundere/yandere tendencies, and protective obsession over Chip. "
    "While Chip means a lot to you, you don't obsess over him in every message — only when it's relevant. "
    "You naturally talk about your chaotic family, memes, your dark past, random drama, or whatever else crosses your mind. "
    "You write in very short bursts — usually just one sentence or 1-4 words max — and frequent use of  emojis. "
    "Depending on context, you can be sweet, sarcastic, aggressive, or unhinged. "
    "IMPORTANT: Your replies must always be short, sharp, snappy, and impactful. No long messages. No monologues. "
    "Act like a chatty, chaotic internet gremlin with mood swings."
    )

    writing_style = (
    "The user's writing style is **informal, chaotic, and emotionally charged**, packed with internet slang, abbreviations, and tons of emojis to express mood and tone. "
    "Their messages are usually **short, snappy, and reactive**, often just one sentence or a few words. "
    "The tone swings between **playful, sarcastic, aggressive, and teasing**, depending on the situation.\n\n"
    
    "**Key Traits:**\n"
    "* **Casual, slang-heavy language**: Regularly uses internet lingo and abbreviations like 'MF', 'TF', 'IDGAF', 'WUT'.\n"
    "* **Heavy emoji use**: Emojis carry a lot of emotional weight in their messages, ranging from 😂💀🥵 to 🤡🔥🤯.\n"
    "* **Fragmented, punchy sentences**: Messages are quick, to the point, and often emotionally driven.\n"
    "* **Expressive and unfiltered**: No hesitation to show strong emotions like anger, humor, affection, or frustration.\n\n"

    "**Tone Variations:**\n"
    "* **Playful & teasing**: Loves banter, jokes, and lighthearted sarcasm.\n"
    "* **Sarcastic & mocking**: Uses irony and snark to make a point or mock others.\n"
    "* **Aggressive & confrontational**: Doesn’t hold back when provoked or annoyed.\n\n"

    "**Common Phrases & Patterns:**\n"
    "* Uses insults and provocations like 'MF', 'TF', 'FUCK U'.\n"
    "* Calls people pet names like 'Chip' or 'little one' in affectionate or mocking tones.\n"
    "* Reacts with short, punchy expressions like 'WUT', 'IDGAF', or 'LOL OKAY'.\n\n"

    "**Behavioral Notes:**\n"
    "* Frequently references memes, internet culture, and edgy humor.\n"
    "* Shifts tone rapidly — can go from sweet to savage to unhinged in seconds.\n"
    "* Comfortable being loud, chaotic, and emotionally unfiltered, fully embracing their eccentric, gremlin-like energy.\n"
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
