import garden, uuid, os, utils

def challenge_identity(key: str):
    challenge = uuid.uuid4()
    pubkey = garden.create_key_from_text(key)
    challenge_message = garden.encrypt_message(str(challenge), pubkey)
    return [str(challenge_message), str(challenge)]

def confirm_identity(challenge_txt: str ,encrypted_message: str):
    encrypted_message = garden.create_pgpmessage_from_text(encrypted_message)
    secret_key = utils.open_server_secret_key()
    confirm_message = garden.decrypt_message(encrypted_message, secret_key)
    print(f"confirm_message {confirm_message}")
    print(f"challenge_txt {challenge_txt}")
    return challenge_txt == confirm_message.message