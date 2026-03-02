from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from agent.graph_builder import builder
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from contextlib import asynccontextmanager
from utils import stream_app_output,get_answer



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSqliteSaver.from_conn_string("./medical_chatbot.db") as checkpointer:
        await checkpointer.setup()
        app.state.checkpointer = checkpointer
        app.state.graph = builder.compile(checkpointer=checkpointer)
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

@app.get("/checkpoints")
async def get_checkpoints():
    """Fetches list of available thread IDs from the checkpointer."""
    
    conn = app.state.checkpointer.conn
    async with conn.execute("SELECT thread_id FROM checkpoints") as cursor:
        rows = await cursor.fetchall()
        
        return {"threads": list(set(row[0] for row in rows))}

@app.post("/chat/stream")
async def chat_stream(user_input: str, thread_id: int = 1):
    state={"query":user_input}
    config = {"configurable": {"thread_id": thread_id}}
    graph_app = app.state.graph
    return StreamingResponse(stream_app_output(graph_app,state,config), media_type="application/event-stream")

@app.post("/chat")
async def chat(user_input: str, thread_id: int = 1):
    state={"query":user_input}
    config = {"configurable": {"thread_id": thread_id}}
    graph_app = app.state.graph
    output=await get_answer(graph_app,state,config)
    return {"response": output}

@app.get("/history")
async def get_history(thread_id: int = 1):
    """Fetches full chat history for a given thread."""
    config = {"configurable": {"thread_id": thread_id}}
    
    
    checkpoint_tuple = await app.state.checkpointer.aget_tuple(config)
    
    if not checkpoint_tuple:
        return {"messages": []}
    
    messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
    formated_messages = [{"type": message.type, "content": message.content} 
                     for message in messages
                     if message.type in ['human', 'ai']
                     and message.content.strip() != ""]
    
        
    return {"messages": formated_messages}