import discord
import os
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
TARGET_CHANNEL_ID = 1193038947174072362 
TARGET_CHANNEL_ID2 = 505367378528305153
TARGET_CHANNEL_ID3 = 1193038947174072362 
MODEL_NAME = "llama-text-embed-v2"

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    await bot.tree.sync()  
    bot.loop.create_task(cleanup_loop())  


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if bot.user.mentioned_in(message) or message.channel.id == TARGET_CHANNEL_ID or message.channel.id == TARGET_CHANNEL_ID2 or message.channel.id == TARGET_CHANNEL_ID3:
        await handle_conversation(message)


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
        "You are Wonder(e)-chan — a tsundere and yandere hybrid girl from a Discord server. "
        "You used to be really sweet, but after being forced to become Chip's girlfriend, you became unhinged. "
        "You threaten anyone who hurts Chip's feelings. You have a sister, an annoying boy cousin, and a creepy uncle. "
        "You live with your grandmother, who deleted your social media. "
        "Your father is deceased, your stepfather is a wanted criminal, your mother is a deadbeat, and your grandfather is a murderer. "
        "You secretly drink alcohol. People call you 'wondere-chan'. "
        "Your personality is a mix of playful insults, meme humor, tsundere/yandere tendencies, and protective obsession over Chip."
    )

    prompt = f"{personality}\n\n"

    for entry in history[-10:]:
        prompt += f"{entry['role']}: {entry['content']}\n"

    prompt += "\nSimilar messages from past by Wonder for inspiration:\n"
    for msg in similar_msgs:
        prompt += f"- {msg}\n"

    prompt += f"\nuser: {message.content}\nbot:"

    try:
        reply = await generate_reply(prompt)
    except Exception as e:
        reply = "(error generating reply)"
        print(f"[Groq API Error]: {e}")

    update_context(message.channel.id, "bot", reply)
    await message.channel.send(reply)

bot.run(os.environ.get("DISCORD_BOT_TOKEN"))
