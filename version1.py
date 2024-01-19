

import sqlite3
import argparse
import re
import getpass
from datetime import datetime

# Primary functions

def connect(path):
    global conn, c

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(' PRAGMA foreign_keys=ON; ')
    conn.commit()
    return

def login_screen():
    global conn, c
    
    user_input = input("Welcome to Fake Twitter!\n\nOptions:\n1 - Login\n2 - Register\n3 - Exit\n\nInput: ")
    print()
    while user_input not in ["1", "2", "3"]:
        user_input = input("Invalid. Please select from one of the following options:\n1 - Login\n2 - Register\n3 - Exit\n\nInput: ")
        print()
    
    if user_input == "1":
        user_id = input("User ID: ")
        while not user_id.isnumeric():
            user_id = input("Invalid. User ID must be a number: ")
        password = getpass.getpass("Password: ")

        c.execute("SELECT * FROM users WHERE usr = ?;", (int(user_id),))
        fetched_row = c.fetchone()

        if (fetched_row is not None) and (fetched_row["pwd"] == password):
            print("\nLogin successful!\n")
            main_page(user_id)
        else:
            print("\nLogin failed! Please check your user ID and password.\n")
    elif user_input == "2":
        register()
    elif user_input == "3":
        print("Thanks for using Fake Twitter!")
        return True
    conn.commit()

def register():
    global conn, c
    
    signup_successful = False
    print("Please fill out the following details to complete your registration.")
    user_name = input("Name: ")
    user_email = input("Email: ")
    user_city = input("City: ")
    user_timezone = input("Timezone: ")
    user_password = getpass.getpass("Password: ")
    user_confirmation = input("Confirm registration? (Y/N) ")

    if user_confirmation.upper() == "Y":
        c.execute("""
            INSERT INTO users (usr, pwd, name, email, city, timezone)
            VALUES ((SELECT MAX(u1.usr) + 1 FROM users u1), ?, ?, ?, ?, ?)
        """, (user_password, user_name, user_email, user_city, user_timezone))

        user_id = c.lastrowid

        if user_id is not None:
            signup_successful = True

        if signup_successful:
            print(f"\nRegistration successful! Your User ID is {user_id}. Don't forget!\n")
            conn.commit()
            main_page(user_id)
        else:
            print("\nRegistration failed!\n")
            conn.rollback()
    else:
        print("\nRegistration cancelled!\n")
    conn.commit()

def main_page(user_id):
    global conn, c
    
    placeholder1 = 0
    while True:
        c.execute("""
        SELECT tid, writer, tdate as date, text, 'Writer:' AS source
        FROM tweets
        WHERE writer IN (
            SELECT flwee
            FROM follows
            WHERE flwer = ?
        )
        UNION
        SELECT r.tid, r.usr, t.tdate, t.text, 'Retweeter:' AS source
        FROM retweets r
        JOIN tweets t ON r.tid = t.tid
        WHERE r.usr IN (
            SELECT flwee
            FROM follows
            WHERE flwer = ?
        )
        ORDER BY date;
        """,(user_id, user_id))
        rows = c.fetchall()
        length = len(rows)

        if length != 0 and placeholder1 == 0:
            for index in range(placeholder1, min(placeholder1 + 5, length)):
                fetched_row = rows[index]
                print(f"Tweet ID: {fetched_row['tid']:4} | {fetched_row['source']:10} {fetched_row['writer']:4} | Date: {fetched_row['date']} | \"{fetched_row['text']}\"")
            print()
            placeholder1 += 5    
            
        user_input = input("Options:\n1 - Load more tweets\n2 - Select a tweet\n3 - Search for tweets\n4 - Search for users\n5 - Compose a tweet\n6 - List followers\n7 - Logout\n\nInput: ")
        print()
        while user_input not in ["1", "2", "3", "4", "5", "6", "7"]:
            user_input = input("Invalid. Please select from one of the following options:\n1 - Select a tweet\n2 - Load more tweets\n3 - Search for tweets\n4 - Search for users\n5 - Compose a tweet\n6 - List followers\n7 - Logout\n\nInput: ")
            print()
                
        if user_input == "1":
            if placeholder1 < length:
                for index in range(placeholder1, min(placeholder1 + 5, length)):
                    fetched_row = rows[index]
                    print(f"Tweet ID: {fetched_row['tid']:4} | {fetched_row['source']:10} {fetched_row['writer']:4} | Date: {fetched_row['date']} | \"{fetched_row['text']}\"")
                print()
                placeholder1 += 5
            else:
                print("No more tweets available to display.\n")

        elif user_input == "2":
            select_tweet(user_id, rows)
            placeholder1 = 0
        elif user_input == "3":
            input_keywords = input("Enter keywords to search for tweets (separated by commas): ")
            keywords = [keyword.strip() for keyword in input_keywords.split(',') if keyword.strip()]
            if not keywords:
                print("No keywords provided. Please try again.")
            else:
                search_tweets(user_id, keywords)
            placeholder1 = 0
        elif user_input == "4":
            search_users(user_id)
            placeholder1 = 0
        elif user_input == "5":
            compose_tweet(user_id,False)
            placeholder1 = 0
        elif user_input == "6":
            list_followers(user_id)
            placeholder1 = 0
        elif user_input == "7":
            return True
    conn.commit()

def select_tweet(user_id, rows):
    global conn, c
    
    selected_tweet = input("Select a displayed tweet ID to see more information: ")
    print()
    while not any(int(selected_tweet) == row['tid'] for row in rows):
        selected_tweet = input("Invalid. No tweet IDs that match. Please enter a valid option: ")
        print()
    
    tweet_id = int(selected_tweet)
    tweet_info = tweet_statistics(tweet_id)

    print(f"Tweet ID: {tweet_info['tid']} | Writer: {tweet_info['writer']} | Date: {tweet_info['date']} | \"{tweet_info['text']}\"")
    print(f"Number of replies: {tweet_info['reply_count']} | Number of retweets: {tweet_info['retweet_count']}\n")

    user_input = input("Options:\n1 - Reply to tweet\n2 - Retweet the tweet\n3 - Go back\n\nInput: ")
    print()
    while user_input not in ["1", "2", "3"]:
        user_input = input("Invalid. Please select from one of the following options:\n1 - Reply to tweet\n2 - Retweet the tweet\n3 - Go back\n\nInput: ")
        print()
        
    if user_input == "1":
        compose_tweet(user_id, True, tweet_info['tid'])
    elif user_input == "2":
        retweet_tweet(user_id,tweet_id)
    conn.commit()

def search_tweets(user_id, keywords):
    global conn, c

    # Prepare the SQL query part for text search
    text_conditions = " OR ".join(f"tweets.text LIKE ?" for keyword in keywords if not keyword.startswith("#"))
    text_terms = [f"%{keyword}%" for keyword in keywords if not keyword.startswith("#")]

    # Prepare the SQL query part for hashtag search
    hashtag_conditions = " OR ".join(f"LOWER(hashtags.term) = LOWER(?)" for keyword in keywords if keyword.startswith("#"))
    hashtag_terms = [keyword[1:] for keyword in keywords if keyword.startswith("#")]

    # Combine the conditions, ensuring we have at least one condition
    conditions = []
    params = []
    if text_conditions:
        conditions.append(f"({text_conditions})")
        params.extend(text_terms)
    if hashtag_conditions:
        conditions.append(f"mentions.term IN (SELECT term FROM hashtags WHERE {hashtag_conditions})")
        params.extend(hashtag_terms)

    # Final query
    query = f"""
    SELECT DISTINCT tweets.tid, tweets.writer, tweets.tdate, tweets.text
    FROM tweets
    LEFT JOIN mentions ON tweets.tid = mentions.tid
    LEFT JOIN hashtags ON mentions.term = hashtags.term
    WHERE {' OR '.join(conditions)}
    ORDER BY tweets.tdate DESC
    """

    offset = 0
    tweet_counter = 1  # Start the counter at 1
    tweet_index_to_id_map = {}  # Dictionary to map display index to tweet ID

    try:
        while True:
            # Execute the query with the current offset
            params_with_offset = params + [offset]  # Ensure params is a list of supported types
            c.execute(query + " LIMIT 5 OFFSET ?", params_with_offset)
            tweets = c.fetchall()
            if not tweets and offset == 0:
                print("No tweets found matching your keywords.\n")
                break
            elif not tweets:
                print("No more tweets available to display.\n")
            else:
                # Process and print tweets with continuous numbering
                for index, tweet in enumerate(tweets, start=tweet_counter):
                    tweet_index_to_id_map[index] = tweet['tid']
                    print(f"{index}. Tweet ID: {tweet['tid']} | Writer: {tweet['writer']} | Date: {tweet['tdate']} | \"{tweet['text']}\"")
                tweet_counter += len(tweets)  # Update the counter to the next starting index
                print()

            tweet_selection = input("Select a tweet by number to see more options, type 'more' to view more tweets, or 'back' to return to the main menu: ")
            print()

            if tweet_selection.isdigit():
                selected_index = int(tweet_selection)
                if selected_index in tweet_index_to_id_map:
                    selected_tweet_id = tweet_index_to_id_map[selected_index]
                    tweet_info = tweet_statistics(selected_tweet_id)
                    print(f"Number of replies: {tweet_info['reply_count']} | Number of retweets: {tweet_info['retweet_count']}\n")
                    handle_tweet_actions(user_id, selected_tweet_id)
                else:
                    print("Invalid selection. Please try again.")
            elif tweet_selection.lower() == 'more':
                if not tweets:
                    print("You have reached the end of the results.\n")
                else:
                    offset += 5
            elif tweet_selection.lower() == 'back':
                break  # Exit the loop to return to the main menu
            else:
                print("Invalid input. Please try again.\n")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.commit()

def search_users(user_id):
    global conn, c
    
    target_user = input("Enter the keyword you want to search for: ").lower().capitalize()
    print()
    
    matched_usrs = []

    # First SELECT statement for those whose names match the target
    c.execute("""
        SELECT u1.usr, u1.name, u1.city
        FROM users u1
        WHERE LOWER(u1.name) LIKE ?
        ORDER BY LENGTH(u1.name)
    """, ('%' + target_user + '%',))

    # Adds the users whose names match the target, to the list
    rows = c.fetchall()
    for row in rows:
        matched_usrs.append(row)

    # Second SELECT statement for those whose city matches the target
    c.execute("""
        SELECT u1.usr, u1.name, u1.city
        FROM users u1
        WHERE LOWER(u1.city) LIKE ? AND u1.usr NOT IN (
            SELECT u2.usr
            FROM users u2
            WHERE LOWER(u2.name) LIKE ?
        )
        ORDER BY LENGTH(u1.city)
    """, ('%' + target_user + '%', '%' + target_user + '%',))

    # Adds the users whose city match the target, to the list
    rows = c.fetchall()
    for row in rows:
        matched_usrs.append(row)

    length2 = len(matched_usrs)
    placeholder2 = 0

    if length2 == 0:
        print("No users that match the keyword.\n")
        return
    else:
        for index in range(placeholder2, min(placeholder2 + 5, length2)):
            print(f"User ID: {matched_usrs[index]['usr']:4} | {matched_usrs[index]['name']} from {matched_usrs[index]['city']}")
        print()
        placeholder2 += 5

        display_again = False
        while True:
            # displays the 5 users again if the user comes back to menu, after they had selected a user
            if display_again == True:
                for index in range(placeholder2, min(placeholder2 + 5, length2)):
                    print(f"User ID: {matched_usrs[index]['usr']:4} | {matched_usrs[index]['name']} from {matched_usrs[index]['city']}")
                print()
                placeholder2 += 5
                display_again = False

            user_input = input("Options:\n1 - Show more\n2 - Select user\n3 - Go back\n\nInput: ")
            print()
            while user_input not in ["1", "2", "3"]:
                user_input = input("Invalid. Please select from one of the following options:\n1 - Show more\n2 - Select user\n3 - Go back\n\nInput: ")
                print()

            if user_input == "1":
                if placeholder2 < length2:
                    for index in range(placeholder2, min(placeholder2 + 5, length2)):
                        print(f"User ID: {matched_usrs[index]['usr']:4} | {matched_usrs[index]['name']} from {matched_usrs[index]['city']}")
                    print()
                    placeholder2 += 5
                else:
                    print("No more users available to display.\n")

            elif user_input == "2":
                user_input = input("Select a displayed user ID to show more information: ")
                print()
                while not any(int(user_input) == user_dict['usr'] for user_dict in matched_usrs):
                    user_input = input("Invalid. No users that match the keyword. Please enter a valid option: ")
                    print()

                # Gets basic info from the user
                c.execute("""
                    SELECT *
                    FROM users u1
                    WHERE u1.usr = ?
                """, (user_input,))
                row = c.fetchone()

                c.execute("""SELECT 
                            (SELECT COUNT(*) FROM tweets WHERE writer = ?) AS num_tweets,
                            (SELECT COUNT(*) FROM follows WHERE flwer = ?) AS num_following,
                            (SELECT COUNT(*) FROM follows WHERE flwee = ?) AS num_followers;
                        """, (row["usr"], row["usr"], row["usr"],))
                counts = c.fetchone()
                
                # Retrieves the tweets made by the user
                c.execute("""
                    SELECT *
                    FROM tweets t1
                    WHERE t1.writer = ?
                    ORDER BY t1.tdate
                """,(row["usr"],))
                usr_tweets = c.fetchall()

                print(f"Name: {row['name']} | Email: {row['email']} | City: {row['city']} | Timezone: {row['timezone']}")
                print(f"Number of tweets: {counts['num_tweets']} | Number of users followed: {counts['num_following']} | Number of followers: {counts['num_followers']}")
                
                placeholder3 = 0
                length3 = len(usr_tweets)
                if length3 != 0:
                    print("Recent tweets:")
                    for index in range(placeholder3, min(3, length3)):
                        print(f"Date: {usr_tweets[index]['tdate']} | \"{usr_tweets[index]['text']}\"")
                    print()
                    placeholder3 += (index + 1)
                else:
                    print("User has no tweets.\n")
                
                while True:
                    user_input = input("Options:\n1 - Follow user\n2 - Show more tweets\n3 - Go back\n\nInput: ")
                    print()
                    while user_input not in ["1", "2", "3"]:
                        user_input = input("Invalid. Please select from one of the following options:\n1 - Follow user\n2 - Show more tweets\n3 - Go back\n\nInput: ")
                        print()
                    
                    if user_input == "1":
                        # Check if the follow relationship already exists
                        c.execute("""
                            SELECT COUNT(*)
                            FROM follows
                            WHERE flwer = ? AND flwee = ?
                        """, (user_id, row["usr"],))

                        count = c.fetchone()[0]

                        # Prevents the user from following themselves
                        if row["usr"] == user_id:
                            print("You cannot follow your own account.\n")
                        
                        # Executes if the users doesn't have the follow relationship
                        elif count == 0:
                            # Format the current date as 'YYYY-MM-DD'
                            current_date = datetime.now().strftime('%Y-%m-%d')

                            c.execute("""
                                INSERT INTO follows (flwer, flwee, start_date)
                                VALUES (?, ?, ?)
                            """, (user_id, row["usr"], current_date))
                            print(f"You are now following {row['name']}.\n")
                        else:
                            print("You are already following this user.\n")
                    
                    elif user_input == "2":
                        # it's meant to display 5 more tweets
                        if placeholder3 < length3:
                            for index in range(placeholder3, min(placeholder3 + 5, length3)):
                                print(f"Date: {usr_tweets[index]['tdate']} | \"{usr_tweets[index]['text']}\"")
                            print()
                            placeholder3 += 5
                        else:
                            print("No more tweets available to display.\n")

                    elif user_input == "3":
                        # This is to display the previous list of user again
                        placeholder2 -= 5
                        display_again = True
                        break
                    
            elif user_input == "3":
                conn.commit()
                break
            
def compose_tweet(user_id, as_reply, replyto=None):
    global conn, c

    if as_reply == False and replyto is None:
        tweet_text = input("Compose your tweet: ").strip()
        print()
        hashtags = re.findall(r"#(\w+)", tweet_text)
        c.execute("""INSERT INTO tweets (tid, writer, tdate, text, replyto) 
                        VALUES ((SELECT MAX(t1.tid) + 1 FROM tweets t1), ?, ?, ?, NULL)""", (user_id, datetime.now().strftime('%Y-%m-%d'), tweet_text))
    else:
        tweet_text = input("Compose your reply: ").strip()
        print()
        hashtags = re.findall(r"#(\w+)", tweet_text)
        c.execute("""INSERT INTO tweets (tid, writer, tdate, text, replyto) 
                        VALUES ((SELECT MAX(t1.tid) + 1 FROM tweets t1), ?, ?, ?, ?)""", (user_id, datetime.now().strftime('%Y-%m-%d'), tweet_text,replyto))
    
    tweet_id = c.lastrowid
    
    for hashtag in hashtags:
        # Check if the hashtag already exists
        c.execute("""SELECT term 
                        FROM hashtags 
                        WHERE LOWER(term) = ?""", (hashtag.lower(),))
        
        existing_hashtag = c.fetchone()
        
        if existing_hashtag is None:
            # Store any new hashtags in the hashtags table
            c.execute("""INSERT INTO hashtags (term) 
                            VALUES (?)""", (hashtag,))
            
        c.execute("""INSERT INTO mentions (tid, term) 
                        VALUES (?, ?)""", (tweet_id, hashtag))
    if as_reply:    
       print("Reply successfully posted!\n")
    else:                 
        print("Tweet successfully posted!\n")
    conn.commit()

def list_followers(user_id):
    global conn, c

    # Retrieve the list of followers
    c.execute("SELECT u.usr, u.name, u.city FROM users u JOIN follows f ON u.usr = f.flwer WHERE f.flwee = ?", (user_id,))
    followers = c.fetchall()

    if not followers:
        print("You don't have any followers.\n")
        return
    
    for follower in followers:
        print(f"User ID: {follower['usr']:4} | {follower['name']} from {follower['city']}")
    print()

    # Allow the user to select a follower to view more details
    user_input = input("Options:\n1 - Select a follower\n2 - Go back\n\nInput: ")
    print()
    while user_input not in ["1", "2"]:
        user_input = input("Invalid. Please select from one of the following options:\n1 - Select a follower\n2 - Go back\n\nInput:")
        print()

    if user_input == "1":
        selected_follower = input("Select a displayed user ID to show more information: ")
        print()
        while not any(int(selected_follower) == follower['usr'] for follower in followers):
            selected_follower = input("Invalid. No users that match the keyword. Please enter a valid option: ")
            print()

        # Gets basic info from the user
        c.execute("SELECT * FROM users u1 WHERE u1.usr = ?", (selected_follower,))
        user_info = c.fetchone()

        # Retrieve and display more details about the selected follower
        c.execute("""SELECT
                    (SELECT COUNT(*) FROM tweets WHERE writer = ?) as num_tweets,
                    (SELECT COUNT(*) FROM follows WHERE flwer = ?) as num_following,
                    (SELECT COUNT(*) FROM follows WHERE flwee = ?) as num_followers;
                    """, (selected_follower, selected_follower, selected_follower,))
        counts = c.fetchone()
        
        # Retrieves the tweets made by the selected follower
        c.execute("SELECT * FROM tweets t1 WHERE t1.writer = ? ORDER BY t1.tdate",(selected_follower,))
        follower_tweets = c.fetchall()
        
        print(f"Name: {user_info['name']} | Email: {user_info['email']} | City: {user_info['city']} | Timezone: {user_info['timezone']}")
        print(f"Number of tweets: {counts['num_tweets']} | Number of users followed: {counts['num_following']} | Number of followers: {counts['num_followers']}")

        placeholder4 = 0
        length5 = len(follower_tweets)
        if length5 != 0:
            print("Recent tweets:")
            for index in range(placeholder4, min(3, length5)):
                print(f"Date: {follower_tweets[index]['tdate']} | \"{follower_tweets[index]['text']}\"")
            print()
            placeholder4 += (index + 1)
        else:
            print("User has no tweets.\n")

        while True:
            user_input = input("Options:\n1 - Follow user\n2 - Show more tweets\n3 - Go back\n\nInput: ")
            print()
            while user_input not in ["1", "2", "3"]:
                user_input = input("Invalid. Please select from one of the following options:\n1 - Follow user\n2 - Show more tweets\n3 - Go back\n\nInput: ")
                    
            if user_input == "1":
                # Check if they already follow the user
                c.execute("SELECT COUNT(*) FROM follows WHERE flwer = ? AND flwee = ?", (user_id, selected_follower))
                count = c.fetchone()[0]

                # Executes if the users doesn't have the follow relationship
                if count == 0:
                    # Format the current date as 'YYYY-MM-DD'
                    current_date = datetime.now().strftime('%Y-%m-%d')

                    c.execute("INSERT INTO follows (flwer, flwee, start_date) VALUES (?, ?, ?)", (user_id, selected_follower, current_date))
                    print(f"You are now following {user_info['name']}.\n")
                else:
                    print("You are already following this user.\n")

            elif user_input == "2":
                # it's meant to display 5 more tweets
                if placeholder4 < length5:
                    for index in range(placeholder4, min(placeholder4 + 5, length5)):
                        print(f"Date: {follower_tweets[index]['tdate']} | \"{follower_tweets[index]['text']}\"")
                    print()
                    placeholder4 += 5
                else:
                    print("No more tweets available to display.\n")
            elif user_input == "3":
                conn.commit()
                break
    else:
        conn.commit()
        return

# Secondary functions

def tweet_statistics(tweet_id):
    global conn, c
    
    c.execute("""SELECT t1.tid, t1.writer, t1.tdate as date, t1.text,
                (SELECT COUNT(*) FROM tweets t2 WHERE t2.replyto = ?) as reply_count,
                (SELECT COUNT(*) FROM retweets r1 WHERE r1.tid = ?) as retweet_count
                FROM tweets t1
                WHERE t1.tid = ?;""", (tweet_id, tweet_id, tweet_id,))
    tweet_info = c.fetchone()

    conn.commit()
    return tweet_info

def handle_tweet_actions(user_id, tweet_id):  
    global conn, c
    
    # Provide options to reply to a tweet or retweet
    while True:
        action = input("Choose an action: 'reply' to reply to the tweet, 'retweet' to retweet, or 'back' to go back: ")

        if action.lower() == 'reply':
            compose_tweet(user_id, True, replyto=tweet_id)
            break  # After replying, break the loop to avoid multiple replies
        elif action.lower() == 'retweet':
            retweet_tweet(user_id, tweet_id)
            break  # After retweeting, break the loop to avoid multiple retweets
        elif action.lower() == 'back':
            break  # Go back to the previous menu
        else:
            print("Invalid action. Please try again.")
    conn.commit()

def retweet_tweet(user_id, tweet_id):
    global conn, c
    
    # Check if retweet already exists
    c.execute("""
            SELECT COUNT(*)
            FROM RETWEETS
            WHERE usr = ? AND tid = ?
            """, (user_id, tweet_id,))
    
    if c.fetchone()[0] == 0:
        retweet_date = datetime.now().strftime('%Y-%m-%d')

        c.execute("""
            INSERT INTO retweets (usr, tid, rdate)
            VALUES (?, ?, ?)
        """, (user_id, tweet_id, retweet_date))

        print("You have successfully made a retweet!\n")
    else:
        print("You have already retweeted this tweet!\n")

    conn.commit()

def main():
    global conn, c
    
    parser = argparse.ArgumentParser(description="Sign Up Script")
    parser.add_argument("--db", help="Path to the SQLite database file", required=True)
    args = parser.parse_args()

    connect(args.db)
    exit_program = False
    while not exit_program:
        exit_program = login_screen()

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()