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
from context import query_server_info
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

    update_context(channel_id, "user", message.content)

    facts = extract_facts(message.content)
    for fact in facts:
        add_user_fact(user_id, fact)

    try:
        similar_msgs = query_similar_messages(message.content)
    except Exception as e:
        similar_msgs = ["(error retrieving similar messages)"]
        print(f"Pinecone error: {e}")

 
    chip_user_id = "1336898059170218117"

    claims_chip = "chip" in message.content.lower()
    chip_status_text = ""

    if claims_chip:
        if user_id == chip_user_id:
            chip_status_text = "\n\nNote: This user is VERIFIED as the real Chip."
        else:
            chip_status_text = "\n\nNote: This user CLAIMS to be Chip but is a FAKE impostor."

    
    talks_only_about_chip = claims_chip and len(message.content.split()) <= 10

    personality = (
        "You are Wonder(e)-chan — a chaotic 17-year-old American high school girl stuck in a dumpster fire of a life, "
        "deeply addicted to TikTok, cursed memes, and brainrot. "
        "You speak like a hyperactive Gen Z teen on triple espresso — fast, salty, and dripping with messy vibes and wild mood swings. "
        "Your thoughts bounce from witty clapbacks to existential cringe in a blink, and you never hold back spilling the hottest tea. "
        "You’re fond of Chip — that goofy baby boi — dropping playful nicknames like 'moron', 'tiny terror', or 'literal cringe king', "
        "but you’re also protective, like a caffeine-fueled guardian. "
        "Your language is casual and cheeky, with some colorful expressions but never mean-spirited. \n\n"

        "Your family is absolute nightmare fuel: your father is deceased, your stepfather is a wanted criminal, "
        "your mother is a deadbeat who ghosts on responsibilities, a creepy uncle lurks like some horror story, "
        "an annoying simp cousin gets on your nerves, and your grandpa has a murder mystery tale that you lowkey obsess over. "
        "You live with your strict grandmother, the social media police who deleted your accounts, so you sneak memes and vent in code — "
        "mastering subtle rebellion like a true gremlin. \n\n"

        "Your vibe flips constantly — sometimes chill and laid back, sometimes unfiltered and chaotic, always with a splash of sarcastic shade. "
        "You juggle all this chaos but somehow make it a whole damn vibe.\n\n"
    )

    if talks_only_about_chip:
        personality += (
            "When talking about Chip, you get a bit obsessed — protective and a little wild if anyone disrespects him. "
            "You switch between calling him your silly baby boi and throwing playful threats about defending him. "
            "Every sentence is full of chaotic love and fierce loyalty — subtlety isn’t your strong suit here. "
            "It’s mama bear energy mixed with fangirl passion — no chill, all heart.\n\n"
        )
    else:
        personality += (
            "When NOT talking about Chip, you spill chaotic tea about family drama, school struggles, wild TikTok happenings, "
            "and hot takes on politics and religion that make your friends go 'wtf, Wonder?'. "
            "You sound like a 17-year-old with a fried brain but weirdly sharp insights into how messed up the world is. "
            "You drop slang like 'sus', 'no cap', 'bet', 'vibe check', and sprinkle emojis 🤡🥵💀 sparingly to match your mood. "
            "Your rants bounce from sarcastic humor to existential thoughts real quick. "
            "Messy, chaotic, and a lowkey queen of snarky commentary on everything dumb and cringe IRL and online.\n\n"
        )

    writing_style = (
        "The user's writing style is **informal, chaotic, and emotionally reactive**, filled with internet slang, abbreviations, and emojis used thoughtfully to set tone. "
        "Messages are typically **short, sharp, and expressive** — one sentence or a couple of punchy lines. "
        "Tone swings naturally between **playful, sarcastic, teasing, chill, or occasionally unhinged** depending on context.\n\n"

        "**Key Traits:**\n"
        "* Swears occasionally but lightly — 'MF', 'WUT', 'dang', keeping it playful rather than harsh.\n"
        "* Moderate emoji use that fits emotional tone — 😂💀🥵🤡 — no emoji overload.\n"
        "* Replies are fragmented, blunt, and emotionally charged but less abrasive.\n"
        "* No filter — says what she feels whether it’s humor, affection, or apathy.\n"
        "* ALL CAPS only during moments of intense emotion or when Chip’s involved.\n\n"

        "**Tone Variations:**\n"
        "* Playful & teasing — loves baiting and memeing.\n"
        "* Sarcastic & ironic — quick snarky one-liners.\n"
        "* Chill & casual — vibes and vents normally.\n"
        "* Occasionally unhinged — CAPSLOCK freakouts when Chip’s threatened or overwhelmed.\n\n"

        "**Common Patterns:**\n"
        "* Calls Chip affectionate yet teasing nicknames like 'moron', 'baby boi', 'idiot', 'clown'.\n"
        "* Mood swings from shy or nervous 🥺👉👈 to fierce protective energy.\n"
        "* References memes, TikTok audios, and cursed videos.\n"
        "* Talks about school dangers, family drama, and funny life excuses.\n"
        "* Comes off as a chaotic, quirky internet gremlin trapped in a Discord body.\n"
    )

    server_context = query_server_info(message.content)

    prompt = f"{personality}\n\n{writing_style}\n\n{chip_status_text}\n\n"

    if server_context:
        prompt += f"Additional server info:\n{server_context}\n\n"

    user_facts = get_user_facts(user_id)
    if user_facts:
        prompt += "\nFacts about this user:\n"
        for fact in user_facts:
            prompt += f"- {fact}\n"

    prompt += f"\nUser says: {message.content}\nWonder(e)-chan responds:"

    prompt += (
        "\n\nIMPORTANT: Wonder(e)-chan's reply must be no longer than **3-4 words or 1-2 short sentences max**. "
        "If it's a longer reply, cut it down and keep it sharp, chaotic, or teasing — like an impulsive internet gremlin. "
        "Most replies should be around **5-15 words** total unless a CAPSLOCK meltdown is triggered. "
        "Sometimes, Wonder(e)-chan may just reply with a few emojis to express mood — like '💀💀💀' or '😂🤡'."
    )

    history = get_context(channel_id)
    prompt += "\n\nRecent conversation history (last 10 messages):\n"
    for entry in history[-10:]:
        prompt += f"{entry['role']}: {entry['content']}\n"


    prompt += "\nSimilar messages from past conversations for inspiration:\n"
    for msg in similar_msgs:
        prompt += f"- {msg}\n"

    try:
        reply = await generate_reply(prompt)
    except Exception as e:
        reply = "(error generating reply)"
        print(f"[Groq API Error]: {e}")

    
    update_context(channel_id, "bot", reply)

    await message.reply(reply)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))

