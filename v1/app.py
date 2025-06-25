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

class User(BaseModel):
    username: str
    contexts: List[Context]

class AgentConfig():
    def __init__(self):
        #self.Agent = Agent
        api_key = os.getenv("OPENAI_API_KEY")
        self.Agent = Agent(
            name="TaskStructurer",
            instructions="""
                You are a planning assistant. Your job is to take a plaintext list of to-do items or goals from the user and return a structured JSON object using the following format, make a plan based on whatever the user inputs, even if it is not "enough" information:


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
        

        '''
        {
        'context': 'wedding planning':
            {'tasks':[
                {'call vendors': ''}
                ]
            }
        }
        '''
    
    def runAgent(self, input):
        return Runner.run_sync(self.Agent, input)



class mongoDBConfig():
    def __init__(self, uri: str = os.getenv("MONGO_URI")):
        self.uri = uri
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))

        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

        self.db = self.client['testing']
        self.collection = self.db['users']

    def get_user_by_name(self, username: str):
        return self.collection.find_one({"username": username})

    def create_user_if_not_exists(self, username: str):
        self.collection.update_one(
            {"username": username},
            {"$setOnInsert": {"username": username, "contexts": []}},
            upsert=True
        )
    def createContext(self, context: dict, username: str):
        try:
            self.collection.update_one(
                {"username": username},
                {"$push": {"contexts": context}},  # push context into user's contexts array
                upsert=True  # creates user if not exists
            )
            print(f"Context added for user '{username}'.")
            return True
        except Exception as e:
            print(f"Error adding context: {e}")
            return False



        
class testUserMongoSynth():
    def __init__(self):
        self.userName = input("input your username: ").strip()
        self.mongoCon = mongoDBConfig()

        self.mongoCon.create_user_if_not_exists(self.userName)
        user_data = self.mongoCon.get_user_by_name(self.userName)

        self.CompilerAgent = AgentConfig()

        print(f"Welcome back!\ndata: {user_data}" if user_data else "Account created.")

    def runUser(self):
        while True:
            usrInput = input("e: enter task\t r: remove task\t q: exit\t p: print tasks\n").lower()

            if usrInput == "q":
                print("Exiting.")
                break
            elif usrInput == "p":
                user_data = self.mongoCon.get_user_by_name(self.userName)
                print(json.dumps(user_data.get("contexts", []), indent=2))
            elif usrInput == "e":
                goals = input("Enter your planning goals (e.g. 'Book a hotel, pack clothes, buy tickets'):\n> ").strip()

                try:
                    response = self.CompilerAgent.runAgent(goals).final_output.strip("'''")

                    print(f"response: {response}")

                    if not response:
                        print("Agent returned an empty response.")
                        return

                    try:
                        context_json = json.loads(response)
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse agent output:\n{response}")
                        print(f"JSON error: {e}")
                        return

                    success = self.mongoCon.createContext(self.userName, context_json)

                    if success:
                        print("Successfully saved your new planning context!")
                    else:
                        print("Failed to save context.")
                except Exception as e:
                    print(f"Error handling context: {e}")
            elif usrInput == "r":
                pass
                
        
        
def main():

    testUser = testUserMongoSynth()
    testUser.runUser()

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