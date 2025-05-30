from groq import Groq
import os
import csv
api_key = "Your GROQ Key" #Place your key here
if not api_key:
    raise ValueError("GROQ_API_KEY not set in .env")

client = Groq(api_key=api_key)


def load_messages_from_csv(file_path):
    messages = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            content = row.get("Content", "").strip()
            if content:
                messages.append(content)
    return messages


def chunk_list(lst, n):
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def summarize_chunk(chunk_messages):
    chunk_text = "\n".join(chunk_messages)
    prompt = f"""
Analyze the following messages from a user. Describe their writing style, tone, emoji usage, and common phrases. Provide a concise summary.

Messages:
{chunk_text}
"""
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

def aggregate_summaries(summaries):
    combined = "\n\n".join(summaries)
    prompt = f"""
You are a helpful assistant. Combine the following style summaries into one clear and comprehensive writing style description.

Style Summaries:
{combined}
"""
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

def main(messages):
    chunk_size = 500  # adjust if needed based on token limits
    style_summaries = []

    print(f"Processing {len(messages)} messages in chunks of {chunk_size}...")

    for i, chunk in enumerate(chunk_list(messages, chunk_size), 1):
        print(f"Summarizing chunk {i} / {((len(messages)-1)//chunk_size)+1}")
        summary = summarize_chunk(chunk)
        style_summaries.append(summary)

    print("Aggregating summaries...")
    final_style_prompt = aggregate_summaries(style_summaries)

    print("\n--- Final Combined Writing Style Prompt ---\n")
    print(final_style_prompt)
    return final_style_prompt

if __name__ == "__main__":
    csv_file_path = r'.\user_messages.csv' #Path to extracted messages
    messages = load_messages_from_csv(csv_file_path)

    if not messages:
        print("No messages found! Load your messages into the 'messages' list.")
    else:
        main(messages)

