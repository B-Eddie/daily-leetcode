import requests
import json
import random

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
LEETCODE_API_URL = "https://leetcode.com/api/problems/all/"

def get_daily_problem(difficulty: str = "random"):
    """Get a daily problem, optionally filtered by difficulty"""
    if difficulty == "random":
        # Use the standard daily challenge
        query = """
        query {
          activeDailyCodingChallengeQuestion {
            date
            question {
              title
              titleSlug
              questionId
            }
          }
        }
        """
        try:
            response = requests.post(LEETCODE_GRAPHQL_URL, json={'query': query}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['activeDailyCodingChallengeQuestion']:
                    question = data['data']['activeDailyCodingChallengeQuestion']['question']
                    return {
                        'id': question['questionId'],
                        'title': question['title'],
                        'slug': question['titleSlug']
                    }
                else:
                    print(f"No daily challenge data in response: {data}")
            else:
                print(f"Error fetching daily challenge: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception fetching daily challenge: {e}")
    else:
        # Get a random problem of specified difficulty
        return get_random_problem_by_difficulty(difficulty)
    
    return None

def get_random_problem_by_difficulty(difficulty: str):
    """Get a random problem of specified difficulty using the /api/problems/all/ endpoint"""
    difficulty_map = {
        "easy": 1,
        "medium": 2, 
        "hard": 3
    }
    
    if difficulty not in difficulty_map:
        print(f"Invalid difficulty: {difficulty}")
        return None
        
    try:
        response = requests.get(LEETCODE_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'stat_status_pairs' in data:
                # Filter problems by difficulty
                target_level = difficulty_map[difficulty]
                filtered_problems = [
                    p for p in data['stat_status_pairs'] 
                    if p['difficulty']['level'] == target_level and not p['paid_only']
                ]
                
                if filtered_problems:
                    # Pick a random question
                    problem = random.choice(filtered_problems)
                    stat = problem['stat']
                    return {
                        'id': str(stat['question_id']),
                        'title': stat['question__title'],
                        'slug': stat['question__title_slug']
                    }
                else:
                    print(f"No {difficulty} problems found")
            else:
                print(f"Unexpected API response structure: {list(data.keys())}")
        else:
            print(f"Error fetching {difficulty} problems: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception fetching {difficulty} problems: {e}")
    
    return None

def check_user_solved(username, problem_slug):
    # This is a placeholder. In reality, checking if a user solved a specific problem requires more complex API calls or scraping.
    # For now, return False. To implement properly, we might need to use unofficial APIs or web scraping.
    # One way is to use the user's submission history, but it's not straightforward.
    # For demonstration, we'll assume we have a way.
    # Actually, LeetCode doesn't provide a direct API for this without authentication.
    # We might need to use selenium or something, but that's overkill.
    # Perhaps use the leetcode-api library if available.
    return False  # Placeholder

# To properly check, we can use:
# But for now, placeholder.

def get_user_stats(username):
    query = f"""
    query {{
      matchedUser(username: "{username}") {{
        submitStats: submitStatsGlobal {{
          acSubmissionNum {{
            difficulty
            count
            submissions
          }}
        }}
      }}
    }}
    """
    try:
        response = requests.post(LEETCODE_GRAPHQL_URL, json={'query': query}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['matchedUser']:
                return data['data']['matchedUser']['submitStats']['acSubmissionNum']
            else:
                print(f"No user data found for username: {username}")
        else:
            print(f"Error fetching user stats: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception fetching user stats: {e}")
    return None

def get_user_solved_count(username):
    stats = get_user_stats(username)
    if stats:
        total = 0
        for item in stats:
            total += item['count']
        return total
    return 0
