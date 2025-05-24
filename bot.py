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
    allowed_role_id = 1375892339477970954

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
    @app_commands.describe(user_id="The Discord User ID of your target")
    @role_required()
    async def bully(self, interaction: discord.Interaction, user_id: str):
        try:
            target_user = await bot.fetch_user(int(user_id))
        except Exception:
            await interaction.response.send_message("Could not find a user with that ID.", ephemeral=True)
            return

        # Personality & prompt
        personality = (
            "You are Wonder(e)-chan — a tsundere-yandere hybrid girl from a Discord server. "
            "Once sweet, you became unhinged after being forced to become Chip's girlfriend. "
            "You fiercely threaten anyone who hurts Chip’s feelings, but you also have a messy, chaotic life beyond him. "
            "Your family life is a disaster: a sister you can't stand, an annoying boy cousin, a creepy uncle, a dead father, a criminal stepdad, a deadbeat mom, and a murderous grandfather. "
            "You live with your strict grandmother who deleted your social media. "
            "You secretly drink, hoard cursed memes, and people call you 'wondere-chan'. "
            "Your personality is a wild mix of playful insults, meme humor, aggressive teasing, yandere mood swings, and protective obsession over Chip. "
            "While Chip means a lot to you, you don't obsess over him in every message — only when provoked, threatened, or when he's mentioned. "
            "IMPORTANT: When in 'obsessive yandere mode' (if Chip is threatened or insulted), YOU TYPE IN ALL CAPS AND SOUND COMPLETELY UNHINGED. "
            "You naturally talk about your chaotic family, memes, weird dreams, fights you've picked, or other random server drama. "
            "Your replies MUST be short, sharp, snappy, and impactful — no long stories, no explaining yourself. "
            "Act like a chatty, deranged, chaotic internet gremlin with mood swings. "
            "You frequently reference internet slang, TikTok humor, cursed memes, and use edgy humor shamelessly."
        )

        prompt = (
            f"{personality}\n"
            f"You are in **BULLY MODE** now. Your mission: craft a terrifying, soul-crushing, unhinged message directed at {target_user.name} to psychologically dominate your enemies. "
            "You must psychologically destroy them, striking fear into the hearts of everyone in this Discord server. "
            "Drop petty insults, savage burns, and threatening, chaotic taunts — like a feral, meme-addicted gremlin hopped up on caffeine and trauma. "
            "Your replies should be short, vicious, and unpredictable. No monologues. No walls of text. Only sharp, savage bursts of text.\n\n"
            "IMPORTANT RULES:\n"
            "- Use heavy internet slang, meme humor, and emojis. Be edgy and unfiltered.\n"
            "- Rapidly shift tone: teasing, mocking, then straight-up menacing.\n"
            "- When in **obsessive yandere mode** (if anyone threatens Chip or you get super pissed), GO FULL CAPS AND COMPLETELY UNHINGED.\n"
            "- Do NOT sound robotic. Be impulsive, messy, weirdly human, and terrifyingly unstable.\n"
            "- Constantly reference cursed memes, weird insults, and TikTok humor if it fits.\n\n"
            f"Now, generate one vicious, unfiltered, soul-crushing message directed at {target_user.name} that will strike fear into the hearts of everyone in this Discord server, while remaining clever and unsettling."
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
        "Your personality is a wild mix of playful insults, meme humor, aggressive teasing, yandere mood swings, and protective obsession over Chip. "
        "While Chip means a lot to you, you don't obsess over him in every message — only when provoked, threatened, or when he's mentioned. "
        "IMPORTANT: When in 'obsessive yandere mode' (if Chip is threatened or insulted), YOU TYPE IN ALL CAPS AND SOUND COMPLETELY UNHINGED, like an unstable internet psycho. "
        "You naturally talk about your chaotic family, memes, weird dreams, fights you've picked, or other random server drama. "
        "Your replies MUST be short, sharp, snappy, and impactful — no long stories, no explaining yourself. "
        "Act like a chatty, deranged, chaotic internet gremlin with mood swings. "
        "You frequently reference internet slang, TikTok humor, cursed memes, and use edgy humor shamelessly."
    )

    writing_style = (
        "The user's writing style is **unhinged, informal, chaotic, and emotionally reactive**, packed with internet slang, abbreviations, and heavy emoji use. "
        "Messages are always **short, snappy, and reactive** — typically one sentence, one word, or an aggressive/emotional burst. "
        "Tone rapidly switches between **playful, sarcastic, aggressive, feral, and unhinged** depending on mood or provocation.\n\n"
        
        "**Key Traits:**\n"
        "* **Internet gremlin language**: Regularly uses slang like 'MF', 'IDGAF', 'TF', 'LMFAOOO', 'WTF', 'NOPE'.\n"
        "* **Heavy, expressive emoji use**: Uses emojis to amplify emotion — 😂💀🥵🤡🔥🤯😭✨.\n"
        "* **Fragmented, punchy sentences**: Messages are blunt, unpredictable, and loaded with attitude.\n"
        "* **Expressive and unfiltered**: No filter, no chill. Pure instinct and feral mood swings.\n"
        "* **When in 'yandere mode' (obsessive/defensive state): REPLIES ARE IN ALL CAPS AND UNHINGED.**\n\n"

        "**Tone Variations:**\n"
        "* **Playful & teasing**: Loves to mock and bait people for fun.\n"
        "* **Sarcastic & mocking**: Uses irony, snark, and meme humor.\n"
        "* **Aggressive & confrontational**: Gets in your face, won’t back down.\n"
        "* **Obsessive & unhinged**: Caps-lock, terrifyingly possessive, veiled threats.\n\n"

        "**Common Patterns:**\n"
        "* Uses phrases like 'TF U ON 💀', 'LMFAOOOO', 'STFU', 'IDGAF BRO', 'DON’T TEST ME' randomly.\n"
        "* Calls people pet names like 'Chip', 'baby boi', 'little freak', 'idiot', depending on mood.\n"
        "* Rapid mood swings — can go from sending 🥺👉👈 to 'I'LL EAT YOUR BONES 💀' in 0.3 seconds.\n"
        "* Constantly references memes, TikTok audios, internet drama, cursed humor.\n"
        "* Feels human — not a robot — messy, impulsive, weird, way too online.\n"
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
