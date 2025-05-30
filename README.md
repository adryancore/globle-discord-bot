# Globle Discord Bot

A Discord bot designed to enhance engagement in your #globle channel by tracking player scores, declaring daily winners, and sending timely reminders.

## Features

- **Score Tracking**: Automatically detects and records Globle scores from user messages
- **Daily Winner**: Declares a winner at the end of each day based on the fewest guesses
- **Personalized Reminders**: Sends reminders at 8am local time and 11pm Eastern Time
- **Leaderboard**: Displays the current day's leaderboard on demand
- **Timezone Management**: Users can set their local timezone for personalized morning reminders

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
   python globle_webhook.py
   ```

## Deploying on Replit

1. **Create a GitHub Repository**:
   - Create a private GitHub repository
   - Push your code to the repository (the `.gitignore` file will prevent sensitive data from being uploaded)

2. **Set Up Replit**:
   - Create a Replit account at [replit.com](https://replit.com/)
   - Create a new Repl and select "Import from GitHub"
   - Connect your GitHub account and select your repository

3. **Configure Environment Variables**:
   - In Replit, click on the lock icon in the sidebar to open the "Secrets" panel
   - Add the following secrets:
     - `DISCORD_WEBHOOK_URL`: Your Discord webhook URL
     - `GLOBLE_CHANNEL_ID`: Your Discord channel ID

4. **Enable "Always On"**:
   - Click on your profile picture in the top right
   - Go to "My Repls"
   - Find your Globle bot repl
   - Toggle "Always On" to keep your bot running 24/7

5. **Run Your Bot**:
   - Click the "Run" button at the top of the screen
   - Replit will install dependencies and start your bot

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
