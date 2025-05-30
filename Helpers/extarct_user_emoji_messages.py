import pandas as pd
import emoji

# Load your CSV file
df = pd.read_csv(r'.\user_messages.csv') #Path to extracted messages

# Function to extract emojis from a string
def extract_emojis(text):
    if not isinstance(text, str):
        return []
    return [char for char in text if char in emoji.EMOJI_DATA]

# Extract emojis from all messages and flatten the list
all_emojis = []
for message in df['Content']:
    all_emojis.extend(extract_emojis(message))

# Get unique emojis by converting to a set
unique_emojis = sorted(set(all_emojis))

# Print unique emojis
print("Unique emojis found in messages:")
print(unique_emojis)

