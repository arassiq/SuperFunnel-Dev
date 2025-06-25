import fastapi
from pydantic import BaseModel
from typing import List
import uvicorn
from typing import Optional

import fastapi
from pydantic import BaseModel
from typing import List
import uvicorn
import requests

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
from fastapi import FastAPI, Header, Body

import psycopg2
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware

import datetime

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.get("/")
def root():
    return {"message": "it works!"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#SUPABASE_URL = "https://your-project.supabase.co"
#SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  

class mainTask(BaseModel):
    id: str
    content: str
    aiGeneratedSubtasks: List[str]
    labels: List[str]
    deadlineType: str
    deadline: str
    priority: int
    estimatedTime: str
    createdAt: str

@app.post("/runTaskGen")
def runTaskGen():
    userAuthHeader: Optional[str] = Header(None), 
    usrTaskInput: str = Body(...)

    '''
        TODO:
            - integrate auth = userAuthHeader -> authAPI -> UserID
            - use the UserID for db insertion instead of sudo id

    ''' 

    userID = userAuthHeader

    USER = os.getenv("user") 
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")

    # Connect to the database
    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        print("Connection successful!")
        
        cursor = connection.cursor()

        cursor.execute("SELECT id FROM users WHERE id = %s;", (userID,))
        result = cursor.fetchone()

        if result is None:
            cursor.execute("INSERT INTO users (id) VALUES (%s);", (userID,))
            connection.commit()
        
        agent_taskGen = Agent(
            name="TaskStructurer",
            instructions="""
                You are a task planning assistant. Your job is to take a plaintext list of to-do items or goals from the user and return a structured list of JSON objects. Each object should conform to the following structure:

                {
                "id": "<unique id for this task>",
                "content": "<the original user-entered task text>",
                "aiGeneratedSubtasks": ["<step 1>", "<step 2>", "..."],
                "labels": ["<category or tag>", "..."],
                "deadlineType": "<either 'soft' or 'hard' no other value>",
                "deadline": "<ISO date string or natural language deadline like 'next Friday'>",
                "priority": <integer between 1 (low) and 10 (high)>,
                "estimatedTime": "<estimated time to complete, like '2 hours' or '1-2 days'>",
                "createdAt": "<timestamp of when the task was created, ideally ISO format>"
                }

                Return one JSON object for each to-do item the user provides. Use your best judgment to infer subtasks, estimate completion time, and categorize the task. Do not stray from the file structure, nor reply with any other text. make sure to look at the current date time and adjust all your outputs based on the date time inputted:
            """ + f"current date, time: {datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()}",
            output_type=mainTask
        )

        agent_taskGenOut = (Runner.run_sync(agent_taskGen, usrTaskInput).final_output).model_dump()

        print(agent_taskGenOut)

        cursor.execute("""
        INSERT INTO tasks (
            user_id,
            content,
            ai_generated_subtasks,
            labels,
            deadline_type,
            deadline,
            priority,
            estimated_time,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            userID, #TODO CHANGE FOR THE AUTH API USERID 
            agent_taskGenOut["content"],
            agent_taskGenOut["aiGeneratedSubtasks"],
            agent_taskGenOut["labels"],
            agent_taskGenOut["deadlineType"],
            agent_taskGenOut["deadline"],
            agent_taskGenOut["priority"],
            agent_taskGenOut["estimatedTime"],
            agent_taskGenOut["createdAt"]
        ))
        connection.commit()

        cursor.close()
        connection.close()
        print("Connection closed.")

        return json.dumps(agent_taskGenOut)

    except Exception as e:
        return f"Failed to connect: {e}"

    
    
def main():
    input = """

        So I am going on PAT leave on July 13th and will be returning on . Big priorities are
        1: Get Q3 roadmaps done before July 13th for Analytics, Platform, Product usage and architecture
        2: Setup Confluencd page for all the programs with the new template
        2.a. Tableau Cloud
        2.b   Harmony
        2.c.  OSIC
        2.d. WITS

    """
    runTaskGen("123e4567-e89b-12d3-a456-426614174000", input)

if __name__ == "__main__":
    main()
    