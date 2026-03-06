"""
Very simple implementation of a Tribes keyserver server.
Right now, the keyserver will do the following:
1) check for username collisions
2) add public keys
3) retrieve public keys by username

"""

from flask import Flask, request
from .db import Keystore
from .messages import MessageRouter
from .ferretdb import FerretDB
from utils import return_keyserver_pubkey, generate_keys, get_keyfile_directory, open_server_secret_key
from .auth import confirm_identity, challenge_identity
import sys, os, json
import garden
import utils
import secrets




app = Flask(__name__)



@app.before_request
def ensure_db_indexes():
    try:
      db = FerretDB()
      db.create_indexes()
    except Exception as e:
      print(e)
      print(os.environ['DATABASE_URI'])
      print(f"Could not ensure db indexes. Shutting down: {str(e)}")
      sys.exit(1)



@app.route("/")
def index():
  print(os.listdir(get_keyfile_directory()))
  if len(os.listdir(get_keyfile_directory())) == 0:
    generate_keys(os.getenv('USERNAME'), os.getenv('EMAIL'), get_keyfile_directory())
    app.logger.error(f"generated keys for {os.getenv('USERNAME')}")
  return "ok.computer"


@app.route("/check", methods=["GET"])
def check_username():
  if request.args.get('username', None) is None:
    return ("Go away!", 405)
  try:
    ks = Keystore(FerretDB())
    username = request.args.get('username')
    hold_id = ks.check_username(username)
    return {'hold_id': str(hold_id)}
  except Exception as e:
    app.logger.error(f"function: check_username, username: {username}, error message: {str(e)}")
    return {'error': f'Error checking username because: {str(e)}'}


@app.route("/username", methods=["GET"])
def find_username():
  try:
    ks = Keystore(FerretDB())
    doc = ks.search_by_username(request.args.get('username'))
    return {'matches': doc }
  except Exception as e:
    app.logger.error(f"function: find_username, username: {request.args.get('username')}, error message: {str(e)}")
    return {"error": "There was an error durimg the search"}


@app.route("/card/<signature>", methods=['GET'])
def get_publickey_from_signature(signature):
    try:
      ks = Keystore(FerretDB())
      card_info = ks.get_contact(signature)
      return {'username': card_info['username'], 'key': card_info['key'], 'signature': signature }
    except Exception as e:
      app.logger.error(f"function: get_publickey_from_signature, signature: {signature}, error message: {str(e)}")
      return {'error': f'Error getting this signature: {str(e)}'}


@app.route("/challenge/<signature>", methods=["POST"])
def challenge_signature(signature):
  try:
    ks = Keystore(FerretDB())
    record = ks.get_contact(signature)
    challenge, challenge_txt, shared_key = challenge_identity(record['key'])
    ks.create_challenge(signature, challenge_txt)
    return {'challenge': challenge, 'enc': shared_key }
  except Exception as e:
    import traceback
    traceback.print_exc()
    app.logger.error(f"function: challenge_signature, signature: {signature}, error message: {str(e)}")
    return {'error': 'Could not complete the challenge'}

@app.route("/confirm/<signature>", methods=["POST"])
def confirm_signature(signature):
  try:
    data = request.get_json()
    print(f"data in confirm is {data}")
    ks = Keystore(FerretDB())
    record = ks.get_contact(signature)
    receiver_key = garden.create_key_from_text(record['key'])
    challenge_txt = ks.get_current_challenge(signature)
    approved = confirm_identity(challenge_txt, data['attempted_message'], data['enc'])
    ks.remove_challenge(signature)
    if approved is True:
      current_messages = ks.retrieve_messages(signature)
      if current_messages is None:
        current_messages = []
      return {'messages': current_messages }
    else:
      return {'error': 'Challenge failed!'}
  except Exception as e:
    if os.getenv('MODE') == 'DEBUG':
      import traceback
      traceback.print_exc() 
    app.logger.error(f"function: confirm_signature, signature: {signature}, error message: {str(e)}")
    return {'error': f'Could not get messages: {str(e)}'}


@app.route("/key", methods=['GET'])
def send_server_key():
    return {'key': return_keyserver_pubkey() }

# client will send signature of person they want to send it to
# and the encrypted message. client will have already downloaded the 
# receiptent's public key
@app.route("/send/<signature>", methods=["POST"])
def send_message_to_signature(signature):
    try:
        data = request.get_json()
        print(f"send sig {data}")
        ks = Keystore(FerretDB())
        ks.store_message(signature, data['from'], data['message'], data['enc'])
        return {'success': True }
    except Exception as e:
        app.logger.error(f"function: send_message_to_signature, signature: {signature}, error message: {str(e)}")
        return {'error': 'Could not send this message. There was an error on the mail server.'}

@app.route("/tribe/join/<tribe_id>", methods=["POST"])
def join_tribe(tribe_id):
    data = request.get_json()
    try:
        ks = Keystore(FerretDB())
        receiver_key = garden.create_key_from_text(data['key'])
        signature = garden.get_key_fingerprint(receiver_key)
        challenge_txt = ks.get_current_challenge(signature)
        approved = confirm_identity(challenge_txt, data['attempted_message'], data['enc'])
        ks.remove_challenge(signature)
        if approved is True:
            payload = garden.decrypt_message(data['payload'], receiver_key, data['enc'])
            paylaod = json.loads(payload)
            record = ks.get_tribe_record(tribe_id)
            if record is None:
              return {"error": "Searched high and low...no tribe found"}
            if payload['signature'] == record['admin_signature']:
              return {"error": "You are already an admin for this tribe"}
            if payload['signature'] in record['blocklist']:
              return {"blocked": "You have been blocked from this tribe. Get the fuck away!"}
            response = garden.encrypt_message(record, receiver_key)
            return {
              "data": response
            }
    except Exception as e:
        app.logger.error(f"function: join_tribe, signature: {signature}, error message: {str(e)}")
        return {'error': 'Could not send this tribe. There was an error on the mail server.'}

@app.route("/tribe/<tribe_id>/post", methods=["POST"])
def post_message_to_tribe(tribe_id):
    data = request.get_json()
    try:
        ks = Keystore(FerretDB())
        receiver_key = garden.create_key_from_text(data['key'])
        signature = garden.get_key_fingerprint(receiver_key)
        challenge_txt = ks.get_current_challenge(signature)
        approved = confirm_identity(challenge_txt, data['data'][0]['attempted_challenge'], data['data'][0]['enc'])
        ks.remove_challenge(signature)
        if approved is True:
            record = ks.get_tribe_record(tribe_id)
            secret_key = utils.open_server_secret_key()
            payload = garden.decrypt_message(data['data'][1]['payload'], secret_key, data['data'][1]['enc'])          
            # data_str = f"{username}@@{datetime.now(pytz.UTC)}@@{form_values['title']}@@{text_image_dict['original_text']}@@{json.dumps(links)}"
            poster_username, dt_posted, post_title, post_text, link_data = payload.split("@@")
            new_post = {
              "from": poster_username, 
              "posted": dt_posted,
              "title": post_title,
              "text": post_text,
              "link_data": link_data
            }
            encrypted_data = garden.cipher_encrypt(bytes(json.dumps(new_post), 'utf-8'), garden.b64_to_bytes(record['shared_key']))
            ks.post_message_to_tribe(tribe_id, encrypted_data)
            return { "success": True }
        else:
            return {
              "error": "Man, something is fucked up on the server"
            }
    except Exception as e:
        import traceback
        print(traceback.print_exc())
        app.logger.error(f"function: post_message_to_tribe, tribe_id: {tribe_id}, error message: {str(e)}")
        return {'error': 'There was an error posting to this mail server.'}

@app.route("/tribe/<tribe_id>", methods=["POST"])
def get_tribe(tribe_id):
    # payload from client is 
    #  { "key": <client public key>
    #  "data": [
    #       {"attempted_challenge": attempted_challenge, "enc": attempted_challenge_enc},
    #      {"payload": payload, "enc": payload_enc}
    #  ]  
    # }
    #   decrypted payload data is this:
    # [
    #      "user signature"
    # ] 
    #
    # this will be encrypted by the usual method
    data = request.get_json()
    try:
      ks = Keystore(FerretDB())
      receiver_key = garden.create_key_from_text(data['key'])
      signature = garden.get_key_fingerprint(receiver_key)
      challenge_txt = ks.get_current_challenge(signature)
      approved = confirm_identity(challenge_txt, data['data'][0]['attempted_challenge'], data['data'][0]['enc'])
      ks.remove_challenge(signature)
      if approved is True:
        secret_key = utils.open_server_secret_key()

        payload = garden.decrypt_message(data['data'][1]['payload'], secret_key, data['data'][1]['enc'])          
        requestor_signature, _ = payload.split("@@")

        record = ks.get_tribe_record(tribe_id)
        print(record)
        is_admin = False
        if record is None:
          return {"error": "Search high and low..no tribe was found"}
        if requestor_signature == record['admin_signature']:
          is_admin == True
        if signature in record['blocklist']:
          return {"blocked": "You have been blocked from this tribe. Get the fuck away!"}
        record['_id'] = str(record['_id'])
        message_str = []
        for message in record['messages']:
          message_str.append({
            'ct': message['ct'],
            'iv': message['iv']
          })
        print(f"message_str is {message_str}")
        data_bytes = f"{str(record['_id'])}@@{json.dumps(message_str)}@@{record['shared_key']}@@{record['description']}@@{is_admin}"
        response, enc = garden.encrypt_message(data_bytes, receiver_key)
        return {
          "data": response,
          "enc": enc
        }
      else:
        return {"error": "Man, something fucked on the server!"}
    except Exception as e:
      import traceback
      print(traceback.print_exc())
      app.logger.error(f"function: get_tribe, signature: {signature}, error message: {str(e)}")
      return {'error': 'There was an error on the mail server.'}


@app.route("/tribe/create", methods=["POST"])
def create_new_tribe():
  # payload from client is 
  #  { "key": <client public key>
  #  "data": [
  #       {"attempted_challenge": attempted_challenge, "enc": attempted_challenge_enc},
  #      {"payload": payload, "enc": payload_enc}
  #  ]  
  # }
  #   decrypted payload data is this:
  # {
  #    "name": "new tribe name",
  #     "userame": "username", 
  #      "signature": "user signature"
  # } 
  #
  # this will be encrypted by the usual method
  data = request.get_json()
  print(data)
  try:
    ks = Keystore(FerretDB())
    receiver_key = garden.create_key_from_text(data['key'])
    signature = garden.get_key_fingerprint(receiver_key)
    challenge_txt = ks.get_current_challenge(signature)
    approved = confirm_identity(challenge_txt, data['data'][0]['attempted_challenge'], data['data'][0]['enc'])
    ks.remove_challenge(signature)
    if approved is True:
      secret_key = utils.open_server_secret_key()

      payload = garden.decrypt_message(data['data'][1]['payload'], secret_key, data['data'][1]['enc'])
      payload_split = payload.split("@@")
      cipher_key = garden.create_cipher_secret()
      tribe_id = ks.create_tribe({
        "tribe_name": payload_split[0], 
        "tribe_description": payload_split[1], 
        "admin_username": payload_split[2],
        "admin_signature": payload_split[3]
        }, cipher_key)
      return {'success': True, 'tribe_id': str(tribe_id) }
    else:
      return {'error': 'Challenge failed!'}
  except Exception as e:
    import traceback
    traceback.print_exc()
    return {'error': f'Error saving key: {str(e)}'}



@app.route("/save", methods=["POST"])
def save_key():
  data = request.get_json()
  object_id = data.get('username_id')
  pubkey = data.get('pubkey')
  pubkey_key = garden.create_key_from_text(pubkey)
  fingerprint = garden.get_key_fingerprint(pubkey_key)
  try:
    ks = Keystore(FerretDB())
    ks.save(object_id, pubkey, fingerprint)
    return {'success': True}
  except Exception as e:
    print(e)
    app.logger.error(f"function: save_key, objectid: {object_id}, pubkey: {pubkey},  error message: {str(e)}")
    return {'error': f'Error saving key: {str(e)}'}

