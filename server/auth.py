import garden, uuid, os, utils

def challenge_identity(key: str):
    challenge = uuid.uuid4()
    pubkey = garden.create_key_from_text(key)
    challenge_message, shared_key = garden.encrypt_message(str(challenge), pubkey)
    return [str(challenge_message), str(challenge), shared_key]

def confirm_identity(challenge_txt: str ,encrypted_message: str, shared_key):
    secret_key = utils.open_server_secret_key()
    confirm_message = garden.decrypt_message(encrypted_message, secret_key, shared_key)
    print(f"confirm_message {confirm_message}")
    print(f"challenge_txt {challenge_txt}")
    return challenge_txt == confirm_message