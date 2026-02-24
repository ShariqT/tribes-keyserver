import garden
import os, json
from Crypto.PublicKey import ECC


def generate_keys(username, email, path):
  try:
    keypair, passphrase = garden.create_key_pair(username, email)
    pubkey = keypair.public_key()
    pubkey_data = {
      "username": username,
      "email": email,
      "key": pubkey.export_key(format='PEM')
    }
  except Exception as e:
    print(e)
  try:
    os.makedirs(path)
  except FileExistsError:
    print(f"path already exists: {path}")
    pass
  
  print("Saving keys in " + path)
  try:
    fp = open( path + "/pub.json", "w+")
    fp.write(json.dumps(pubkey_data))
    fp.close()

    fp = open( path + "/p.txt", "w+")
    fp.write(passphrase)
    fp.close()

    fp = open(path + "/sec.key", "w+")
    fp.write(keypair.export_key(format='PEM'))
    fp.close()
    print("Keys created!")
  except Exception as e:
    print(e)


def get_keyfile_directory():
  path = "/keys"
  if os.environ['MODE'] == 'DEBUG':
    path = "./skeys"
  return path


def open_server_public_key():
  fp = open(os.path.join(get_keyfile_directory(), "pub.json"))
  keydata = json.loads(fp.read())
  key = ECC.import_key(keydata['key'])
  fp.close()
  return key

def open_server_secret_key():
  fp = open(os.path.join(get_keyfile_directory(), "sec.key"))
  keydata = fp.read()
  key = ECC.import_key(keydata)
  fp.close()
  return key


def return_keyserver_pubkey():
  fp = open(os.path.join(get_keyfile_directory(), "pub.json"))
  keydata = json.loads(fp.read())
  fp.close()
  return keydata['key']