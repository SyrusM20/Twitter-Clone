import argparse
import json
from pymongo import MongoClient

def insert_batch(batch, collection):
    collection.insert_many(batch)

def main():
    parser = argparse.ArgumentParser(description="Load json script")
    parser.add_argument("--json", help="JSON file to be read for the program", default="10.json")
    parser.add_argument("--port", help="Port for the program", default="27017")
    args = parser.parse_args()

    client = MongoClient("mongodb://localhost:" + args.port)
    db = client["database"]
    tweets = db["tweets"]

    # Drop and create the "tweets" collection
    tweets.drop()
    db.create_collection("tweets")

    # Set your desired batch size
    batch_size = 10000

    with open(args.json, 'r') as json_file:
        batch = []
        for line in json_file:
            try:
                json_data = json.loads(line)
                batch.append(json_data)
                if len(batch) == batch_size:
                    insert_batch(batch, tweets)
                    batch = []
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                continue

        # Insert any remaining data in the last batch
        if batch:
            insert_batch(batch, tweets)

if __name__ == "__main__":
    main()
