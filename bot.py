import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from models import data_manager, create_user, create_config, create_daily_problem
from leetcode import get_daily_problem, get_user_solved_count
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

scheduler = AsyncIOScheduler()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Sync commands globally
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} commands globally')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    
    # Set up daily schedulers for each configured guild
    configs = data_manager.get_all_configs()
    
    for config in configs:
        # Use Eastern Time (EST/EDT) for scheduling
        trigger = CronTrigger(hour=config['post_hour'], minute=config['post_minute'], timezone='US/Eastern')
        scheduler.add_job(
            post_daily_problem_for_guild,
            trigger,
            args=[config['guild_id'], config['channel_id']],
            id=f'daily_{config["guild_id"]}'
        )
        print(f'Scheduled daily posts for guild {config["guild_id"]} at {config["post_hour"]:02d}:{config["post_minute"]:02d} EST/EDT')
    
    # Print current jobs for debugging
    jobs = scheduler.get_jobs()
    print(f'Total scheduled jobs: {len(jobs)}')
    for job in jobs:
        try:
            next_run = job.next_run_time if hasattr(job, 'next_run_time') else 'Unknown'
            print(f'Job: {job.id} - Next run: {next_run}')
        except AttributeError:
            print(f'Job: {job.id} - Next run: Unable to determine')
    
    scheduler.start()
    print('Daily problem scheduler started')

async def post_daily_problem_for_guild(guild_id: str, channel_id: str):
    config = data_manager.get_config(guild_id)
    if not config:
        print(f"No config found for guild {guild_id}")
        return
        
    difficulty = config.get('difficulty', 'random')
    problem = get_daily_problem(difficulty)
    if problem:
        # Check if already posted today
        today = datetime.datetime.now(datetime.UTC).date().isoformat()
        existing = data_manager.get_daily_problem(today)
        if not existing:
            daily_prob = create_daily_problem(problem['id'], problem['title'])
            data_manager.save_daily_problem(today, daily_prob)
            
            # Post to the specific guild's channel
            channel = bot.get_channel(int(channel_id))
            if channel:
                difficulty_emoji = {
                    "easy": "🟢",
                    "medium": "🟡", 
                    "hard": "🔴",
                    "random": "🎲"
                }.get(difficulty, "🎲")
                
                embed = discord.Embed(
                    title=f"Daily LeetCode Challenge {difficulty_emoji}",
                    description=f"**{problem['title']}**\nSolve it here: https://leetcode.com/problems/{problem['slug']}/"
                )
                await channel.send(embed=embed)
                print(f'Posted {difficulty} problem to guild {guild_id}')
        else:
            print(f'Problem already posted today for guild {guild_id}')
    else:
        print(f'Failed to fetch {difficulty} problem for guild {guild_id}')

@bot.tree.command(name="setup_channel", description="Set the channel, time, and difficulty for daily LeetCode posts")
@app_commands.describe(
    channel="The channel to post daily problems",
    hour="Hour of the day (0-23, default: 9)",
    minute="Minute of the hour (0-59, default: 0)",
    difficulty="Problem difficulty: random, easy, medium, or hard (default: random)"
)
@app_commands.choices(difficulty=[
    app_commands.Choice(name="Random (LeetCode's daily)", value="random"),
    app_commands.Choice(name="Easy", value="easy"),
    app_commands.Choice(name="Medium", value="medium"),
    app_commands.Choice(name="Hard", value="hard")
])
async def setup_channel(interaction: discord.Interaction, channel: discord.TextChannel, hour: int = 9, minute: int = 0, difficulty: str = "random"):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need administrator permissions to set the channel.", ephemeral=True)
        return
    
    # Validate time parameters
    if not (0 <= hour <= 23):
        await interaction.response.send_message("Hour must be between 0 and 23.", ephemeral=True)
        return
    if not (0 <= minute <= 59):
        await interaction.response.send_message("Minute must be between 0 and 59.", ephemeral=True)
        return
    
    # Validate difficulty
    valid_difficulties = ["random", "easy", "medium", "hard"]
    if difficulty not in valid_difficulties:
        await interaction.response.send_message("Difficulty must be: random, easy, medium, or hard.", ephemeral=True)
        return
    
    config = data_manager.get_config(str(interaction.guild.id))
    if config:
        config['channel_id'] = str(channel.id)
        config['post_hour'] = hour
        config['post_minute'] = minute
        config['difficulty'] = difficulty
        data_manager.save_config(str(interaction.guild.id), config)
    else:
        config = create_config(str(interaction.guild.id), str(channel.id), hour, minute, difficulty)
        data_manager.save_config(str(interaction.guild.id), config)
    
    difficulty_display = difficulty.title() if difficulty != "random" else "Random (LeetCode's daily)"
    await interaction.response.send_message(
        f"Daily LeetCode channel set to {channel.mention}\n"
        f"Daily posts scheduled for {hour:02d}:{minute:02d}\n"
        f"Problem difficulty: {difficulty_display}",
        ephemeral=True
    )

@bot.tree.command(name="setup_username", description="Link your LeetCode username")
@app_commands.describe(username="Your LeetCode username")
async def setup_username(interaction: discord.Interaction, username: str):
    user = data_manager.get_user(str(interaction.user.id))
    current_count = get_user_solved_count(username)
    if user:
        user['leetcode_username'] = username
        user['solved_count'] = current_count
        data_manager.save_user(str(interaction.user.id), user)
    else:
        user = create_user(str(interaction.user.id), username, current_count)
        data_manager.save_user(str(interaction.user.id), user)
    await interaction.response.send_message(f"Linked your LeetCode username: {username}", ephemeral=True)

@bot.tree.command(name="status", description="Check if you've solved today's problem")
async def status(interaction: discord.Interaction):
    user = data_manager.get_user(str(interaction.user.id))
    if not user:
        await interaction.response.send_message("Please set up your LeetCode username with /setup_username", ephemeral=True)
        return
    
    # Get today's problem
    today = datetime.datetime.now(datetime.UTC).date().isoformat()
    problem = data_manager.get_daily_problem(today)
    if not problem:
        await interaction.response.send_message("No daily problem posted yet.", ephemeral=True)
        return
    
    # Check if user has already marked today's problem as solved
    last_solve_date = user.get('last_solve_date')
    if last_solve_date:
        last_solve = datetime.datetime.fromisoformat(last_solve_date).date()
        today_date = datetime.datetime.now(datetime.UTC).date()
        if last_solve == today_date:
            await interaction.response.send_message(f"You've already solved today's problem! Streak: {user['streak']}", ephemeral=True)
            return
    
    # Try to detect solve automatically
    current_count = get_user_solved_count(user['leetcode_username'])
    if current_count > user['solved_count']:
        # Update user's solved count and streak
        user['solved_count'] = current_count
        user['streak'] += 1
        user['last_solve_date'] = datetime.datetime.now(datetime.UTC).isoformat()
        data_manager.save_user(str(interaction.user.id), user)
        
        # Announce the solve if there's a configured channel
        config = data_manager.get_config(str(interaction.guild.id))
        if config:
            channel = bot.get_channel(int(config['channel_id']))
            if channel:
                embed = discord.Embed(
                    title="🎉 Problem Solved!",
                    description=f"**{interaction.user.mention}** solved today's problem!\n**{problem['title']}**\n\nStreak: {user['streak']} 🔥",
                    color=0x00ff00
                )
                await channel.send(embed=embed)
        
        await interaction.response.send_message(f"You've solved today's problem! Streak: {user['streak']}", ephemeral=True)
    else:
        # Show current status with option to mark as solved
        embed = discord.Embed(title="Daily Problem Status", color=0xffa500)
        embed.add_field(name="Problem", value=problem['title'], inline=False)
        embed.add_field(name="Your Streak", value=str(user['streak']), inline=True)
        embed.add_field(name="Status", value="Not solved yet", inline=True)
        embed.set_footer(text="Use /mark_solved if you've solved it but it's not detected automatically")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="mark_solved", description="Manually mark today's problem as solved")
async def mark_solved(interaction: discord.Interaction):
    user = data_manager.get_user(str(interaction.user.id))
    if not user:
        await interaction.response.send_message("Please set up your LeetCode username with /setup_username", ephemeral=True)
        return
    
    # Get today's problem
    today = datetime.datetime.now(datetime.UTC).date().isoformat()
    problem = data_manager.get_daily_problem(today)
    if not problem:
        await interaction.response.send_message("No daily problem posted yet.", ephemeral=True)
        return
    
    # Check if already marked as solved today
    last_solve_date = user.get('last_solve_date')
    if last_solve_date:
        last_solve = datetime.datetime.fromisoformat(last_solve_date).date()
        today_date = datetime.datetime.now(datetime.UTC).date()
        if last_solve == today_date:
            await interaction.response.send_message(f"You've already marked today's problem as solved! Streak: {user['streak']}", ephemeral=True)
            return
    
    # Mark as solved and update streak
    user['streak'] += 1
    user['last_solve_date'] = datetime.datetime.now(datetime.UTC).isoformat()
    data_manager.save_user(str(interaction.user.id), user)
    
    # Announce the solve if there's a configured channel
    config = data_manager.get_config(str(interaction.guild.id))
    if config:
        channel = bot.get_channel(int(config['channel_id']))
        if channel:
            today = datetime.datetime.now(datetime.UTC).date().isoformat()
            problem = data_manager.get_daily_problem(today)
            if problem:
                embed = discord.Embed(
                    title="🎉 Problem Solved!",
                    description=f"**{interaction.user.mention}** solved today's problem!\n**{problem['title']}**\n\nStreak: {user['streak']} 🔥",
                    color=0x00ff00
                )
                await channel.send(embed=embed)
    
    await interaction.response.send_message(f"Marked today's problem as solved! Streak: {user['streak']}", ephemeral=True)

@bot.tree.command(name="view_config", description="View the current daily post configuration")
async def view_config(interaction: discord.Interaction):
    config = data_manager.get_config(str(interaction.guild.id))
    
    if not config:
        await interaction.response.send_message("No configuration found. Use `/setup_channel` to set up daily posts.", ephemeral=True)
        return
    
    channel = bot.get_channel(int(config['channel_id']))
    channel_mention = channel.mention if channel else f"Channel ID: {config['channel_id']}"
    
    difficulty_display = config.get('difficulty', 'random').title()
    if difficulty_display == "Random":
        difficulty_display = "Random (LeetCode's daily)"
    
    embed = discord.Embed(title="Daily LeetCode Configuration", color=0x00ff00)
    embed.add_field(name="Channel", value=channel_mention, inline=True)
    embed.add_field(name="Time", value=f"{config['post_hour']:02d}:{config['post_minute']:02d} EST/EDT", inline=True)
    embed.add_field(name="Difficulty", value=difficulty_display, inline=True)
    embed.add_field(name="Next Post", value="Today at the scheduled time (if not already posted)", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="post_now", description="Post the daily LeetCode problem immediately (admin only)")
async def post_now(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need administrator permissions to post immediately.", ephemeral=True)
        return
    
    config = data_manager.get_config(str(interaction.guild.id))
    if not config:
        await interaction.response.send_message("No configuration found. Use `/setup_channel` first.", ephemeral=True)
        return
    
    # Get the daily problem with configured difficulty
    difficulty = config.get('difficulty', 'random')
    problem = get_daily_problem(difficulty)
    if not problem:
        await interaction.response.send_message("Failed to fetch daily problem. Try again later.", ephemeral=True)
        return
    
    # Check if already posted today
    today = datetime.datetime.now(datetime.UTC).date().isoformat()
    existing = data_manager.get_daily_problem(today)
    if existing:
        await interaction.response.send_message("Today's problem has already been posted.", ephemeral=True)
        return
    
    # Save the problem
    daily_prob = create_daily_problem(problem['id'], problem['title'])
    data_manager.save_daily_problem(today, daily_prob)
    
    # Post to the configured channel
    channel = bot.get_channel(int(config['channel_id']))
    if channel:
        difficulty_emoji = {
            "easy": "🟢",
            "medium": "🟡", 
            "hard": "🔴",
            "random": "🎲"
        }.get(difficulty, "🎲")
        
        embed = discord.Embed(
            title=f"Daily LeetCode Challenge {difficulty_emoji}",
            description=f"**{problem['title']}**\nSolve it here: https://leetcode.com/problems/{problem['slug']}/"
        )
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Posted {difficulty} problem to {channel.mention}!", ephemeral=True)
    else:
        await interaction.response.send_message("Could not find the configured channel.", ephemeral=True)

@bot.tree.command(name="today_solvers", description="Show who has solved today's problem")
async def today_solvers(interaction: discord.Interaction):
    today = datetime.datetime.now(datetime.UTC).date().isoformat()
    problem = data_manager.get_daily_problem(today)
    
    embed = discord.Embed(title="Today's Problem Solvers 🧩", color=0x00ff00)
    
    if problem:
        embed.add_field(name="Today's Problem", value=problem['title'], inline=False)
    
    solvers = data_manager.get_today_solvers()
    
    if solvers:
        solver_list = []
        for solver in solvers:
            solver_list.append(f"🏆 {solver['username']} (Streak: {solver['streak']})")
        
        embed.add_field(name=f"Solvers ({len(solvers)})", value="\n".join(solver_list), inline=False)
    else:
        embed.add_field(name="Solvers", value="No one has solved today's problem yet! 🧩", inline=False)
    
    # Add some stats
    total_users = len(data_manager.data['users'])
    embed.set_footer(text=f"Total registered users: {total_users}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="View the top streaks and active solvers")
async def leaderboard(interaction: discord.Interaction):
    embed = discord.Embed(title="🏆 LeetCode Leaderboard", color=0xffd700)
    
    # Top streaks
    top_users = data_manager.get_top_users_by_streak(5)
    if top_users:
        streak_list = []
        for i, user in enumerate(top_users, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else "🏅"
            streak_list.append(f"{medal} {user['leetcode_username']}: {user['streak']}")
        
        embed.add_field(name="🔥 Top Streaks", value="\n".join(streak_list), inline=False)
    
    # Active solvers (solved in last 7 days)
    active_users = data_manager.get_active_streaks()
    if active_users:
        # Sort by most recent solve
        active_users.sort(key=lambda x: x['last_solve'], reverse=True)
        active_list = []
        for user in active_users[:5]:  # Show top 5 most recent
            days_ago = (datetime.datetime.now(datetime.UTC) - user['last_solve']).days
            time_str = "today" if days_ago == 0 else f"{days_ago} days ago"
            active_list.append(f"⚡ {user['username']}: {user['streak']} ({time_str})")
        
        embed.add_field(name="⚡ Active Solvers", value="\n".join(active_list), inline=False)
    
    if not top_users and not active_users:
        embed.add_field(name="No Data", value="No users have solved problems yet!", inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="test_post", description="Test the daily posting (admin only)")
async def test_post(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need administrator permissions to test posting.", ephemeral=True)
        return
    
    config = data_manager.get_config(str(interaction.guild.id))
    if not config:
        await interaction.response.send_message("No configuration found. Use `/setup_channel` first.", ephemeral=True)
        return
    
    # Get the daily problem with configured difficulty
    difficulty = config.get('difficulty', 'random')
    problem = get_daily_problem(difficulty)
    if not problem:
        await interaction.response.send_message("Failed to fetch daily problem. Try again later.", ephemeral=True)
        return
    
    # Post to the configured channel
    channel = bot.get_channel(int(config['channel_id']))
    if channel:
        difficulty_emoji = {
            "easy": "🟢",
            "medium": "🟡", 
            "hard": "🔴",
            "random": "🎲"
        }.get(difficulty, "🎲")
        
        embed = discord.Embed(
            title=f"Daily LeetCode Challenge {difficulty_emoji} (TEST)",
            description=f"**{problem['title']}**\nSolve it here: https://leetcode.com/problems/{problem['slug']}/",
            color=0xffa500
        )
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Test post sent to {channel.mention}!", ephemeral=True)
    else:
        await interaction.response.send_message("Could not find the configured channel.", ephemeral=True)

bot.run(TOKEN)
