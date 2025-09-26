import fastapi
from pydantic import BaseModel, Field
from uuid import UUID
from typing import List
import uvicorn
from typing import Optional

import fastapi
from pydantic import BaseModel
from typing import List, Literal
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
from fastapi import FastAPI, Header, Body, HTTPException

import psycopg2
from dotenv import load_dotenv

from supabase import create_client
from supabase.client import ClientOptions


from fastapi.middleware.cors import CORSMiddleware

import datetime

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

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


class TaskCreate(BaseModel):
    title: str
    description: str
    ai_generated_subtasks: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    deadline_type: Literal['soft', 'hard'] | None = None
    due_date: str | None = None
    priority: int = Field(default=None, ge=1, le=10)
    # estimated_time: str | None = None

class usr_task_in(BaseModel):
    title: str
    description: str


def extract_jwt(authorization: str) -> str:
    """Extracts JWT from Authorization header."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization.split(" ", 1)[1]

def init_database(authorization: str) -> str:
    usrJWT = extract_jwt(authorization)

    options = ClientOptions(headers={
        "Authorization": f"Bearer {usrJWT}"
    })

    supabase = create_client(
        SUPABASE_URL,
        SUPABASE_ANON_KEY,
        options=options
    )

    return supabase

@app.post("/api/v1/tasks/create")
async def run_task_gen(
    task: usr_task_in,
    authorization: str = Header(...)
):
    supabase = init_database(authorization)

    AGENT_INSTRUCTIONS = f"""
        You are a task planning assistant. You will receive a plaintext list of to-do items or goals.
        Return a **JSON object** with exactly these snake_case fields:

        {{
            "title": string,
            "description": string,
            "ai_generated_subtasks": [string, ...],
            "labels": [string, ...],
            "deadline_type": "soft" | "hard" | null,
            "due_date": string | null,          // ISO-8601 date or datetime
            "priority": integer,         // integer between 1 and 10 (never null), lower numbers are higher priority
        }}

        HARD REQUIREMENTS:
        - Output **only** a JSON object; no extra text, no markdown.
        - Do NOT include: id, user_id, created_at.
        - If a value is unknown, use null (do not invent).
        - For relative dates like "next Friday", convert to an absolute ISO-8601 value using the current date.
        Current local datetime: {datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()}
        """

    agent = Agent(name="TaskStructurer", instructions=AGENT_INSTRUCTIONS, output_type=TaskCreate)
    agent_input = f"Task Title: {task.title}\nTask Description: {task.description}"
    result = await Runner.run(agent, agent_input)

    try:
        raw = result.final_output if isinstance(result.final_output, str) else result.final_output
        obj = json.loads(raw)
    except Exception:
        raise HTTPException(400, "Agent did not return valid JSON")

    try:
        t = TaskCreate.model_validate(obj)
    except Exception as e:
        raise HTTPException(400, f"Agent output failed schema validation: {e}")

    payload = t.model_dump(exclude_none=True)

    payload['title'] = task.title
    payload['description'] = task.description
    payload['priority'] = 10 if payload.get('priority') == None else payload['priority'] #can use "p['prio'] ==" if we are confident in pydantic
        

    # if isinstance(payload.get("labels"), list):
    #     payload["labels"] = json.dumps(payload["labels"], ensure_ascii=False)
    # if isinstance(payload.get("ai_generated_subtasks"), list):
    #     payload["ai_generated_subtasks"] = json.dumps(payload["ai_generated_subtasks"], ensure_ascii=False)

    resp = (
        supabase.table("tasks")
        .insert(payload)
        .execute()
    )

    return resp

@app.delete("/api/v1/users/{user_id}")
async def delete_user(
    user_id: str,
    authorization: str = Header(...)
):
    usrJWT = extract_jwt(authorization)
    supabase = init_database(authorization)

    user = supabase.auth.get_user(usrJWT)

    # Check if the user_id from JWT matches the user_id in the API path
    if user.user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized: User IDs don't match"
        )

    # Create admin client with service role key
    admin_client = create_client(
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY,
    )

    try:
        admin_client.auth.admin.delete_user(
            id=user_id,
            shouldSoftDelete=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting user: {str(e)}"
        )

'''
def main():
    input = """

        So I am going on PAT leave on July 13th and will be returning on . Big priorities are
        1: Get Q3 roadmaps done before July 13th for Analytics, Platform, Product usage and architecture
        2: Setup Confluencd page for all the programs with the new template
        2.a. Tableau Cloud
        2.b   Harmony
        2.c.  OSIC
        2.d. WITS

    ""
    # runTaskGen("123e4567-e89b-12d3-a456-426614174000", input)

if __name__ == "__main__":
    # main()
    pass
'''