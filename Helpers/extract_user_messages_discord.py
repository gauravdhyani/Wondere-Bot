import discord
import asyncio
import csv
import html

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

client = discord.Client(intents=intents)

target_user_ids = ["PLACEHOLDER"]  # Your target users
target_guild_ids = ["PLACEHOLDER"]  # Server IDs you care about

output_file = "user_messages.csv"

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

    with open(output_file, mode='w', newline='', encoding='utf-8-sig') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Guild', 'Channel', 'Author', 'Timestamp', 'Content'])  # CSV headers

        total_messages_checked = 0
        total_messages_found = 0

        for guild in client.guilds:
            if guild.id not in target_guild_ids:
                continue

            print(f"🔍 Searching in guild: {guild.name}")

            for channel in guild.text_channels:
                if not channel.permissions_for(guild.me).read_message_history:
                    print(f"Skipping {channel.name} (no permission)")
                    continue

                print(f"📜 Fetching messages from: {channel.name}")

                last_message = None
                while True:
                    try:
                        if last_message:
                            history = [m async for m in channel.history(limit=100, before=last_message)]
                        else:
                            history = [m async for m in channel.history(limit=100)]

                        if not history:
                            break  # No more messages

                        total_messages_checked += len(history)

                        for message in history:
                            if message.author.id in target_user_ids:
                                clean_content = html.unescape(message.content.replace('\n', ' '))
                                csv_writer.writerow([
                                    guild.name,
                                    channel.name,
                                    message.author.name,
                                    message.created_at.isoformat(),
                                    clean_content
                                ])
                                total_messages_found += 1

                        last_message = history[-1]

                    except Exception as e:
                        print(f"❌ Could not access {channel.name}: {e}")
                        break

        print(f"\nTotal messages scanned: {total_messages_checked}")
        print(f"Messages found from target users: {total_messages_found}")
        print(f"Results saved to {output_file}")

    await client.close()


def run_bot():
    try:
        asyncio.run(client.start('Enter your BOT TOKEN'))
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    run_bot()
