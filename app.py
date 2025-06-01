import fastapi
import pydantic
import uvicorn
import openai
from agents import Agent, Runner

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

class mongoDBConfig():
    def __init__(self, uri: str):
        self.uri = uri
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))
        self.db = self.client['testing']
        self.collection = self.db['users']

    def insert_user(self, user: dict):
        try:
            result = self.collection.insert_one(user)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error inserting user: {e}")
            return None
        
    def get_user(self, user_id: str):
        try:
            user = self.collection.find_one({"_id": user_id})
            return user
        except Exception as e:
            print(f"Error retrieving user: {e}")
            return None
        

    