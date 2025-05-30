import os
import nextcord
from nextcord.ext import commands
import datetime
import json
import pytz
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GLOBLE_CHANNEL_ID = int(os.getenv('GLOBLE_CHANNEL_ID', 0))

# Bot setup with intents
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Data storage
SCORES_FILE = 'scores.json'
USER_TIMEZONES_FILE = 'user_timezones.json'

# Load scores from file
def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, 'r') as f:
            return json.load(f)
    return {"date": datetime.datetime.now().strftime('%Y-%m-%d'), "scores": {}}

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
    scores = {"date": datetime.datetime.now().strftime('%Y-%m-%d'), "scores": {}}
    save_scores(scores)
    return scores

# Bot events
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    
    # Start background tasks
    bot.loop.create_task(schedule_daily_tasks())
    print("Scheduler started!")

async def schedule_daily_tasks():
    while True:
        try:
            # Get current time
            now = datetime.datetime.now(pytz.UTC)
            
            # Check if it's midnight UTC to declare winner
            if now.hour == 0 and now.minute == 0:
                await declare_winner()
            
            # Check reminders every hour
            if now.minute == 0:
                await check_reminders()
                
            # Wait until the next minute
            seconds_until_next_minute = 60 - now.second
            await asyncio.sleep(seconds_until_next_minute)
        except Exception as e:
            print(f"Error in schedule_daily_tasks: {e}")
            await asyncio.sleep(60)  # Wait a minute before trying again

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Only process messages in the Globle channel
    if GLOBLE_CHANNEL_ID and message.channel.id != GLOBLE_CHANNEL_ID:
        await bot.process_commands(message)
        return
    
    # Check if the message contains a Globle score
    if "Globle" in message.content and "guesses" in message.content.lower():
        # Try to extract the number of guesses
        try:
            # Look for patterns like "I got it in X guesses" or "X/6" or similar
            content = message.content.lower()
            guesses = None
            
            # Check for common patterns
            if "i got it in " in content:
                parts = content.split("i got it in ")
                if len(parts) > 1:
                    num_part = parts[1].split()[0]
                    if num_part.isdigit():
                        guesses = int(num_part)
            
            # Check for X/6 pattern
            elif "/" in content:
                for word in content.split():
                    if "/" in word:
                        num_part = word.split("/")[0]
                        if num_part.isdigit():
                            guesses = int(num_part)
            
            # If we found a valid guess count
            if guesses is not None:
                scores = load_scores()
                
                # Check if it's a new day
                today = datetime.datetime.now().strftime('%Y-%m-%d')
                if scores["date"] != today:
                    scores = reset_daily_scores()
                
                # Record the score
                user_id = str(message.author.id)
                if user_id not in scores["scores"] or guesses < scores["scores"][user_id]:
                    scores["scores"][user_id] = guesses
                    save_scores(scores)
                    await message.add_reaction("🌎")
                    
                    # Provide feedback
                    if len(scores["scores"]) == 1:
                        await message.channel.send(f"Recorded your Globle score of {guesses} guesses, {message.author.display_name}! You're the first to submit today.")
                    else:
                        await message.channel.send(f"Recorded your Globle score of {guesses} guesses, {message.author.display_name}!")
        except Exception as e:
            print(f"Error processing Globle score: {e}")
    
    await bot.process_commands(message)

# Commands
@bot.command(name='settz', help='Set your timezone (e.g., !settz America/New_York)')
async def set_timezone(ctx, timezone=None):
    if not timezone:
        await ctx.send("Please provide a timezone. Example: `!settz America/New_York`")
        return
    
    try:
        # Validate the timezone
        pytz.timezone(timezone)
        
        # Save the user's timezone
        timezones = load_user_timezones()
        timezones[str(ctx.author.id)] = timezone
        save_user_timezones(timezones)
        
        await ctx.send(f"Your timezone has been set to {timezone}. You'll receive reminders at 8am and 9pm in your local time.")
    except pytz.exceptions.UnknownTimeZoneError:
        await ctx.send(f"Unknown timezone: {timezone}. Please use a valid timezone from the IANA timezone database.")

@bot.command(name='score', help='Check your current Globle score')
async def check_score(ctx):
    scores = load_scores()
    user_id = str(ctx.author.id)
    
    if user_id in scores["scores"]:
        await ctx.send(f"Your best Globle score today is {scores['scores'][user_id]} guesses.")
    else:
        await ctx.send("You haven't submitted a Globle score today.")

@bot.command(name='leaderboard', help='Show the current Globle leaderboard')
async def show_leaderboard(ctx):
    scores = load_scores()
    
    if not scores["scores"]:
        await ctx.send("No scores have been submitted today.")
        return
    
    # Sort scores by number of guesses (ascending)
    sorted_scores = sorted(scores["scores"].items(), key=lambda x: x[1])
    
    # Create leaderboard message
    leaderboard = f"**Globle Leaderboard for {scores['date']}**\n\n"
    
    for i, (user_id, guesses) in enumerate(sorted_scores, 1):
        user = await bot.fetch_user(int(user_id))
        leaderboard += f"{i}. {user.display_name}: {guesses} guesses\n"
    
    await ctx.send(leaderboard)

# Scheduled tasks
async def declare_winner():
    try:
        scores = load_scores()
        
        # If no scores, nothing to do
        if not scores["scores"]:
            channel = bot.get_channel(GLOBLE_CHANNEL_ID)
            if channel:
                await channel.send("No Globle scores were submitted today.")
            return
        
        # Sort scores by number of guesses (ascending)
        sorted_scores = sorted(scores["scores"].items(), key=lambda x: x[1])
        winner_id, winner_score = sorted_scores[0]
        
        # Get the winner's user object
        winner = await bot.fetch_user(int(winner_id))
        
        # Send winner announcement
        channel = bot.get_channel(GLOBLE_CHANNEL_ID)
        if channel:
            await channel.send(f"🏆 **Today's Globle Winner** 🏆\n\nCongratulations to {winner.mention} who solved today's Globle in just {winner_score} guesses!")
            
            # If there are more participants, show the full leaderboard
            if len(sorted_scores) > 1:
                leaderboard = "**Final Leaderboard**\n\n"
                for i, (user_id, guesses) in enumerate(sorted_scores, 1):
                    user = await bot.fetch_user(int(user_id))
                    leaderboard += f"{i}. {user.display_name}: {guesses} guesses\n"
                
                await channel.send(leaderboard)
        
        # Reset for the next day
        reset_daily_scores()
    except Exception as e:
        print(f"Error in declare_winner: {e}")

async def check_reminders():
    try:
        now = datetime.datetime.now(pytz.UTC)
        timezones = load_user_timezones()
        channel = bot.get_channel(GLOBLE_CHANNEL_ID)
        
        if not channel:
            return
        
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
                
                # Evening reminder at 9pm local time
                elif user_hour == 21 and user_time.minute < 5:
                    evening_users.append(user_id)
            except Exception as e:
                print(f"Error processing timezone for user {user_id}: {e}")
        
        # Send morning reminders
        if morning_users:
            morning_mentions = " ".join([f"<@{user_id}>" for user_id in morning_users])
            await channel.send(f"Good morning {morning_mentions}! Don't forget to play Globle today: https://globle-game.com/")
        
        # Send evening reminders
        if evening_users:
            evening_mentions = " ".join([f"<@{user_id}>" for user_id in evening_users])
            await channel.send(f"Hey {evening_mentions}! Have you played Globle today? If so, share your score!")
    except Exception as e:
        print(f"Error in check_reminders: {e}")

# Run the bot
if __name__ == '__main__':
    bot.run(TOKEN)
