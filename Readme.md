## Overview
This project is a comprehensive Discord bot system designed to collect, process, and analyze messages from specific users in Discord servers. The bot uses advanced AI models to generate context-aware, personality-driven responses. The system is divided into several parts, each responsible for a specific aspect of the overall functionality.

---

## Part 1: Discord Bot — Message Collection

### Purpose
Collect messages from specific users in specific Discord servers and save them to a CSV file for further processing.

### Key Components
- **Libraries Used:** `discord`, `asyncio`, `csv`, `html`
- **Target Filters:**  
  - `target_user_ids`: List of user IDs to track  
  - `target_guild_ids`: List of server IDs to scan

### Core Function: `on_ready()`
- Triggered when the bot logs in.
- Iterates through all guilds and channels.
- Skips channels without `read_message_history` permission.
- Fetches messages in batches of 100 using pagination.
- Filters messages by `target_user_ids`.
- Cleans message content (removes newlines, unescapes HTML).
- Writes to `user_messages.csv` with columns:
  - Guild, Channel, Author, Timestamp, Content

### Error Handling
- Catches exceptions per channel to avoid crashing the bot.

---

## Part 2: Pinecone — Embedding & Indexing

### Purpose
Convert messages into vector embeddings and store them in Pinecone for semantic search.

### Key Components
- **Libraries Used:** `pinecone`, `pandas`, `tqdm`, `time`
- **Model Used:** `llama-text-embed-v2`
- **Index Name:** `"wondere"`

### Workflow
1. **Initialize Pinecone Client**
2. **Check/Create Index**
   - Dimension: 1024
   - Metric: Cosine
3. **Load CSV**
   - Drop NaNs
   - Filter out empty or overly long messages
4. **Batch Embedding**
   - Batch size: 96
   - Generate embeddings
5. **Upsert to Pinecone**
   - Each vector includes:
     - `id`: Unique message ID
     - `values`: Embedding
     - `metadata`: Original message text
6. **Rate Limiting**
   - Adds `time.sleep(0.5)` between batches

---

## Part 3: Groq — Writing Style Analysis

### Purpose
Analyze the writing style, tone, and personality of the user based on their messages.

### Key Components
- **Libraries Used:** `groq`, `dotenv`, `csv`
- **Model Used:** `meta-llama/llama-4-scout-17b-16e-instruct`

### Functions
- **`load_messages_from_csv()`**
  - Loads messages from the CSV file.
- **`chunk_list(lst, n)`**
  - Splits the message list into chunks of size `n`.
- **`summarize_chunk(chunk_messages)`**
  - Sends a prompt to Groq to analyze writing style, tone, emoji usage, and common phrases.
- **`aggregate_summaries(summaries)`**
  - Combines all chunk summaries into a final personality profile.
- **`main(messages)`**
  - Orchestrates the entire process.

### Output
A detailed personality profile including:
- Writing style
- Tone
- Emoji usage
- Common phrases
- Behavioral patterns

---

## Part 4: Emoji Analysis

### Purpose
Extract and list all unique emojis used in the messages.

### Key Components
- **Libraries Used:** `pandas`, `emoji`

### Functions
- **`extract_emojis(text)`**
  - Extracts emojis from a string using `emoji.EMOJI_DATA`.

### Workflow
- Load messages from CSV.
- Extract emojis from each message.
- Flatten and deduplicate the list.
- Output a sorted list of unique emojis.

---

## Part 5: Interactive Discord Bot (Updated)

### Purpose
This module powers a real-time Discord bot that responds to users using contextual memory, semantic similarity, and a custom personality. It now includes **channel- and user-specific memory**, **server context awareness**, and **dynamic prompt construction**.

### Key Enhancements
- **Modular Imports**:
  - `query_similar_messages` from `pinecone_fetch`
  - `generate_reply` from `groq_fetch`
  - `query_server_info` from `context`
  - Context management functions from `history_maintain`
- **Improved Context Handling**:
  - Separate memory for **channels** and **users**
  - Dynamic prompt building using:
    - Channel history
    - User history
    - Server context
    - Semantic similarity
- **New Constants**:
  - `ACTIVE_CHANNELS`: List of channel IDs where the bot is active
  - `RESPONSE_CHANCE`: Probability of random reply (7%)

### Slash Commands (`GeneralCommands`)
- **`/ping`**: Checks if the bot is online.
- **`/convo_history`**: Displays the last 10 messages from the current channel. Uses `get_channel_context(channel_id)`.
- **`/toggle_responses`**: Toggles random response behavior. Controlled by `GeneralCommands.bot_active`.
- **`/bully`**: Generates a chaotic insult for a target user. Uses `generate_reply(prompt)` with a custom personality prompt (currently placeholder).

### Event: `on_ready()`
- Logs bot status.
- Registers and syncs slash commands.
- Starts the `cleanup_loop()` for memory management.

### Event: `on_message(message)`
- Triggers only in `ACTIVE_CHANNELS`.
- Responds if:
  - Bot is mentioned
  - Regex match for “wonder”
  - Random chance
- Updates channel context with:
  - Role: `"user"`
  - Content: `message.content`
  - Username: `message.author.display_name`
- Calls `handle_conversation(message)`.

### Function: `handle_conversation(message)`

#### Step-by-Step Logic
1. **Extract IDs**:
   - `user_id` and `channel_id` as strings.
2. **Query Similar Messages**:
   - Uses `query_similar_messages(message.content)`.
3. **Chip Identity Check**:
   - If message mentions "chip":
     - Adds a note if the user is or isn’t the real Chip.
     - Adjusts personality if the message is short and chip-focused.
4. **Build Prompt**:
   - Includes:
     - Personality (placeholder)
     - Writing style (placeholder)
     - Chip status
     - Server context from `query_server_info()`
     - User history from `get_user_context(user_id)`
     - Channel history from `get_channel_context(channel_id)`
     - Similar messages from Pinecone
     - Final user message and username
5. **Generate Reply**:
   - Sends prompt to `generate_reply()`
   - Updates channel context with bot’s reply
   - Sends reply in the channel

### Memory Management
- **Channel context** is updated in `on_message()` and used in `handle_conversation()`.
- **User context** is used to personalize replies and track user-specific behavior.
- **Memory cleanup** ensures the bot doesn’t retain stale or irrelevant data.

---

## Part 7: Server Context Module (`context.py`)

### Purpose
This module provides dynamic server-related context based on keywords found in user messages. It enriches the bot’s responses with relevant lore, history, and social dynamics of the Discord server.

### Key Features
- **Keyword-triggered context injection**:  
  The bot scans user messages for specific tokens and returns relevant server information.
- **Structured `server_info` dictionary**:
  - `overview`: General background of the server
  - `history`: Important events and incidents
  - `lore`: Cultural and meme-based elements
  - `admins_mods`: Info about moderators and admins
  - `members`: Notable active members
  - `banned`: Problematic or banned users

### Function: `query_server_info(input_text)`

#### Purpose
To return relevant server context based on the content of a user’s message.

#### Logic
1. **Normalize Input**:
   - Converts the input text to lowercase for case-insensitive matching.
2. **Token Matching**:
   - Checks for presence of keywords in the message.
   - Keywords are grouped by category (e.g., history, lore, members).
3. **Context Assembly**:
   - If a keyword matches a category, the corresponding section from `server_info` is appended to the response.
   - Multiple categories can be matched and combined.
4. **Return**:
   - A single string containing all matched context sections, stripped of extra whitespace.

### Example Use Case in Bot Flow
In `handle_conversation()` (from `bot.py`):
- The bot calls `query_server_info(message.content)`
- If relevant tokens are found, the returned context is added to the prompt
- This helps the bot generate more informed, personalized, and lore-aware responses

---

## Part 8: Memory Management System (`history_maintain.py`)

### Purpose
This module manages **short-term memory** for both channels and users, enabling the bot to maintain context-aware conversations. It also includes a background cleanup system to remove stale data.

### Key Enhancements
- **Dual Context Tracking**:
  - `channel_id` → for public conversation history
  - `user_id` → for private or user-specific memory
- **Persistent Storage**:
  - Uses `TinyDB` to store:
    - `conversations.json`: per-channel history
    - `user_conversations.json`: per-user history
    - `user_memory.json`: optional long-term memory (not yet used)
- **Automatic Cleanup**:
  - Removes inactive conversations after a timeout (default: 30 minutes)
  - Runs asynchronously every 60 seconds

### Functions

#### `update_channel_context(channel_id, role, content, username=None, max_messages=20)`
- **Purpose:** Update the conversation history for a specific channel.
- **Logic:**
  - Adds a new message entry with role, content, timestamp, and optional username.
  - Maintains a rolling window of the last `max_messages` (default: 20).
  - Updates or inserts the record in `db_convo`.

#### `update_user_context(user_id, role, content, username=None, max_messages=20)`
- **Purpose:** Update the conversation history for a specific user.
- **Logic:**
  - Same as `update_channel_context`, but stores data in `db_user_convo`.

#### `get_channel_context(channel_id)`
- **Purpose:** Retrieve the last messages from a specific channel.
- **Returns:** A list of message dictionaries (or empty list if none found).

#### `get_user_context(user_id)`
- **Purpose:** Retrieve the last messages from a specific user.
- **Returns:** A list of message dictionaries (or empty list if none found).

#### `remove_old_contexts(timeout=1800)`
- **Purpose:** Remove channel and user conversations that have been inactive for more than `timeout` seconds (default: 30 minutes).
- **Logic:**
  - Compares current time with `last_active` timestamp.
  - Deletes expired records from both `db_convo` and `db_user_convo`.

#### `cleanup_loop(interval=60, timeout=1800)`
- **Purpose:** Run `remove_old_contexts()` every `interval` seconds (default: 60).
- **Usage:** Called as a background task in `on_ready()` in `bot.py`.

### Integration in Bot Workflow
- **Channel context** is updated in `on_message()` and used in `handle_conversation()`.
- **User context** is used to personalize replies and track user-specific behavior.
- **Memory cleanup** ensures the bot doesn’t retain stale or irrelevant data.

---

## Part 9: Groq Integration Module (`groq_fetch.py`)

### Purpose
This module handles the interaction with the Groq API to generate AI-powered responses for the bot. It encapsulates the logic for sending prompts and receiving replies from the LLaMA-4 model.

### Key Features
- **Environment-based API key loading**:
  - Uses `dotenv` to securely load the `GROQ_API_KEY`.
- **Client Initialization**:
  - Initializes a `Groq` client using the provided API key.
- **Character Persona**:
  - The system prompt defines the bot’s personality.”

### Function: `generate_reply(prompt: str) -> str`

#### Purpose
To send a user-generated prompt to Groq and return a stylized, character-driven response.

#### Logic
1. **Prompt Construction**:
   - Sends a two-part message:
     - **System message**: Defines Wonder(e)-chan’s personality.
     - **User message**: Contains the dynamically generated prompt.
2. **Model Used**:
   - `meta-llama/llama-4-scout-17b-16e-instruct`
3. **Temperature**:
   - Set to `0.7` for creative but coherent responses.
4. **Error Handling**:
   - If the API call fails, logs the error and returns a fallback message:
     > “Oops — I couldn't think of a reply right now!”

### Integration in Bot Workflow
- Called in:
  - `/bully` command
  - `handle_conversation()` function
- Receives a prompt built from:
  - Personality
  - Writing style
  - Channel/user history
  - Server context
  - Semantic similarity
- Returns a reply that is:
  - In-character
  - Emotionally expressive
  - Contextually aware

---

## System Flow Summary

1. **Collect** messages → `user_messages.csv`
2. **Embed** messages → Pinecone
3. **Analyze** style → Groq
4. **Extract** emojis → Emoji list
5. **Respond** in real-time → Interactive bot
6. **Support** with memory, similarity, and reply generation

---


