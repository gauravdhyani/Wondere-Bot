## Overview
This project is designed to create an intelligent Discord bot that collects messages from specific users, processes and analyzes these messages, and responds in real-time using AI. The system is divided into six parts, each with specific responsibilities and functionalities.

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
- **Triggered when the bot logs in.**
  - Iterates through all guilds and channels.
  - Skips channels without `read_message_history` permission.
  - Fetches messages in batches of 100 using pagination.
  - Filters messages by `target_user_ids`.
  - Cleans message content (removes newlines, unescapes HTML).
  - Writes to `user_messages.csv` with columns:
    - Guild, Channel, Author, Timestamp, Content

### Error Handling
- **Catches exceptions per channel to avoid crashing the bot.**

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

## Part 5: Interactive Discord Bot

### Purpose
Create a real-time interactive bot that responds to users using memory, semantic similarity, and a custom personality.

### Key Components
- **Libraries Used:** `discord`, `commands`, `app_commands`, `re`, `random`, `asyncio`
- **Triggers:**
  - Direct mention of the bot
  - Regex match for “wonder”
  - Random chance (7%)

### Slash Commands
- `/ping`: Check if bot is online
- `/convo_history`: Show recent conversation history
- `/toggle_responses`: Enable/disable random replies
- `/bully`: Generate a chaotic insult using Groq

### Function: `handle_conversation()`
- Updates conversation history
- Retrieves similar messages from Pinecone
- Builds a prompt using:
  - Personality
  - Recent history
  - Similar messages
- Sends prompt to Groq
- Replies in the channel and updates memory

---

## Part 6: Supporting Modules

### groq_fetch.py
- **Function: `generate_reply(prompt)`**
  - Sends prompt to Groq
  - Returns stylized reply as Wonder(e)-chan

### history_maintain.py
- **Function: `update_context(channel_id, role, content)`**
  - Stores last 10 messages per channel in TinyDB
- **Function: `get_context(channel_id)`**
  - Retrieves conversation history
- **Function: `cleanup_loop()`**
  - Removes inactive conversations every 60 seconds

### pinecone_fetch.py
- **Function: `query_similar_messages(input_text)`**
  - Embeds input
  - Queries Pinecone for top 5 similar messages
  - Returns their text

---

## System Flow Summary

1. **Collect** messages → `user_messages.csv`
2. **Embed** messages → Pinecone
3. **Analyze** style → Groq
4. **Extract** emojis → Emoji list
5. **Respond** in real-time → Interactive bot
6. **Support** with memory, similarity, and reply generation

---

---

## Detailed Function Analysis

### Part 1: Discord Bot — Message Collection

#### `on_ready()`
- **Purpose:** Initialize the bot and start collecting messages.
- **Logic:**
  - Connects to Discord and prints a login message.
  - Opens the CSV file for writing.
  - Iterates through all guilds the bot is part of.
  - Filters guilds based on `target_guild_ids`.
  - Iterates through text channels in each guild.
  - Checks for `read_message_history` permission.
  - Fetches messages in batches of 100 using pagination.
  - Filters messages by `target_user_ids`.
  - Cleans message content (removes newlines, unescapes HTML).
  - Writes filtered messages to the CSV file.
  - Prints summary statistics (total messages scanned, messages found).
  - Closes the bot connection.

#### `run_bot()`
- **Purpose:** Run the bot with error handling.
- **Logic:**
  - Starts the bot and handles keyboard interrupts and unexpected errors.

---

### Part 2: Pinecone — Embedding & Indexing

#### `initialize_pinecone()`
- **Purpose:** Initialize Pinecone client and check/create index.
- **Logic:**
  - Initializes Pinecone client.
  - Checks if the index `"wondere"` exists.
  - Creates the index if it doesn't exist with specified dimensions and metric.

#### `load_and_clean_messages()`
- **Purpose:** Load messages from CSV and clean them.
- **Logic:**
  - Loads messages from the CSV file.
  - Drops NaNs and filters out empty or overly long messages.

#### `embed_and_upsert_messages()`
- **Purpose:** Embed messages and upsert them to Pinecone.
- **Logic:**
  - Batches messages into groups of 96.
  - Generates embeddings using `llama-text-embed-v2`.
  - Prepares vectors with metadata.
  - Upserts vectors to Pinecone index.
  - Adds rate limiting between batches.

---

### Part 3: Groq — Writing Style Analysis

#### `load_messages_from_csv()`
- **Purpose:** Load messages from the CSV file.
- **Logic:**
  - Opens the CSV file and reads messages into a list.

#### `chunk_list(lst, n)`
- **Purpose:** Split the message list into chunks of size `n`.
- **Logic:**
  - Iterates over the list and yields successive n-sized chunks.

#### `summarize_chunk(chunk_messages)`
- **Purpose:** Send a prompt to Groq to analyze writing style.
- **Logic:**
  - Joins chunk messages into a single string.
  - Constructs a prompt with the chunk messages.
  - Sends the prompt to Groq and retrieves the summary.

#### `aggregate_summaries(summaries)`
- **Purpose:** Combine all chunk summaries into a final personality profile.
- **Logic:**
  - Joins all summaries into a single string.
  - Constructs a prompt with the combined summaries.
  - Sends the prompt to Groq and retrieves the final profile.

#### `main(messages)`
- **Purpose:** Orchestrate the entire process.
- **Logic:**
  - Splits messages into chunks.
  - Summarizes each chunk.
  - Aggregates all summaries into a final profile.

---

### Part 4: Emoji Analysis

#### `extract_emojis(text)`
- **Purpose:** Extract emojis from a string using `emoji.EMOJI_DATA`.
- **Logic:**
  - Iterates over each character in the text.
  - Checks if the character is an emoji.
  - Returns a list of emojis found in the text.

#### `main()`
- **Purpose:** Extract and list all unique emojis used in the messages.
- **Logic:**
  - Loads messages from the CSV file.
  - Extracts emojis from each message.
  - Flattens and deduplicates the list.
  - Outputs a sorted list of unique emojis.

---

### Part 5: Interactive Discord Bot

#### `on_ready()`
- **Purpose:** Initialize the bot and sync slash commands.
- **Logic:**
  - Prints a login message.
  - Adds slash commands to the bot.
  - Syncs slash commands with Discord.
  - Starts a background task to clean up old conversation history.

#### `on_message()`
- **Purpose:** Listen for messages and trigger responses.
- **Logic:**
  - Checks if the message author is the bot.
  - Checks if the message is in active channels.
  - Checks if the bot is mentioned directly.
  - Checks for regex match for “wonder”.
  - Checks for random chance to reply.
  - Calls `handle_conversation()` if any condition is met.

#### `handle_conversation(message)`
- **Purpose:** Handle conversation and generate replies.
- **Logic:**
  - Updates conversation history.
  - Retrieves similar messages from Pinecone.
  - Builds a prompt with personality, recent history, and similar messages.
  - Sends the prompt to Groq and retrieves the reply.
  - Updates conversation history with the reply.
  - Sends the reply in the channel.

---

### Part 6: Supporting Modules

#### `groq_fetch.py`

##### `generate_reply(prompt)`
- **Purpose:** Generate a reply using Groq’s LLaMA model.
- **Logic:**
  - Constructs a prompt with the user message.
  - Sends the prompt to Groq and retrieves the reply.
  - Returns the reply.

#### `history_maintain.py`

##### `update_context(channel_id, role, content)`
- **Purpose:** Update conversation history in TinyDB.
- **Logic:**
  - Retrieves existing conversation history for the channel.
  - Appends the new message to the history.
  - Removes old messages if history exceeds 10 messages.
  - Updates the conversation history in TinyDB.

##### `get_context(channel_id)`
- **Purpose:** Retrieve conversation history from TinyDB.
- **Logic:**
  - Retrieves conversation history for the channel from TinyDB.
  - Returns the history.

##### `cleanup_loop()`
- **Purpose:** Periodically remove inactive conversations.
- **Logic:**
  - Removes conversations with inactivity greater than 5 minutes.
  - Runs every 60 seconds.

#### `pinecone_fetch.py`

##### `query_similar_messages(input_text)`
- **Purpose:** Retrieve semantically similar messages from Pinecone.
- **Logic:**
  - Embeds the input text using `llama-text-embed-v2`.
  - Queries Pinecone for top 5 similar messages.
  - Returns the text of similar messages.

---

## System Flow Summary

1. **Collect** messages → `user_messages.csv`
2. **Embed** messages → Pinecone
3. **Analyze** style → Groq
4. **Extract** emojis → Emoji list
5. **Respond** in real-time → Interactive bot
6. **Support** with memory, similarity, and reply generation

---

