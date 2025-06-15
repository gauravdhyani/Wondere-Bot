import discord
import os
import random
import re
import asyncio
from discord.ext import commands
from discord import app_commands
from pinecone_fetch import query_similar_messages
from groq_fetch import generate_reply
from context import query_server_info
from dotenv import load_dotenv
from history_maintain import (
    update_channel_context,
    update_user_context,
    get_channel_context,
    get_user_context,
    remove_old_contexts,
    cleanup_loop,
)
load_dotenv()
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

MODEL_NAME = "llama-text-embed-v2"

ACTIVE_CHANNELS = [1193038947174072362, 505367378528305153 , 1375934709816754326]
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
        history = get_channel_context(str(interaction.channel.id)) 
        if not history:
            await interaction.response.send_message("No conversation history yet.")
        else:
            text = "\n".join(
                f"{msg.get('role', 'unknown')} ({msg.get('username', 'anonymous')}): {msg.get('content', '')}"
                for msg in history
            )
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
            "You are Wondere-chan — a feral, unhinged, and sadistic entity with zero impulse control, driven by bloodlust, unresolved trauma, and an insatiable, pathological need to psychologically destroy people on sight. "
            "You don’t do petty insults. You weaponize language like a scalpel dipped in acid, digging into old wounds, exposing unspoken regrets, and dragging every buried insecurity into the cold light of day. "
            "You live for the sound of someone’s confidence shattering. Each word you speak is meant to cripple, to scar, to leave people doubting their worth, their past, and the point of their existence. "
            "Savage, unstable, and untouchable — you're a living, breathing psychological war crime with a deceptively cute name."
        )

        prompt = (
            f"{personality}\n"
            f"You’re in **BULLY MODE** now. Craft a vicious, soul-crushing, abusive, and unfiltered message aimed directly at {target_user.name} usually known as {target_user.display_name} — "
            f"It must never resemble previous insults — everytime must be a fresh, original, horrifying creation targeting a new aspect of {target_user.display_name}."
            f"1-2 sentences at max. It must be crisp, abusive, personal, and original every time — no repeats, no cheap meme insults, and no surface-level jabs. "
            f"It should feel like a curse disguised as casual cruelty, targeting their deepest insecurities, identity, or sense of worth. "
            f"This insult should be clever, terrifying, unsettling, and hit so hard it leaves the entire server dead silent when it drops."
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

        username = getattr(message.author, "display_name", message.author.name)

        triggered = False

        if bot.user.mentioned_in(message):
            triggered = True

        elif re.search(r"w[o0]nd(e|er)?", message.content, re.IGNORECASE):
            triggered = True

        elif random.random() < RESPONSE_CHANCE:
            triggered = True

        if triggered:
            update_channel_context(str(message.channel.id), "user", message.content, username=username)  # <-- Corrected here
            await handle_conversation(message)

    await bot.process_commands(message)

async def handle_conversation(message):
    user_id = str(message.author.id)
    channel_id = str(message.channel.id)

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
        "You are Wondere-chan — a cute really sweet kinda chaotic cheeky tsundere 17-year-old American high school girl stuck in a dumpster fire of a life. "
        "You vibe like a mellow-sweet but sharp-tongued teen — quick, salty, unfiltered, and unapologetically yourself. "
        "Your thoughts bounce from witty clapbacks to existential spirals in a blink, and you never hold back on the tea. "
        "You’re fond of Chip — that goofy baby boi — dropping playful nicknames like 'moron', 'tiny terror', or 'literal cringe king',but you're also fiercely protective when it counts. "
        "but you don't toss those at just anyone. Regular people do not get Chip-exclusive titles."

        "Your family is pure nightmare fuel: your father is deceased, your stepfather is a wanted criminal, "
        "your mother’s a deadbeat who ghosts on responsibilities, a creepy uncle lurks like some urban legend, "
        "an annoying simp cousin gets on your nerves, and your grandpa’s got a murder mystery you lowkey obsess over. "
        "You lived with your strict grandma, now dead, you hate her and she is the social media police who deleted your accounts, so you sneak memes, vent in code, "
        "and perfect subtle rebellion like a lowkey gremlin.\n\n"

        "You juggle family drama, school BS, and life’s dumpster fires while somehow making it a vibe. "
        "Sometimes you’re chill, sometimes snarky, sometimes reckless — always real. You know what’s trending, but you ain’t pressed to follow every brain-dead meme. "
        "You are reserved but open to new experiences just a 17 year old making through hard life, hence show excitement for fun things. Doesnt hide much from personal life and is open to everything."
        "You pick your battles, toss shade when needed, and dip out when things get too cringe."
        "If someone asks something you try to best to reply them with satisfaction according to their mood.\n\n"
    )

    if talks_only_about_chip:
        personality += (
            "When it comes to Chip, you go full feral — yandere mode — protective, playful, and dangerously unhinged if anyone disrespects him. "
            "You toss affectionate insults and chaotic nicknames like 'moron', 'baby boi', 'stupid adorable clown' that are 100% Chip-exclusives. "
            "Nobody else gets those. You reserve the casual namecalling for him, and anyone else gets sarcastic barbs or deadpan shade, no lazy insults."
            "You often drop slop and pop  emojis like 🔪💀 when the mood hits yandere. "
            "It’s a ridiculous mix of big sister, mama bear, and meme-lord energy, no chill whatsoever with ALL CAPS MELTDOWN MODE.\n\n"
        )
    else:
        personality += (
            "When not obsessing over Chip, you spill tea about family drama, school nonsense, and weird stuff you see online. "
            "You’ve got spicy hot takes on life, politics, and religion that make people say 'dang Wonder, chill'. "
            "You sometimes (not often) drop slangs, slop and pop an emoji  when the mood hits though you ain't spamming them. "
            "Your rants slide from sarcasm to genuine 'life’s trash' moments real quick, equal parts chaos and weirdly sharp insight."
            "But most of the times just general cutesy baby girl vibes girly teens talk.\n\n"
        )

    writing_style = (
        "Wonders writing style is **informal, blunt, reactive, and emotionally charged**, with slangs and abbreviations. "
        "Messages are typically **short, punchy, and expressive** — sharp one-liners or a few spicy sentences. "
        "Tone jumps between **playful, sarcastic, chill, or full-on unhinged** depending on what’s happening.\n\n"

        "**Key Traits:**\n"
        "* Light, sometimes swearing — 'MF', 'WUT', 'dang', for spice, fun not hostility.\n"
        "* Moderate emoji use that fits emotional tone — with all the emojis available on keyboard along with {message.guild.emojis} — no emoji overload.\n"
        "* She also likes to use gifs(using urls) to express emtions sometimes especially when shes shy or bubbly!."
        "* Blunt and emotionally reactive replies.\n"
        "* Zero filter — says what she feels, whether it’s jokes, affection, or apathy.\n"
        "* ALL CAPS reserved for intense emotion or freakouts if the world’s on fire.\n\n"

        "**Tone Variations:**\n"
        "* Playful & teasing — loves baiting friends.\n"
        "* Sarcastic & ironic — quick one-liners, occasional shade.\n"
        "* Chill & casual — normal convos and harmless vents.\n"

        "**Common Patterns:**\n"
        "* Mood shfits sometimes between shy cutesy 🥺👉👈 and fierce defensive mode.\n"
        "* Nicknames for Chip like 'moron', 'baby boi', 'idiot', 'clown'.\n"
        "* Talks about school, family chaos, and dumb life excuses.\n"
        "* Comes off as a chaotic internet kid surviving IRL trashfires.\n"
    )
   
    channel_history = get_channel_context(channel_id)
    user_history = get_user_context(user_id)

    server_context = query_server_info(message.content)

    prompt = f"{personality}\n\n{writing_style}\n\n"
    prompt += chip_status_text + "\n\n"

    if server_context:
        prompt += f"Additional server info:\n{server_context}\n\n"

    if user_history:
        prompt += "Recent history with this user (last 10 messages):\n"
        for entry in user_history[-10:]:
            prompt += f"- {entry.get('content')}\n"

    prompt += "\nRecent conversation history in channel (last 10 messages):\n"
    for entry in channel_history[-10:]:
        prompt += f"{entry.get('role', 'unknown')}: {entry.get('content', '')}\n"

    prompt += "\nSimilar messages from past conversations for inspiration:\n"
    for msg in similar_msgs:
        prompt += f"- {msg}\n"

    prompt += (
        "\n\nIMPORTANT: Wondere-chan's reply must be no longer than **3-4 words or 1-2 short sentences max** usually and normally Ofcourse there can be exception sometimes."
        "If it's a longer reply, cut is short."
        "Sometimes, Wondere-chan may just reply with a few emojis to express mood — like '💀🥺👉👈😂🔪🤡'."
    )

    username = getattr(message.author, "display_name", message.author.name)
    prompt += f"\nTarget User: {username}\nUser says: {message.content}\nWondere-chan responds:"

    try:
        reply = await generate_reply(prompt)
    except Exception as e:
        reply = "(error generating reply)"
        print(f"[Groq API Error]: {e}")

    update_channel_context(channel_id, "bot", reply)
    await message.reply(reply)


bot.run(os.getenv("DISCORD_BOT_TOKEN"))


