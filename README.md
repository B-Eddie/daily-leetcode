# Daily LeetCode Bot

A Discord bot that posts daily LeetCode challenges and tracks user progress.

## Features

- Posts a daily LeetCode problem at a configurable time each day.
- Choose problem difficulty: Random (LeetCode's daily), Easy, Medium, or Hard.
- Users can link their LeetCode username.
- Automatic solve detection with manual override option.
- **Community Features**: See who solved today's problem and track streaks.
- **Solve Announcements**: Automatic announcements when someone solves a problem.
- **Enhanced Leaderboards**: Top streaks and active solver tracking.
- Tracks solve streaks based on increase in solved problems count.
- Leaderboard for top streaks.
- Status command to check if you've solved today's problem.
- Per-server configuration for channel, posting time, and difficulty.
- Simple JSON-based data storage (no database required).

## Data Storage

The bot uses a simple JSON file (`bot_data.json`) for data storage instead of a database. This makes it:

- Easier to set up (no database installation needed)
- More portable (single file)
- Human-readable (you can edit the JSON directly if needed)
- Lightweight for small to medium communities

## Setup

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Create a Discord bot at https://discord.com/developers/applications
4. Enable "Message Content Intent" and "Server Members Intent" in the bot settings.
5. Get the bot token and invite the bot to your server with appropriate permissions.
6. Update `.env` with your `DISCORD_TOKEN`.
7. Run the bot: `python bot.py`

## Setup Process

1. **Initial Setup**: Use `/setup_channel #your-channel [hour] [minute]` to configure where and when daily problems are posted
2. **User Setup**: Each user links their LeetCode account with `/setup_username username`
3. **Daily Posts**: The bot will automatically post problems at the configured time each day
4. **Manual Posts**: Admins can use `/post_now` to immediately post the daily problem for testing or special occasions

## Commands

- `/setup_channel <channel> [hour] [minute] [difficulty]`: Set the channel, time, and difficulty for daily posts (admin only). Time defaults to 9:00 AM, difficulty defaults to random.
- `/setup_username <username>`: Link your LeetCode username.
- `/status`: Check if you've solved today's problem.
- `/mark_solved`: Manually mark today's problem as solved (if automatic detection fails).
- `/today_solvers`: Show who has solved today's problem and their streaks.
- `/leaderboard`: View the top streaks and active solvers.
- `/view_config`: View the current daily post configuration.
- `/post_now`: Post the daily LeetCode problem immediately (admin only).
- `/sync_commands`: Manually sync slash commands (admin only, use if commands don't appear).

## Difficulty Options

- **Random**: Uses LeetCode's official daily challenge (default)
- **Easy**: Posts only easy difficulty problems 🟢
- **Medium**: Posts only medium difficulty problems 🟡
- **Hard**: Posts only hard difficulty problems 🔴

## Setup Process

1. **Initial Setup**: Use `/setup_channel #your-channel [hour] [minute] [difficulty]` to configure where, when, and what difficulty problems are posted
2. **User Setup**: Each user links their LeetCode account with `/setup_username username`
3. **Daily Posts**: The bot will automatically post problems at the configured time each day
4. **Manual Posts**: Admins can use `/post_now` to immediately post a problem for testing or special occasions

## Time Configuration

- **Hour**: 0-23 (24-hour format)
- **Minute**: 0-59
- **Examples**:
  - `/setup_channel #leetcode 9 0` - 9:00 AM (default)
  - `/setup_channel #leetcode 14 30` - 2:30 PM
  - `/setup_channel #leetcode 18 0` - 6:00 PM

## Difficulty Examples

- `/setup_channel #leetcode 9 0 easy` - Easy problems at 9:00 AM
- `/setup_channel #leetcode 14 30 medium` - Medium problems at 2:30 PM
- `/setup_channel #leetcode 18 0 hard` - Hard problems at 6:00 PM
- `/setup_channel #leetcode 9 0 random` - LeetCode's daily challenge at 9:00 AM

## Community Features

### Today's Solvers

- Use `/today_solvers` to see who has solved today's problem
- Shows usernames and current streaks
- Encourages friendly competition

### Enhanced Leaderboard

- `/leaderboard` shows both top streaks and active solvers
- **Top Streaks**: All-time highest streaks with medals 🥇🥈🥉
- **Active Solvers**: Users who solved problems in the last 7 days
- Motivates continued participation

### Solve Announcements

- Automatic announcements when someone solves a problem
- Shows the solver's name, problem title, and updated streak
- Builds community engagement and celebration

### Streak Tracking

- Individual user streaks maintained automatically
- Visual indicators and celebration messages
- Encourages daily problem-solving habits

## Command Syncing

The bot automatically syncs slash commands when it starts up. If you don't see the commands in Discord after adding the bot:

1. Make sure the bot has been invited with the `applications.commands` scope
2. Wait a few minutes for Discord to update
3. Use `/sync_commands` as an admin to manually sync if needed
4. Restart the bot if issues persist

The bot will log the number of synced commands when it starts up.

## Requirements

- Python 3.8+
- Discord.py
- APScheduler
- Requests
- Python-dotenv
