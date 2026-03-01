from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from agent.graph_builder import builder
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from langchain_core.messages import HumanMessage
from contextlib import asynccontextmanager
from utils import stream_app_output

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSqliteSaver.from_conn_string("./medical_chatbot.db") as checkpointer:
        app.state.checkpointer = checkpointer
        yield   

app=FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],)

@app.get("/")
async def root():
    return {"message": "Welcome to the Medical Chatbot API. Use the /chat endpoint to interact with the chatbot."}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat")
async def chat_endpoint(user_input: str, thread_id: int = 1):
    state={"messages":[HumanMessage(content=user_input)]}
    config = {"configurable": {"thread_id": thread_id}}
    graph_app = builder.compile(checkpointer=app.state.checkpointer)
    return StreamingResponse(stream_app_output(graph_app,state,config), media_type="application/event-stream")


