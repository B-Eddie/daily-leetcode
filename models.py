import json
import os
import datetime
from typing import Dict, List, Optional

DATA_FILE = 'bot_data.json'

class DataManager:
    def __init__(self):
        self.data = {
            'users': {},
            'daily_problems': {},
            'configs': {},
            'user_solves': []
        }
        self.load_data()

    def load_data(self):
        """Load data from JSON file"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                print("Warning: Could not load data file, starting with empty data")
                self.data = {
                    'users': {},
                    'daily_problems': {},
                    'configs': {},
                    'user_solves': []
                }

    def save_data(self):
        """Save data to JSON file"""
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving data: {e}")

    def get_user(self, discord_id: str) -> Optional[Dict]:
        """Get user by Discord ID"""
        return self.data['users'].get(discord_id)

    def save_user(self, discord_id: str, user_data: Dict):
        """Save or update user"""
        self.data['users'][discord_id] = user_data
        self.save_data()

    def get_config(self, guild_id: str) -> Optional[Dict]:
        """Get config by guild ID"""
        return self.data['configs'].get(guild_id)

    def save_config(self, guild_id: str, config_data: Dict):
        """Save or update config"""
        self.data['configs'][guild_id] = config_data
        self.save_data()

    def get_daily_problem(self, date: str) -> Optional[Dict]:
        """Get daily problem by date"""
        return self.data['daily_problems'].get(date)

    def save_daily_problem(self, date: str, problem_data: Dict):
        """Save daily problem"""
        self.data['daily_problems'][date] = problem_data
        self.save_data()

    def get_all_configs(self) -> List[Dict]:
        """Get all configs"""
        return list(self.data['configs'].values())

    def get_top_users_by_streak(self, limit: int = 10) -> List[Dict]:
        """Get top users by streak"""
        users = list(self.data['users'].values())
        users.sort(key=lambda x: x.get('streak', 0), reverse=True)
        return users[:limit]

    def get_today_solvers(self) -> List[Dict]:
        """Get users who have solved today's problem"""
        today = datetime.datetime.now(datetime.UTC).date().isoformat()
        solvers = []
        for user_id, user_data in self.data['users'].items():
            last_solve = user_data.get('last_solve_date')
            if last_solve:
                solve_date = datetime.datetime.fromisoformat(last_solve).date().isoformat()
                if solve_date == today:
                    solvers.append({
                        'user_id': user_id,
                        'username': user_data['leetcode_username'],
                        'streak': user_data['streak']
                    })
        return solvers

    def get_active_streaks(self) -> List[Dict]:
        """Get users with active streaks (solved within last 7 days)"""
        week_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7)
        active_users = []
        for user_id, user_data in self.data['users'].items():
            last_solve = user_data.get('last_solve_date')
            if last_solve:
                solve_date = datetime.datetime.fromisoformat(last_solve)
                if solve_date > week_ago:
                    active_users.append({
                        'user_id': user_id,
                        'username': user_data['leetcode_username'],
                        'streak': user_data['streak'],
                        'last_solve': solve_date
                    })
        return active_users

    def get_yesterday_solvers(self) -> List[str]:
        """Get Discord user IDs of users who solved yesterday's problem"""
        yesterday = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)).date().isoformat()
        yesterday_solvers = []
        for user_id, user_data in self.data['users'].items():
            last_solve = user_data.get('last_solve_date')
            if last_solve:
                solve_date = datetime.datetime.fromisoformat(last_solve).date().isoformat()
                if solve_date == yesterday:
                    yesterday_solvers.append(user_id)
        return yesterday_solvers

# Global data manager instance
data_manager = DataManager()

# User data structure
def create_user(discord_id: str, leetcode_username: str, solved_count: int = 0, streak: int = 0) -> Dict:
    return {
        'discord_id': discord_id,
        'leetcode_username': leetcode_username,
        'solved_count': solved_count,
        'streak': streak,
        'last_solve_date': None
    }

# Config data structure
def create_config(guild_id: str, channel_id: str, post_hour: int = 9, post_minute: int = 0, difficulty: str = "random") -> Dict:
    return {
        'guild_id': guild_id,
        'channel_id': channel_id,
        'post_hour': post_hour,
        'post_minute': post_minute,
        'difficulty': difficulty  # "easy", "medium", "hard", or "random"
    }

# Daily problem data structure
def create_daily_problem(problem_id: str, title: str) -> Dict:
    return {
        'problem_id': problem_id,
        'title': title,
        'date': datetime.datetime.now(datetime.UTC).isoformat()
    }
