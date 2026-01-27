import garden

class MessageRouter:
    def verify_signature(self, pubkey: str, signature_to_check: str, encrypted_message: str):
        pubkey_key = garden.create_key_from_text(pubkey)
        return pubkey.verify(encrypted_message)

