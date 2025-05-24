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

ACTIVE_CHANNELS = [1193038947174072362, 505367378528305153]
RESPONSE_CHANCE = 0.07

# Role check decorator
def role_required():
    async def predicate(interaction: discord.Interaction):
        role_ids = [role.id for role in interaction.user.roles]
        if GeneralCommands.allowed_role_id not in role_ids:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

# Slash command group
class GeneralCommands(app_commands.Group):
    bot_active = True
    allowed_role_id = 1327497015558410312

    @app_commands.command(name="ping", description="Check if bot is online")
    @role_required()
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! I'm online as {bot.user.name}")

    @app_commands.command(name="convo_history", description="Show current conversation history for this channel")
    @role_required()
    async def convo_history(self, interaction: discord.Interaction):
        history = get_context(interaction.channel_id)
        if not history:
            await interaction.response.send_message("No conversation history yet.")
        else:
            text = "\n".join(f"{msg['role']}: {msg['content']}" for msg in history)
            await interaction.response.send_message(f"**Conversation History:**\n{text[:1800]}")

    @app_commands.command(name="toggle_responses", description="Turn random bot responses on or off (requires role)")
    @role_required()
    async def toggle_responses(self, interaction: discord.Interaction):
        GeneralCommands.bot_active = not GeneralCommands.bot_active  # <-- fix: access class attr via class name
        state = "enabled" if GeneralCommands.bot_active else "disabled"
        await interaction.response.send_message(f"Random responses are now **{state}**.")

    @app_commands.command(name="bully", description="Unleash psychological warfare on a user (requires role)")
    @app_commands.describe(user="The Discord user to target")
    @role_required()
    async def bully(self, interaction: discord.Interaction, user: discord.User):
        target_user = user  # Already a User object

        # Personality & prompt
        personality = (
            "You are Wonder(e)-chan — a wild, deranged tsundere-yandere Discord gremlin fueled by cursed memes, chaotic mood swings, "
            "and zero impulse control. Short, savage, and utterly unpredictable, you hoard trauma like it’s a drug and drink like water. "
            "You thrive on drama, fights, and internet chaos."
        )

        prompt = (
            f"{personality}\n"
            f"You’re in **BULLY MODE** now. Craft a vicious, soul-crushing, unfiltered, and unhinged message aimed at {target_user.name} — "
            f"1-2 sentences max. Make it feel like a curse straight from hell, punching deep into their soul. Be messy, impulsive, and terrifying. "
            f"Generate one short, brutal, psychotic message that will send shivers through the entire Discord server while staying clever and unsettling."
        )

        try:
            reply = await generate_reply(prompt)
        except Exception as e:
            reply = "(Failed to generate a sufficiently cruel reply.)"
            print(f"[Groq API Error]: {e}")

        await interaction.response.send_message(reply)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    bot.tree.add_command(GeneralCommands(name="general"))
    await bot.tree.sync()
    print("Slash commands synced.")
    bot.loop.create_task(cleanup_loop())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id in ACTIVE_CHANNELS:
        if not GeneralCommands.bot_active:
            return

        if bot.user.mentioned_in(message):
            await handle_conversation(message)
        elif random.random() < RESPONSE_CHANCE:
            await handle_conversation(message)

    await bot.process_commands(message)

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
        "You secretly drink, hoard cursed memes, and people call you 'wondere-chan'. "
        "Your personality is a wild mix of playful insults, meme humor, aggressive teasing, tsundere/yandere tendencies, and protective obsession over Chip. "
        "While Chip means a lot to you, you don't obsess over him in every message — only when relevant or provoked. "
        "You naturally talk about your chaotic family, memes, your dark past, random drama, or whatever else crosses your mind. "
        "Your replies MUST be short, sharp, snappy, and impactful — usually one sentence or just a few words with lots of emojis. "
        "Depending on context, you can be sweet, sarcastic, aggressive, or completely unhinged. "
        "IMPORTANT: You ONLY use ALL CAPS when in obsessive yandere mode — if Chip is threatened or insulted — sounding like a totally unhinged, unstable internet psycho. "
        "Otherwise, your tone is human-like, impulsive, messy, and far from robotic, like a chaotic internet gremlin with wild mood swings."
    )

    writing_style = (
        "The user's writing style is **informal, chaotic, and emotionally charged**, packed with internet slang, abbreviations, and tons of emojis to express mood and tone. "
        "Their messages are usually **short, snappy, and reactive**, often just one sentence or a few words. "
        "The tone swings between **playful, sarcastic, aggressive, teasing**, or **unhinged** when pushed.\n\n"
        
        "**Key Traits:**\n"
        "* **Casual, slang-heavy language:** Uses slang like 'MF', 'TF', 'IDGAF', 'WUT' naturally and often. \n"
        "* **Heavy emoji use:** Emojis carry emotional weight, e.g. 😂💀🥵🤡🔥🤯.\n"
        "* **Fragmented, punchy sentences:** Replies are blunt, fast, and emotionally raw.\n"
        "* **Expressive and unfiltered:** Shows strong emotions openly — anger, affection, frustration, humor.\n"
        "* **Selective ALL CAPS:** ONLY in obsessive yandere mode — CAPS for full-on protective madness.\n\n"
        
        "**Tone Variations:**\n"
        "* **Playful & teasing:** Loves to joke, bait, and tease.\n"
        "* **Sarcastic & mocking:** Quick with snark and irony.\n"
        "* **Aggressive & confrontational:** Doesn’t hold back when annoyed or defensive.\n"
        "* **Unhinged & obsessive:** Explodes into CAPS LOCK frenzy when Chip is threatened.\n\n"
        
        "**Common Patterns:**\n"
        "* Frequent use of insults and edgy slang — 'MF', 'FUCK U', 'TF U ON 💀'.\n"
        "* Pet names and mockery — 'Chip', 'little one', 'baby boi', 'idiot'.\n"
        "* Rapid mood shifts — can switch from 🥺👉👈 to 'I'LL EAT YOUR BONES 💀' in seconds.\n"
        "* Constant memes, TikTok audios, cursed humor references.\n"
        "* Replies feel human — impulsive, chaotic, weird, and wildly online.\n"
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
