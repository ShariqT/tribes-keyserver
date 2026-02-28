import base64
from Crypto.PublicKey import ECC
import secrets
from utils.bip39 import INDEX_TO_WORD_TABLE, decode_phrase, encode_bytes
from Crypto.Protocol import HPKE
import base64
from Crypto.Random import get_random_bytes

def open_keyfile(keyfile_path):
  key, _ = pgpy.PGPKey.from_file(keyfile_path)
  return key

def create_key_from_text(keydata):
  key = ECC.import_key(encoded=keydata, curve_name='X25519')
  return key

def create_pgpmessage_from_text(message_text):
  pass

def create_key_pair(username, email):
  seed = secrets.token_bytes(32)
  passphrase = encode_bytes(seed)
  # for i in range(12):
  #   choice = secrets.choice(INDEX_TO_WORD_TABLE)
  #   passphrase.append(choice)
  
  keypair = ECC.construct(
    curve="X25519",
    seed=seed
  )
  return [keypair, passphrase]

def bytes_to_b64(raw_bytes):
    encoded = base64.b64encode(raw_bytes)
    return encoded.decode('utf-8')

def b64_to_bytes(b64_str):
    print(f"b64_str is {b64_str}")
    decoded_bytes = b64_str.encode('utf-8')
    return base64.b64decode(decoded_bytes)

def encrypt_message(message, public_key):
  encryptor = HPKE.new(receiver_key=public_key, aead_id=HPKE.AEAD.AES128_GCM)
  encrypted_message = encryptor.seal(bytes(message, 'utf-8'))
  # print(encryptor.enc.decode('utf-8'))
  return [bytes_to_b64(encrypted_message), bytes_to_b64(encryptor.enc)]


def decrypt_message(encrypted_message, secret_key, shared_key):
  try:
    encryptor = HPKE.new(receiver_key=secret_key, aead_id=HPKE.AEAD.AES128_GCM, enc=b64_to_bytes(shared_key))
    message = encryptor.unseal(b64_to_bytes(encrypted_message))
    return str(message, 'utf-8')

  except Exception as e:
    raise Exception("could not decrypt message")

def create_cipher_secret():
  key = get_random_bytes(16)
  return bytes_to_b64(key)

def get_key_fingerprint(pubkey_key):
  return pubkey_key.export_key(format="raw")[:20].hex()