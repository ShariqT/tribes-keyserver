from abc import ABC, abstractmethod
from .messages import MessageRouter

class DataCenter(ABC):
    @abstractmethod
    def create_challenge(self, signature:str, challenge_txt:str):
        pass
    
    @abstractmethod
    def get_challenge_for_signature(self, signature:str):
        pass
    
    @abstractmethod
    def check_for_username(self, potential_username: str):
        pass

    @abstractmethod
    def save_key_and_username(self, username: str, pubkey: str, signature: str):
        pass
    
    @abstractmethod
    def save_message(self, signature:str, from_username: str, encrypted_message:str):
        pass
      
    @abstractmethod
    def get_messages(self, signature: str):
        pass
    
    @abstractmethod
    def remove_challenge(self, signature: str):
        pass
    
    @abstractmethod
    def search_by_username(self, query: str):
        pass
    
class Keystore:
    def __init__(self, storage: DataCenter):
        self.storage = storage
    def check_username(self, username: str):
        return self.storage.check_for_username(username)
    def save(self, username: str, publickey: str, signature: str):
        return self.storage.save_key_and_username(username, publickey, signature)
    def get_contact(self, signature: str):
        return self.storage.get_key_and_username(signature)
    def create_challenge(self, signature, challenge_txt):
        return self.storage.create_challenge(signature, challenge_txt)
    def get_current_challenge(self, signature):
        return self.storage.get_challenge_for_signature(signature)
    def retrieve_messages(self, signature):
        return self.storage.get_messages(signature)
    def store_message(self, to_signature, from_username, encrypted_message):
        return self.storage.save_message(to_signature, from_username, encrypted_message)
    def remove_challenge(self, signature):
        return self.storage.remove_challenge(signature)
    def search_by_username(self, query):
        return self.storage.search_by_username(query)
