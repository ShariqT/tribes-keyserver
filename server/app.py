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
from utils import return_keyserver_pubkey, generate_keys, get_keyfile_directory
from .auth import confirm_identity, challenge_identity
import sys, os
import garden


app = Flask(__name__)



@app.before_request
def ensure_db_indexes():
    try:
      db = FerretDB()
      db.create_indexes()
    except Exception as e:
      print(e)
      print(f"Could not ensure db indexes. Shutting down: {str(e)}")
      sys.exit(1)



@app.route("/")
def index():
  if len(os.listdir(get_keyfile_directory())) == 0:
    generate_keys(os.getenv('USERNAME'), os.getenv('EMAIL'), get_keyfile_directory())
    print(f"generated keys for {os.getenv('USERNAME')}")
  return "ok.computer"


@app.route("/check", methods=["GET"])
def check_username():
  if request.args.get('username', None) is None:
    return ("Go away!", 405)
  try:
    ks = Keystore(FerretDB())
    hold_id = ks.check_username(request.args.get('username'))
    return {'hold_id': str(hold_id)}
  except Exception as e:
    app.logger.error(f"function: get_publickey_from_signature, signature: {signature}, error message: {str(e)}")
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
    challenge, challenge_txt = challenge_identity(record['key'])
    ks.create_challenge(signature, challenge_txt)
    return {'challenge': challenge }
  except Exception as e:
    app.logger.error(f"function: challenge_signature, signature: {signature}, error message: {str(e)}")
    return {'error': 'Could not complete the challenge'}

@app.route("/confirm/<signature>", methods=["POST"])
def confirm_signature(signature):
  try:
    data = request.get_json()
    ks = Keystore(FerretDB())
    record = ks.get_contact(signature)
    challenge_txt = ks.get_current_challenge(signature)
    approved = confirm_identity(challenge_txt, data['attempted_message'])
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
        ks = Keystore(FerretDB())
        ks.store_message(signature, data['from'], data['message'])
        return {'success': True }
    except Exception as e:
        app.logger.error(f"function: send_message_to_signature, signature: {signature}, error message: {str(e)}")
        return {'error': 'Could not send this message. There was an error on the mail server.'}

@app.route("/save", methods=["POST"])
def save_key():
  data = request.get_json()
  object_id = data.get('username_id')
  pubkey = data.get('pubkey')
  pubkey_key = garden.create_key_from_text(pubkey)
  try:
    ks = Keystore(FerretDB())
    ks.save(object_id, pubkey, pubkey_key.fingerprint)
    return {'success': True}
  except Exception as e:
    print(e)
    app.logger.error(f"function: save_key, objectid: {objectid}, pubkey: {pubkey},  error message: {str(e)}")
    return {'error': f'Error saving key: {str(e)}'}

