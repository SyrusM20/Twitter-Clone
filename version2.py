import pymongo
from pymongo import MongoClient
import pprint
from datetime import datetime
import re

def connect_to_mongodb():
    try:
        port_no = input("Please enter your port number: ")
        print()
        client = MongoClient("mongodb://localhost:" + port_no)
        db = client["Database_name"]
        tweets = db["tweets"]

        # creates the indexes needed for the functions to work
        tweets.create_index([("user.username", "text"), ("content", "text"), ("location", "text")], name='compound_text_index', default_language='english', textIndexVersion=3)

        return tweets
    except pymongo.errors.ConnectionFailure as error:
        print(f"Error connecting to MongoDB: {error}\n")
        return None

def search_tweets(tweets):
    while True:
        user_input = input("Enter keywords to search for tweets, or type 'menu' to return: ")
        print()
        if user_input.lower() == 'menu':
            return

        # Find tweets that match the keyword
        keywords = user_input.split(',')
        keyword_queries = [{"content": {"$regex": f"\\b{re.escape(keyword)}\\b", "$options": "i"}} for keyword in keywords]
        query = {"$and": keyword_queries}
        matched_tweets = list(tweets.find(query))

        for index, result in enumerate(matched_tweets, start=1):
            print(f"Tweet {index}:")
            print(f"  ID: {result.get('id', 'N/A')}")
            print(f"  Date: {result.get('date','N/A')}")
            print(f"  Content: {result.get('content','N/A')}")
            print(f"  Username: {result.get('user', {}).get('username', 'N/A')}\n")

        if not matched_tweets:
            print("No results found.\n")
            continue

        tweet_selection = input("Enter the number of the tweet to see full details, or type 'menu' to return: ")
        print()
        if tweet_selection.lower() == 'menu':
            return

        # Prints the full details of the tweet selected
        try:
            tweet_number = int(tweet_selection)
            if 0 < tweet_number <= len(listed_results):
                selected_tweet = listed_results[tweet_number - 1]
                pprint.pprint(selected_tweet)
            else:
                print("Invalid tweet number entered.\n")
        except ValueError:
            print("Invalid input. Please enter a number.\n")

def search_users(tweets):
    while True:
        user_input = input("Enter a keyword to search for, or type 'menu' to return: ")
        print()
        if user_input.lower() == 'menu':
            return

        # Stops keywords from being matched partially
        pattern = r'\b' + re.escape(user_input) + r'\b'

        # Query that searches for the users in which that their displayname and location fields match the keyword
        query = {
            "$or": [
                {"user.displayname": {"$regex": pattern, "$options": "i"}},
                {"user.location": {"$regex": pattern, "$options": "i"}}
            ]
        }
        results = list(tweets.find(query))

        unique_users = set()
        merged_results = []

        # Merges the users in which their displayname and location fields match the keyword, while removing duplicates
        for result in results:
            user_id = result.get("user", {}).get("id")
            if user_id and user_id not in unique_users:
                unique_users.add(user_id)
                merged_results.append(result)

        for index, result in enumerate(merged_results, start=1):
            print(f"User {index}:")
            user = result.get("user", {})
            print(f"  Username: {user.get('username', 'N/A')}")
            print(f"  Display Name: {user.get('displayname', 'N/A')}")
            print(f"  Location: {user.get('location', 'N/A')}\n")

        if not merged_results:
            print("No results found.\n")
            continue

        user_selection = input("Enter the number of the user to see full details, or type 'menu' to return: ")
        print()
        if user_selection.lower() == 'menu':
            return
        # prints the full details of the user that was selected
        try:
            user_number = int(user_selection)
            if 0 < user_number <= len(merged_results):
                selected_user = merged_results[user_number - 1]
                pprint.pprint(selected_user.get("user", {}))
            else:
                print("Invalid user number entered.\n")
        except ValueError:
            print("Invalid input. Please enter a number.\n")

def list_top_tweets(tweets):
    while True:
        field_input = input("Enter the field to sort by (retweetCount, likeCount, quoteCount), or type 'menu' to return: ")
        print()
        if field_input.lower() == 'menu':
            return

        if field_input not in ['retweetCount', 'likeCount', 'quoteCount']:
            print("Invalid field. Please enter one of 'retweetCount', 'likeCount', 'quoteCount'.\n")
            continue

        try:
            n = int(input("Enter the number of top tweets to list: "))
            print()
        except ValueError:
            print("Invalid number entered.\n")
            continue

        # Finds the top tweets based on the input of the user
        results = tweets.find().sort(field_input, pymongo.DESCENDING).limit(n)
        tweet_list = list(results)

        if not tweet_list:
            print("No tweets found.")
            continue

        for index, tweet in enumerate(tweet_list, start=1):
            print(f"Tweet {index}:")
            print(f"  ID: {tweet['id']}")
            print(f"  Date: {tweet['date']}")
            print(f"  Content: {tweet['content']}")
            print(f"  Username: {tweet['user']['username']}\n")

        tweet_selection = input("Enter the number of the tweet to see full details, or type 'menu' to return: ")
        print()
        if tweet_selection.lower() == 'menu':
            return

        # Prints the full details of the tweet that was selected
        try:
            tweet_number = int(tweet_selection)
            if 0 < tweet_number <= len(tweet_list):
                selected_tweet = tweet_list[tweet_number - 1]
                pprint.pprint(selected_tweet)
            else:
                print("Invalid tweet number entered.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def list_top_users(tweets):
    while True:
        n = input("Enter the number of users you would like to list, or type 'menu' to return: ")
        print()
        if n.lower() == 'menu':
            return
        if not n.isdigit():
            print("Invalid. Please enter a valid number.\n")
            continue
        # Get the the top users based on the number of followers and the input by the user
        results = list(tweets.aggregate([
                {"$group": {"_id": "$user.id", "username": {"$first": "$user.username"}, "displayname": {"$first": "$user.displayname"}, "followersCount": {"$first": "$user.followersCount"}}},
                {"$sort": {"followersCount": -1}},
                {"$limit": int(n)}
            ]))

        if not results:
            print("No users found.")
            continue

        # Gets rid of duplicates
        else:
            no_duplicates = []
            for index, user in enumerate(results, start=1):
                if user not in no_duplicates:
                    no_duplicates.append(user)
                    print(f"{index:4}. Username: {user['username']:20} | Display name: {user['displayname']:45} | Followers Count: {user['followersCount']}")
            print()

        user_selection = input("Enter the number of the user to see full details, or type 'menu' to return: ")
        print()
        if user_selection.lower() == 'menu':
            return

        # Prints the full information of the tweet that is selected
        try:
            user_number = int(user_selection)
            if 0 < user_number <= len(results):
                selected_user = results[user_number - 1]
                pprint.pprint(selected_user)
            else:
                print("Invalid user number entered.\n")
        except ValueError:
            print("Invalid input. Please enter a number.\n")
            
def compose_tweet(tweets):
    content = input("Enter the tweet content: ")
    print()

    # Define a base tweet template
    tweet_template = {
        "content": None, "date": None, "id": None, "replyCount": None, "retweetCount": None,
        "likeCount": None, "quoteCount": None, "conversationId": None, "lang": None,
        "source": None, "sourceUrl": None, "sourceLabel": None, "outlinks": None,
        "tcooutlinks": None, "renderedContent": None,
        "user": {
            "username": None, "displayname": None, "location": None, "followersCount": None,
            "friendsCount": None, "statusesCount": None, "favouritesCount": None,
            "listedCount": None, "mediaCount": None, "protected": None,
            "profileImageUrl": None, "profileBannerUrl": None, "url": None
        }
    }

    # Update necessary fields for the new tweet
    tweet_template["content"] = content
    tweet_template["date"] = datetime.now().strftime("%Y-%m-%d")
    tweet_template["user"]["username"] = "291user"

    result = tweets.insert_one(tweet_template)

    if result.inserted_id:
        print("Tweet successfully composed and inserted into the database.\n")
    else:
        print("Failed to compose and insert the tweet.\n")
        
def main():
    tweets = connect_to_mongodb()

    if tweets is not None:
        end_program = False
        while not end_program:
            user_input = input("Welcome to Fake Twitter 2.0!\n\nOptions:\n1 - Search for tweets\n2 - Search for users\n3 - List top tweets\n4 - List top users\n5 - Compose a tweet\n6 - Exit the program\n\nInput: ")
            print()
            if user_input == "1":
                search_tweets(tweets)
            elif user_input == "2":
                search_users(tweets)
            elif user_input == "3":
                list_top_tweets(tweets)
            elif user_input == "4":
                list_top_users(tweets)
            elif user_input == "5":
                compose_tweet(tweets)
            elif user_input == "6":
                end_program = True
            else:
                print("Invalid option. Please try again.\n")
    else:
        print("Exiting program due to connection error.\n")

if __name__ == "__main__":
    main()