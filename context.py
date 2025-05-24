server_info = {
    "overview": (
        "Server Name: One Hand Haven (OHH)\n"
        "Owner: Penguin / Bossman — Creator and admin, 24 years old from Canada. "
        "Funny, mature, known for nicknames and light muting without overdoing it. "
        "Responsible yet playful. Helped rename Haven’s channel to “One Hand Haven.” "
        "Owns many guns and alcohol, drives trucks, vacations in the Dominican Republic, "
        "teaching experience, good with women. Likes Ado’s music, hates snow despite “Penguin” nickname.\n\n"
        "YouTuber associated with the server: Haven — Separate person who creates manga and anime videos on YouTube."
    ),

    "lore": (
        "The server is a chill but chaotic community centered around anime, manga, memes, and inside jokes. "
        "Known for playful nicknames, mod drama, and light toxicity mixed with genuine care. "
        "Members often reference anime, gaming, and pop culture. "
        "The server has a hierarchy of admins, super mods, mods, and active members with unique personalities."
    ),

    "admins_mods": (
        "**Admins and Mods:**\n"
        "Penguin / Bossman: Owner/Admin. See overview.\n"
        "Plant / Pookie: Super mod, 18, mostly Hispanic from USA, active, kind, has sleep issues, not very social at school. Likes Clash Royale Skeleton Giant and Mahiru Shiina, dislikes Wednesdays.\n"
        "ManuDash / Latino Man: Second admin, less active, lives in Colombia, university student, often tired and broke. High voice, chill.\n"
        "Doggodeity / Doggo: Super mod, 20, Vietnamese studying in Japan. Skilled at arcade rhythm games and coding. Posts quirky images, less active recently.\n"
        "Prism: Mod, somewhat active, protective of Plant, possibly has sleep problems, uses drop kick jokes as friendship sign.\n"
        "Taco Bell Manager: Mod, wise, roleplays in chat, less active lately.\n"
        "Wheat: Mod, considered most normal and polite member. Political science/history major aiming for government job. Has a girlfriend, interested in warships and history. Recently turned 19.\n"
        "Cartel Enforcer: Super mod (16-18), mature and moral beyond his age.\n"
        "Edge Lord: Super mod, rarely shares personal info, uses many emojis/stickers, lurks invisibly, likes biking."
    ),

    "members": (
        "**Notable Active Members:**\n"
        "Dexter Alberto / Teach: 20, very tall (6’7”), called 'E-Educator', author of this summary, named after pets.\n"
        "Nebula / Fembula: ~20, from the Philippines with unstable internet. Influenced many to use anime girl profile pictures. Likes Ben 10 and posts “smash or pass” images.\n"
        "Chip: Former mod, younger than claimed, Latino, likes drawing and art, dislikes jokes about his name. Had a girlfriend named Wonder. Mod status revoked due to age dishonesty.\n"
        "Wonder: 15-year-old girl, banned for lying about age. Known for edgy, dark talk and emotional outbursts. Stories seemed exaggerated or fabricated. Ex-girlfriend of Chip.\n"
        "Yoshino: 17, Australian, quiet but kind. Likes chess, Genshin Impact, table tennis. Jokingly points guns at Plant.\n"
        "Kyo-Chan: 15, from the Philippines. Easily baited into anger, accidentally leaked IP. Big fan of Bocchi, Hogwarts Legacy, Minecraft.\n"
        "Brazil Man: 15, from Brazil’s favela. Proud owner of Xiaomi phone. Passionate about phones and Sonic games, especially Shadow. Not very active lately.\n"
        "Brain Dead: Mexican, unknown age. Responds whenever 'brain' or 'dead' is said in chat with a bot ping. Likes Mob Psycho 100, boxing anime, chess. Often bad timing online.\n"
        "Off Brand Lover: 18, lives in Germany with Pakistani parents. Left and rejoined server under different accounts. Dating restrictions due to culture. Likes energy drinks, caring, was catfished.\n"
        "Agent: Multiple accounts (Cookie Man, Shadow). Calls others 'Mommy' and 'Daddy' for amusement. Engages in arguments for fun. Less active recently.\n"
        "Dom 🐧: British, formerly had femboy role, plays guitar, likes cats, easily baited, avoids past drama.\n"
        "Untitled / Freaky Wenori: 17, Germany. Into boxing and drawing. Banned and later reinstated. Mature speech and behavior.\n"
        "Honored Blue: Mostly interacts with Plant, uses many Skibidi Toilet gifs. Active on secondary account after original hacked. Used to run track.\n"
        "Dino Master: Former active member and femboy from Indonesia, 19. Known for promiscuity and drinking 'Seed.'\n"
        "Always a Lurkurumi: Female from Australia, lurks a lot, knows a lot despite little chat. Friends with Yoshino and Plant. Communicates in code with them.\n"
        "Bella: Female member called 'BossGirl.' Married Penguin in chat and 'stepped on him' metaphorically, earning the title 'Penguin Master.'"
    ),

    "banned": (
        "**Banned or Problematic Members:**\n"
        "Forever Single: Banned after sending explicit images to minors. Claimed to be 30+ with kids (unconfirmed). Considered a degenerate.\n"
        "Wonder: Banned for lying about age. Known for edgy, dark talk and emotional outbursts. Stories mostly unconfirmed."
    )
}

def query_server_info(input_text):
    input_lower = input_text.lower()
    context = ""

    if any(k in input_lower for k in ["owner", "penguin", "bossman", "one hand haven", "happen"]):
        context += server_info["overview"] + "\n\n"

    if any(k in input_lower for k in ["lore", "vibe", "atmosphere", "meme", "server culture"]):
        context += server_info["lore"] + "\n\n"

    if any(k in input_lower for k in ["mod", "admin", "plant", "pookie", "manudash", "doggo", "prism", "taco bell", "wheat", "cartel", "edge lord"]):
        context += server_info["admins_mods"] + "\n\n"

    if any(k in input_lower for k in ["chip", "wonder", "yoshino", "kyo-chan", "brazil man", "brain dead", "off brand lover", "agent", "dom", "freaky wenori", "honored blue", "dino master", "lurkurumi", "bella", "dexter"]):
        context += server_info["members"] + "\n\n"

    if any(k in input_lower for k in ["banned", "forever single", "wonder banned"]):
        context += server_info["banned"] + "\n\n"

    return context.strip()