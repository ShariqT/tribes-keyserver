from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()
CONNECTION_URI = os.environ['DATABASE_URI']
