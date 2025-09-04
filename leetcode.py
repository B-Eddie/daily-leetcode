import requests
import json

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

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
        response = requests.post(LEETCODE_GRAPHQL_URL, json={'query': query})
        if response.status_code == 200:
            data = response.json()
            question = data['data']['activeDailyCodingChallengeQuestion']['question']
            return {
                'id': question['questionId'],
                'title': question['title'],
                'slug': question['titleSlug']
            }
    else:
        # Get a random problem of specified difficulty
        return get_random_problem_by_difficulty(difficulty)
    
    return None

def get_random_problem_by_difficulty(difficulty: str):
    """Get a random problem of specified difficulty"""
    difficulty_map = {
        "easy": "EASY",
        "medium": "MEDIUM", 
        "hard": "HARD"
    }
    
    if difficulty not in difficulty_map:
        return None
        
    # Query for problems with the specified difficulty
    query = f"""
    query {{
      problemsetQuestionList(
        categorySlug: ""
        limit: 100
        skip: 0
        filters: {{
          difficulty: {difficulty_map[difficulty]}
        }}
      ) {{
        questions {{
          title
          titleSlug
          questionId
          difficulty
        }}
      }}
    }}
    """
    
    response = requests.post(LEETCODE_GRAPHQL_URL, json={'query': query})
    if response.status_code == 200:
        data = response.json()
        questions = data['data']['problemsetQuestionList']['questions']
        if questions:
            # Pick a random question
            import random
            question = random.choice(questions)
            return {
                'id': question['questionId'],
                'title': question['title'],
                'slug': question['titleSlug']
            }
    
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
    response = requests.post(LEETCODE_GRAPHQL_URL, json={'query': query})
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and data['data']['matchedUser']:
            return data['data']['matchedUser']['submitStats']['acSubmissionNum']
    return None

def get_user_solved_count(username):
    stats = get_user_stats(username)
    if stats:
        total = 0
        for item in stats:
            total += item['count']
        return total
    return 0
