import fastapi
from pydantic import BaseModel
from typing import List
import uvicorn

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

import json
import os
import dotenv

dotenv.load_dotenv()

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class Block(BaseModel):
    name: str
    commonTasks: List[str]
    timeEstimate: str


class Context(BaseModel):
    contextName: str
    Blocks: List[Block]
    completionCriteria: str

class AgentConfig():
    def __init__(self):
        self.Agent = Agent
        api_key = os.getenv("OPENAI_API_KEY")
        self.Agent = Agent(
            name="TaskStructurer",
            instructions="""
                You are a planning assistant. Your job is to take a plaintext list of to-do items or goals from the user and return a structured JSON object using the following format:

                {
                "contextName": "<title of this context>",
                "Blocks": [
                    {
                    "name": "<block name>",
                    "commonTasks": ["<task 1>", "<task 2>", "..."],
                    "timeEstimate": "<estimated time like '1-2 weeks'>"
                    },
                    ...
                ],
                "completionCriteria": "<short description of what it means to consider this context 'complete'>"
                }

                Use intuitive grouping. For example, if the user inputs:
                "Book a wedding venue, invite guests, pick a caterer, send out RSVPs, research florists"

                Then you should return:
                {
                "contextName": "Wedding Planning",
                "Blocks": [
                    {
                    "name": "Venue & Vendors",
                    "commonTasks": ["Book a wedding venue", "Pick a caterer", "Research florists"],
                    "timeEstimate": "2-3 weeks"
                    },
                    {
                    "name": "Guest Management",
                    "commonTasks": ["Invite guests", "Send out RSVPs"],
                    "timeEstimate": "1-2 weeks"
                    }
                ],
                "completionCriteria": "All major services booked and guests invited"
                }
            """
            )
    
    def testAgent(self, input):
        return Runner.run_sync(self.Agent, input)



class mongoDBConfig():
    def __init__(self, uri: str):
        self.uri = uri
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))

        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

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
        
def main():
    #mongoclient = mongoDBConfig(dotenv.get_key('.env', 'MONGO_URI'))
    CompilerAgent = AgentConfig()
    print(CompilerAgent.testAgent("I need toBook a wedding venue, invite guests, pick a caterer, send out RSVPs, research florists"))

if __name__ == "__main__":
    main()
    
'''
{
    "contextName": "Wedding Planning"{
        "Blocks": [
        "Venue & Vendors"
            {
                "name": "Venue & Vendors",
                "commonTasks": ["Research venues", "Get quotes", "Book venue"],
                "timeEstimate": "2-3 weeks"
            },
        "Guest Management"
            {
                "name": "Guest Management", 
                "commonTasks": ["Create guest list", "Send invitations", "Track RSVPs"],
                "timeEstimate": "4-6 weeks"
            }
        ],
        "completionCriteria": "All vendors booked, timeline finalized, guests confirmed"
    }
}

new_context = Context(
    contextName="Wedding Planning",
    Blocks=[
        Block(
            name="Venue & Vendors",
            commonTasks=["Research venues", "Get quotes", "Book venue"],
            timeEstimate="2-3 weeks"
        ),
        Block(
            name="Guest Management",
            commonTasks=["Create guest list", "Send invitations", "Track RSVPs"],
            timeEstimate="4-6 weeks"
        )
    ],
    completionCriteria="All vendors booked, timeline finalized, guests confirmed"
)
'''