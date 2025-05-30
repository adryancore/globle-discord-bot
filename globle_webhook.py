import os
import json
import requests
import datetime
import time
import pytz
import re
from dotenv import load_dotenv
from flask import Flask, request, abort

# Load environment variables
load_dotenv()
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')
DISCORD_PUBLIC_KEY = os.getenv('DISCORD_PUBLIC_KEY', '')
# Use PORT environment variable for Replit compatibility
PORT = int(os.getenv('PORT', os.getenv('REPLIT_PORT', os.getenv('SERVER_PORT', '8080'))))

# Default timezone (Eastern Time)
DEFAULT_TIMEZONE = 'America/New_York'

# Data storage
SCORES_FILE = 'scores.json'
USER_TIMEZONES_FILE = 'user_timezones.json'

# Create Flask app for webhook listener
app = Flask(__name__)

# Load scores from file
def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, 'r') as f:
            return json.load(f)
    return {"date": datetime.datetime.now(pytz.timezone(DEFAULT_TIMEZONE)).strftime('%Y-%m-%d'), "scores": {}}

# Save scores to file
def save_scores(scores):
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f)

# Load user timezones from file
def load_user_timezones():
    if os.path.exists(USER_TIMEZONES_FILE):
        with open(USER_TIMEZONES_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save user timezones to file
def save_user_timezones(timezones):
    with open(USER_TIMEZONES_FILE, 'w') as f:
        json.dump(timezones, f)

# Reset scores for a new day
def reset_daily_scores():
    scores = {"date": datetime.datetime.now(pytz.timezone(DEFAULT_TIMEZONE)).strftime('%Y-%m-%d'), "scores": {}}
    save_scores(scores)
    return scores

# Send message to Discord via webhook
def send_discord_message(content):
    if not WEBHOOK_URL:
        print("Error: Discord webhook URL not set")
        return False
    
    data = {
        "content": content
    }
    
    response = requests.post(WEBHOOK_URL, json=data)
    
    if response.status_code == 204:
        return True
    else:
        print(f"Error sending message: {response.status_code}, {response.text}")
        return False

# Parse Globle score from message content
def parse_globle_score(content):
    # Convert to lowercase for easier matching
    content = content.lower()
    
    # Check if this is a Globle message
    if "globle" not in content:
        return None
    
    # Try different patterns to extract the score
    
    # Pattern 1: "I got it in X guesses"
    match = re.search(r'(?:got|solved|finished)(?:\s+it)?\s+in\s+(\d+)', content)
    if match:
        return int(match.group(1))
    
    # Pattern 2: "X/6" or similar patterns
    match = re.search(r'(\d+)\s*\/\s*\d+', content)
    if match:
        return int(match.group(1))
    
    # Pattern 3: "X guesses"
    match = re.search(r'(\d+)\s+guess(?:es)?', content)
    if match:
        return int(match.group(1))
    
    # Pattern 4: Just look for "Globle" and a number close by
    if "globle" in content:
        # Find all numbers in the message
        numbers = re.findall(r'\b(\d+)\b', content)
        if numbers:
            # Take the first number as the guess count (most likely to be the score)
            # Could be improved with more context analysis
            for num in numbers:
                if int(num) < 100:  # Reasonable guess limit
                    return int(num)
    
    return None

# Process a message for Globle score
def process_message(user_id, username, content):
    try:
        # Try to extract a score from the message
        guesses = parse_globle_score(content)
        
        if guesses is not None:
            scores = load_scores()
            
            # Check if it's a new day
            today = datetime.datetime.now(pytz.timezone(DEFAULT_TIMEZONE)).strftime('%Y-%m-%d')
            if scores["date"] != today:
                scores = reset_daily_scores()
            
            # Record the score if it's better than their previous score or first submission
            if user_id not in scores["scores"] or guesses < scores["scores"][user_id]:
                scores["scores"][user_id] = guesses
                save_scores(scores)
                
                # Provide feedback
                if len(scores["scores"]) == 1:
                    send_discord_message(f"Recorded your Globle score of {guesses} guesses, {username}! You're the first to submit today.")
                else:
                    send_discord_message(f"Recorded your Globle score of {guesses} guesses, {username}!")
                
                return True
    except Exception as e:
        print(f"Error processing message: {e}")
    
    return False

# Process a command message
def process_command(user_id, username, content):
    try:
        # Check for settz command
        if content.startswith("!settz "):
            # Extract timezone
            timezone_str = content[7:].strip()
            
            try:
                # Validate the timezone
                pytz.timezone(timezone_str)
                
                # Save the user's timezone
                timezones = load_user_timezones()
                timezones[user_id] = timezone_str
                save_user_timezones(timezones)
                
                send_discord_message(f"{username}, your timezone has been set to {timezone_str}. You'll receive reminders at 8am and 11pm in your local time.")
                return True
            except pytz.exceptions.UnknownTimeZoneError:
                send_discord_message(f"Unknown timezone: {timezone_str}. Please use a valid timezone from the IANA timezone database.")
                return True
        
        # Check for score command
        elif content == "!score":
            scores = load_scores()
            
            if user_id in scores["scores"]:
                send_discord_message(f"{username}, your best Globle score today is {scores['scores'][user_id]} guesses.")
            else:
                send_discord_message(f"{username}, you haven't submitted a Globle score today.")
            return True
        
        # Check for leaderboard command
        elif content == "!leaderboard":
            scores = load_scores()
            
            if not scores["scores"]:
                send_discord_message("No scores have been submitted today.")
                return True
            
            # Sort scores by number of guesses (ascending)
            sorted_scores = sorted(scores["scores"].items(), key=lambda x: x[1])
            
            # Create leaderboard message
            leaderboard = f"**Globle Leaderboard for {scores['date']}**\n\n"
            
            for i, (user_id, guesses) in enumerate(sorted_scores, 1):
                leaderboard += f"{i}. <@{user_id}>: {guesses} guesses\n"
            
            send_discord_message(leaderboard)
            return True
        
        # Check for help command
        elif content == "!help":
            help_text = "**Globle Bot Commands**\n\n"
            help_text += "• `!settz <timezone>` - Set your timezone (e.g., `!settz America/New_York`)\n"
            help_text += "• `!score` - Check your current Globle score\n"
            help_text += "• `!leaderboard` - Show the current day's leaderboard\n"
            help_text += "• `!help` - Show this help message\n\n"
            help_text += "You can also simply share your Globle score in the channel and I'll record it automatically!"
            
            send_discord_message(help_text)
            return True
    
    except Exception as e:
        print(f"Error processing command: {e}")
    
    return False

# Declare winner for the day
def declare_winner():
    try:
        scores = load_scores()
        
        # If no scores, nothing to do
        if not scores["scores"]:
            send_discord_message("No Globle scores were submitted today.")
            return
        
        # Sort scores by number of guesses (ascending)
        sorted_scores = sorted(scores["scores"].items(), key=lambda x: x[1])
        winner_id, winner_score = sorted_scores[0]
        
        # Get current date in Eastern Time
        now_et = datetime.datetime.now(pytz.timezone(DEFAULT_TIMEZONE))
        today_et = now_et.strftime('%Y-%m-%d')
        
        # Send winner announcement
        winner_message = f"🏆 **Globle Winner for {today_et}** 🏆\n\nCongratulations to <@{winner_id}> who solved today's Globle in just {winner_score} guesses!"
        send_discord_message(winner_message)
        
        # If there are more participants, show the full leaderboard
        if len(sorted_scores) > 1:
            leaderboard = "**Final Leaderboard**\n\n"
            for i, (user_id, guesses) in enumerate(sorted_scores, 1):
                leaderboard += f"{i}. <@{user_id}>: {guesses} guesses\n"
            
            send_discord_message(leaderboard)
        
        # Reset for the next day
        reset_daily_scores()
    except Exception as e:
        print(f"Error in declare_winner: {e}")

# Check for reminders based on user timezones
def check_reminders():
    try:
        now = datetime.datetime.now(pytz.UTC)
        timezones = load_user_timezones()
        
        morning_users = []
        evening_users = []
        
        for user_id, timezone_str in timezones.items():
            try:
                # Convert UTC time to user's local time
                user_tz = pytz.timezone(timezone_str)
                user_time = now.astimezone(user_tz)
                user_hour = user_time.hour
                
                # Morning reminder at 8am local time
                if user_hour == 8 and user_time.minute < 5:
                    morning_users.append(user_id)
                
                # Evening reminder at 11pm local time
                elif user_hour == 23 and user_time.minute < 5:
                    evening_users.append(user_id)
            except Exception as e:
                print(f"Error processing timezone for user {user_id}: {e}")
        
        # Send morning reminders
        if morning_users:
            morning_mentions = " ".join([f"<@{user_id}>" for user_id in morning_users])
            send_discord_message(f"Good morning {morning_mentions}! Don't forget to play Globle today: https://globle-game.com/")
        
        # Send evening reminders
        if evening_users:
            evening_mentions = " ".join([f"<@{user_id}>" for user_id in evening_users])
            send_discord_message(f"Hey {evening_mentions}! Have you played Globle today? If so, share your score!")
    except Exception as e:
        print(f"Error in check_reminders: {e}")

# Flask route to handle Discord webhook events
@app.route('/discord-webhook', methods=['POST'])
def discord_webhook():
    # Verify the request is from Discord (simplified for this example)
    # In production, you should verify the signature using DISCORD_PUBLIC_KEY
    
    # Get the JSON data from the request
    data = request.json
    
    # Check if this is a ping event
    if data.get('type') == 1:
        return {'type': 1}  # Respond to Discord's ping with a pong
    
    # Handle message events
    if data.get('type') == 0:
        # Check if this is a message
        if data.get('message'):
            message = data['message']
            content = message.get('content', '')
            user_id = message.get('author', {}).get('id')
            username = message.get('author', {}).get('username')
            
            # Ignore messages from bots
            if message.get('author', {}).get('bot', False):
                return {'status': 'ignored bot message'}
            
            # Process commands
            if content.startswith('!'):
                process_command(user_id, username, content)
            
            # Process potential Globle score
            process_message(user_id, username, content)
    
    return {'status': 'ok'}

# Main loop for scheduled tasks
def scheduled_tasks_loop():
    print("Starting scheduled tasks loop")
    
    try:
        while True:
            # Get current time in Eastern Time
            now_utc = datetime.datetime.now(pytz.UTC)
            now_et = now_utc.astimezone(pytz.timezone(DEFAULT_TIMEZONE))
            
            # Check if it's midnight Eastern Time to declare winner
            if now_et.hour == 0 and now_et.minute == 0:
                declare_winner()
            
            # Check reminders every hour
            if now_utc.minute == 0:
                check_reminders()
                
            # Wait until the next minute
            seconds_until_next_minute = 60 - datetime.datetime.now().second
            time.sleep(seconds_until_next_minute)
    except KeyboardInterrupt:
        print("Scheduled tasks loop stopped by user")
    except Exception as e:
        print(f"Error in scheduled tasks loop: {e}")

# Main function
def main():
    print("Starting Globle Discord Webhook Bot")
    print(f"Webhook URL: {'Set' if WEBHOOK_URL else 'Not Set'}")
    print(f"Default timezone: {DEFAULT_TIMEZONE}")
    
    # Send startup message
    if WEBHOOK_URL:
        send_discord_message("Globle Bot is now active! Default timezone is Eastern Time (ET).")
        send_discord_message("Use `!help` to see available commands.")
    
    import threading
    
    # Start the scheduled tasks in a separate thread
    scheduler_thread = threading.Thread(target=scheduled_tasks_loop)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Start the Flask app to listen for Discord webhook events
    print(f"Starting webhook listener on port {PORT}")
    app.run(host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    main()
