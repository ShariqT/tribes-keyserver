import garden, uuid, os

def challenge_identity(key: str):
    challenge = uuid.uuid4()
    pubkey = garden.create_key_from_text(key)
    challenge_message = garden.encrypt_message(str(challenge), pubkey)
    return [str(challenge_message), str(challenge)]

def confirm_identity(challenge_txt: str ,encrypted_message: str):
    encrypted_message = garden.create_pgpmessage_from_text(encrypted_message)
    confirm_message = garden.decrypt_message(encrypted_message, garden.create_key_from_text(os.getenv('SECRET_KEY')))
    return challenge_txt == confirm_message.message