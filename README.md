# Globle Discord Bot

A Discord bot designed to enhance engagement in your #globle channel by tracking player scores, declaring daily winners, and sending timely reminders.

## Features

- **Score Tracking**: Automatically detects and records Globle scores from user messages
- **Daily Winner**: Declares a winner at the end of each day based on the fewest guesses
- **Personalized Reminders**: Sends reminders at 8am and 9pm in each user's local timezone
- **Leaderboard**: Displays the current day's leaderboard on demand

## Setup Instructions

1. **Prerequisites**:
   - Python 3.8 or higher
   - A Discord account and server with admin permissions

2. **Discord Bot Setup**:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application and add a bot
   - Enable the "Message Content Intent" and "Server Members Intent" under the Bot section
   - Copy your bot token for later use
   - Use the OAuth2 URL Generator to create an invite link with the `bot` scope and permissions:
     - Read Messages/View Channels
     - Send Messages
     - Add Reactions
     - Read Message History
   - Invite the bot to your server using the generated link

3. **Installation**:
   ```bash
   # Clone the repository or download the files
   # Install dependencies
   pip install -r requirements.txt
   
   # Create .env file from the example
   cp .env.example .env
   ```

4. **Configuration**:
   - Edit the `.env` file with your Discord bot token
   - Add your Globle channel ID (right-click on the channel and select "Copy ID")

5. **Running the Bot**:
   ```bash
   python bot.py
   ```

## Usage

### Commands

- `!settz <timezone>` - Set your timezone (e.g., `!settz America/New_York`)
- `!score` - Check your current Globle score for the day
- `!leaderboard` - Show the current day's leaderboard

### Automatic Features

- **Score Detection**: The bot automatically detects Globle scores when users share their results
- **Morning Reminder**: Users receive a reminder at 8am in their local timezone to play Globle
- **Evening Check-in**: At 9pm local time, users are asked if they've played Globle for the day
- **Winner Declaration**: At midnight UTC, the bot declares the day's winner and resets scores

## Timezone Information

Users must set their timezone using the `!settz` command to receive personalized reminders. Valid timezone formats follow the IANA timezone database (e.g., `America/New_York`, `Europe/London`, `Asia/Tokyo`).

## Troubleshooting

- If the bot doesn't respond to commands, ensure it has the proper permissions in your Discord server
- If score detection isn't working, make sure users are sharing their Globle results in a format that includes the word "Globle" and "guesses"
- For timezone issues, verify that users are using valid IANA timezone names
