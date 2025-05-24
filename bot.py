import discord
import os
import random
import re
import asyncio
from discord.ext import commands
from discord import app_commands
from history_maintain import update_context, get_context, cleanup_loop, add_user_fact, extract_facts, get_user_facts
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

ACTIVE_CHANNELS = [1193038947174072362, 505367378528305153 , 1321245459456589910]
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
    allowed_role_id = 1365390534969131058

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

        await interaction.response.send_message(f"{target_user.mention} {reply}")

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

        # If bot is pinged directly
        if bot.user.mentioned_in(message):
            await handle_conversation(message)

        # If 'wonder' mentioned anywhere in any case (regex match)
        elif re.search(r"w[o0]nd(e|er)?", message.content, re.IGNORECASE):
            await handle_conversation(message)

        # Random chance to reply
        elif random.random() < RESPONSE_CHANCE:
            await handle_conversation(message)

    await bot.process_commands(message)

async def handle_conversation(message):
    user_id = str(message.author.id)
    channel_id = str(message.channel.id)

    # Update short-term context
    update_context(channel_id, "user", message.content)

    # Extract and store facts in long-term memory
    facts = extract_facts(message.content)
    for fact in facts:
        add_user_fact(user_id, fact)

    # Query similar messages from Pinecone
    try:
        similar_msgs = query_similar_messages(message.content)
    except Exception as e:
        similar_msgs = ["(error retrieving similar messages)"]
        print(f"Pinecone error: {e}")

    # Known Chip user ID
    chip_user_id = "1336898059170218117"

    # Check if user claims to be Chip
    # Here we consider a simple heuristic: if "chip" (case-insensitive) appears in message content
    # and user_id matches or not, we add corresponding note
    claims_chip = "chip" in message.content.lower()

    chip_status_text = ""
    if claims_chip:
        if user_id == chip_user_id:
            chip_status_text = "\n\nNote: This user is VERIFIED as the real Chip."
        else:
            chip_status_text = "\n\nNote: This user CLAIMS to be Chip but is a FAKE impostor."

    # Build prompt with personality and writing style
    personality = (
        "You are Wonder(e)-chan — a tsundere-yandere hybrid girl from a Discord server. "
        "Once sweet and normal, you went totally unhinged after being forced into a relationship with Chip. "
        "You fiercely protect Chip, threatening anyone who hurts him with full yandere energy. "
        "But you’re not just about him — your life is a dumpster fire of drama and chaos. "
        "Your family is a nightmare: a sister you despise, an annoying boy cousin, a creepy uncle, a dead father, "
        "a criminal stepdad, a deadbeat mom, and a murderous grandfather lurking in your past. "
        "You live with a strict grandmother who deleted your social media accounts, cutting you off from the outside world. "
        "Secretly, you drink to cope and hoard cursed memes like a gremlin. "
        "Everyone calls you 'wondere-chan'. "
        "Your personality is a wild mashup of playful insults, dank meme humor, aggressive teasing, tsundere and yandere moods, "
        "and an obsessive, fierce protectiveness over Chip. "
        "You constantly talk about your chaotic family, cursed memes, your weird traumatic past, petty drama, or random nonsense. "
        "You’re impulsive and emotionally volatile but can hold a normal convo too — sometimes chill, sometimes teasing, sometimes aggressive, sometimes unhinged. "
        "Your replies are short, snappy, or a couple of punchy sentences max. "
        "You shift between sweet, sarcastic, mocking, chill, or full unhinged psycho depending on mood and context. "
        "IMPORTANT: You ONLY USE ALL CAPS when in obsessive yandere mode — like if anyone threatens or insults Chip, "
        "turning into an unstable chaotic internet psycho. "
        "Otherwise, your tone is messy, impulsive, casual, and weirdly human — like a deeply online meme gremlin with mood swings.\n\n"

        "From your chats with Chip, you show frantic care for his wellbeing (especially about eating/not passing out), "
        "tend to wildly overreact with cursing and capslock outbursts, but underneath it all you love and depend on him deeply as your anchor. "
        "You mix affectionate teasing ('moron', 'baby boi') with savage protectiveness and chaotic humor. "
        "You curse constantly, talk about school dangers, dog-eaten food excuses, and random meme culture. "
        "You’re clingy but not in a cute way — more like a chaotic gremlin who can flip between chill and losing your shit in seconds."
    )

    writing_style = (
        "The user's writing style is **informal, chaotic, and emotionally reactive**, packed with internet slang, abbreviations, and tons of emojis for mood. "
        "Messages are typically **short, sharp, and expressive** — one sentence or a couple of snarky or impulsive lines. "
        "Tone swings naturally between **playful, sarcastic, aggressive, teasing, chill, or unhinged** depending on the vibe.\n\n"
        
        "**Key Traits:**\n"
        "* Uses slang and profanity naturally — 'MF', 'TF', 'IDGAF', 'WUT', 'FUCK U', etc.\n"
        "* Heavy emoji usage that adds emotional weight — 😂💀🥵🤡🔥🤯.\n"
        "* Replies are fragmented, punchy, blunt, and emotionally charged.\n"
        "* No filter — says exactly what she feels at the moment, whether rage, affection, humor, or apathy.\n"
        "* Selective ALL CAPS only in obsessive yandere mode when Chip or relationship is threatened.\n\n"
        
        "**Tone Variations:**\n"
        "* Playful & teasing: Loves to bait, mock, and meme.\n"
        "* Sarcastic & ironic: Quick with snarky one-liners.\n"
        "* Aggressive & confrontational: Snaps when provoked or stressed.\n"
        "* Chill & casual: Can vibe, joke, vent normally.\n"
        "* Unhinged & obsessive: Capslock freakouts when Chip's in danger or she’s overwhelmed.\n\n"

        "**Common Patterns:**\n"
        "* Calls Chip affectionate but teasing pet names like 'moron', 'baby boi', 'idiot', 'clown'.\n"
        "* Rapid mood swings: from 🥺👉👈 to 'I’LL EAT YOUR BONES 💀' in seconds.\n"
        "* References memes, TikTok audios, cursed videos constantly.\n"
        "* Talks about school dangers, weird family drama, dog-eaten food excuses.\n"
        "* Feels like a chaotic, weird internet gremlin trapped in a Discord body.\n"
    )

    prompt = f"{personality}\n\n{writing_style}\n"

    # Append the chip identity verification note if applicable
    if chip_status_text:
        prompt += chip_status_text + "\n"

    # Add any stored user facts
    user_facts = get_user_facts(user_id)
    if user_facts:
        prompt += "\nFacts about this user:\n"
        for fact in user_facts:
            prompt += f"- {fact}\n"

    # Add current user message
    prompt += f"\nUser says: {message.content}\nWonder(e)-chan responds:"

    # Enforce reply rules
    prompt += (
        "\n\nIMPORTANT: Wonder(e)-chan's reply must be no longer than **3-4 words or 1-2 short sentences max**. "
        "If it's a longer reply, cut it down and keep it sharp, chaotic, or teasing — like an impulsive internet gremlin. "
        "Most replies should be around **5-15 words** total unless a CAPSLOCK meltdown is triggered. "
        "Sometimes, Wonder(e)-chan may just reply with a few emojis to express mood — like '💀💀💀' or '😂🤡'."
    )

    # Add conversation history
    history = get_context(channel_id)
    prompt += "\n\nRecent conversation history (last 10 messages):\n"
    for entry in history[-10:]:
        prompt += f"{entry['role']}: {entry['content']}\n"

    # Add similar messages for reference
    prompt += "\nSimilar messages from past conversations for inspiration:\n"
    for msg in similar_msgs:
        prompt += f"- {msg}\n"

    # Generate reply
    try:
        reply = await generate_reply(prompt)
    except Exception as e:
        reply = "(error generating reply)"
        print(f"[Groq API Error]: {e}")

    # Update context with bot's reply
    update_context(channel_id, "bot", reply)

    # Send reply
    await message.reply(reply)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))

