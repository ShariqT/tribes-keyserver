from server.db import DataCenter
from server.messages import MessageRouter
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
from datetime import datetime
import pytz
import os
import garden

load_dotenv()
CONNECTION_URI = os.environ['DATABASE_URI']


class FerretDB(DataCenter):
    def __init__(self):
        self.conn_uri = CONNECTION_URI

    def search_by_username(self, query: str):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            keys_username = db['keys_username']
            record = keys_username.find(
              {'username': {'$regex': query}}, 
              {'username':1 , 'signature': 1, '_id':0, 'key': 1}).limit(20)
            return list(record)
        except Exception as e:
            raise Exception("Search failed!")
        finally:
            client.close()
    def check_for_username(self, potential_username: str):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            reserved_names = db['reserved_names']
            if reserved_names.find_one({'username': potential_username}):
                raise Exception("Someone already took this")
            names_on_hold = db['names_on_hold']
            held_names_doc = names_on_hold.find_one({'username': potential_username })
            if held_names_doc is not None:
              raise Exception(f"{potential_username} is on hold. Please try again later.")
            result = names_on_hold.insert_one({
                'username': potential_username,
                'createdAt': datetime.now(pytz.UTC)
            })
            return result.inserted_id
        finally:
            client.close()

    def get_tribe_record(self, tribe_id: str):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            tribes_collection = db['tribes']
            tribe_doc = tribes_collection.find_one({
              '_id': tribe_id
            })
            return tribe_doc
        finally:
            client.close()


    def post_message_to_tribe(self, tribe_id: str, encrypted_message: str):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            tribes_collection = db['tribes']
            tribe_doc = tribes_collection.find_one({
              '_id': tribe_id
            })
            tribe_doc.messages.append({
              'enc': encrypted_message,
              'createdAt': datetime.now(pytz.UTC)
            })
            tribes_collection.update_one({'_id': tribe_id}, tribe_doc)
        finally:
            client.close()


    def create_tribe(self, data: dict, secret: str):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            tribes_collection = db['tribes']
            inserted_doc = tribes_collection.insert_one({
              'name': data['tribe_name'],
              "description": data['tribe_description'],
              'admin_signature': data['admin_signature'],
              'shared_key':  secret,
              'blocklist': [],
              'members': [ data['admin_signature'] ],
              'messages':[]
            })
            return inserted_doc.inserted_id
        finally:
            client.close()
      
    def save_key_and_username(self, username_id: str, key: str, signature: str):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            names_on_hold = db['names_on_hold']
            document = names_on_hold.find_one({'_id': ObjectId(username_id)})
            if not document:
                raise Exception("Could not find this username. Has this username been requested to be held?")
            future_username = document['username']
            keys_username = db['keys_username']
            try:
                keys_username.insert_one({'username': future_username, 'key': key, 'signature': signature})
            except Exception:
                raise Exception("Could not save this username. The username will go to being unreserved in 15 minutues.")
            try:
                names_on_hold.delete_one({'_id': ObjectId(username_id)})
            except Exception:
                raise Exception(f"Could not delete {future_username} from the name on hold collection. Alert someone!")
            return True
        finally:
            client.close()
        

    def get_challenge_for_signature(self, signature):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            history = db['challenge_history']
            record = history.find_one({'signature': signature})
            if record is None:
                raise Exception(f"No challenge found")
            return record['challenge_txt']
        except Exception as e:
            raise Exception(f"Could not confirm identity: {str(e)}")
        finally:
            client.close()


    def create_challenge(self, signature, challenge_txt):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            history = db['challenge_history']
            history.insert_one({
              'challenge_txt': challenge_txt,
              'signature': signature,
              'createdAt': datetime.now(pytz.UTC)
            })
            return True
        except Exception as e:
            raise Exception(f"Could not find the challenge text for {signature}")
        finally:
            client.close()

    def get_key_and_username(self, signature: str):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            key_username = db['keys_username']
            card_info = key_username.find_one({'signature': signature})
            if card_info is None:
                raise Exception(f"Signature does not exist")
            return card_info
        except Exception as e:
            raise Exception(f"Could not retrieve the contact info. {str(e)}")
        finally:
            client.close()
    

    def remove_challenge(self, signature):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            history = db['challenge_history']
            history.delete_one({'signature': signature})
        except Exception as e:
            raise Exception(f"Could not remove challenge")
        finally:
            client.close()

    def get_messages(self, signature):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            messages = db['message_storage']
            selected = messages.find({'to': signature}, {'to': 1, 'from': 1, 'message': 1, 'enc': 1, '_id': 0})
            return list(selected)
        except Exception as e:
            raise Exception(f"Could not find any messages")
        finally:
            client.close()




    def save_message(self, to_signature:str, from_username:str, client_encrypted_message:str, enc:str):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            messages = db['message_storage']
            messages.insert_one({
              'from': from_username, 
              'to': to_signature, 
              'message': client_encrypted_message,
              'enc': enc,
              'createdAt': datetime.now(pytz.UTC) 
            })
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"Could not send this message: {str(e)}")
        finally:
            client.close()



    def create_indexes(self):
        client = MongoClient(self.conn_uri)
        try:
            db = client['keystore']
            names_on_hold = db['names_on_hold']
            names_on_hold.create_index('createdAt', expireAfterSeconds=600)
            messages = db['message_storage']
            messages.create_index('createdAt', expireAfterSeconds=10800)
            challenges = db['challenge_history']
            challenges.create_index('createdAt', expireAfterSeconds=120)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception("Could not create neccessary indexes. Stop the server!")
        finally:
            client.close()
