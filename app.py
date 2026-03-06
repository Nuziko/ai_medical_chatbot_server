from fastapi import FastAPI,UploadFile,File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from agent.graph_builder import builder
from agent.utils import transcript
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from contextlib import asynccontextmanager
from utils import stream_app_output,get_answer
from type import ChatRequest, ChatResponse,ThreadListResponse,HistoryResponse,TranscriptionResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSqliteSaver.from_conn_string("./medical_chatbot.db") as checkpointer:
        await checkpointer.setup()
        await checkpointer.conn.execute("""CREATE TABLE IF NOT EXISTS threads (
            thread_id TEXT PRIMARY KEY,
            thread_name TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        app.state.checkpointer = checkpointer
        app.state.graph = builder.compile(checkpointer=checkpointer)
        yield   

app=FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],)

async def insert_thread(thread_id: str, thread_name: str, app: FastAPI):
    """Inserts a new thread into the database."""

    conn = app.state.checkpointer.conn
    await conn.execute("INSERT OR IGNORE INTO threads (thread_id, thread_name) VALUES (?, ?)", (thread_id, thread_name))
    await conn.commit()

@app.get("/")
async def root():
    return {"message": "Welcome to the Medical Chatbot API. Use the /chat endpoint to interact with the chatbot."}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/checkpoints", response_model=ThreadListResponse)
async def get_checkpoints():
    """Fetches list of available thread IDs from the checkpointer."""
    
    conn = app.state.checkpointer.conn
    async with conn.execute("SELECT distinct thread_id, thread_name FROM threads") as cursor:
        rows = await cursor.fetchall()
        print(f"Fetched threads from DB: {rows}")
        return ThreadListResponse(threads=list({"thread_id": row[0], "thread_name": row[1]} for row in rows))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    await insert_thread(request.thread_id, request.user_input, app)  
    state={"query":request.user_input}
    config = {"configurable": {"thread_id": request.thread_id}}
    graph_app = app.state.graph
    return StreamingResponse(stream_app_output(graph_app,state,config), media_type="application/event-stream")

@app.post("/chat",response_model=ChatResponse)
async def chat(request: ChatRequest):
    await insert_thread(request.thread_id, request.user_input, app)  
    state={"query":request.user_input}
    config = {"configurable": {"thread_id": request.thread_id}}
    graph_app = app.state.graph
    try:
        output, urls = await get_answer(graph_app,state,config)
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return ChatResponse(success=False, error="Something went wrong while processing the request.")
    return ChatResponse(success=True, response=output, urls=urls)

@app.get("/history", response_model=HistoryResponse)
async def get_history(thread_id: str = None):
    """Fetches full chat history for a given thread."""
    config = {"configurable": {"thread_id": thread_id}}
    
    
    checkpoint_tuple = await app.state.checkpointer.aget_tuple(config)
    
    if not checkpoint_tuple:
        return HistoryResponse(messages=[])
    
    messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
    formated_messages = [{"type": message.type, "content": message.content} 
                     for message in messages
                     if message.type in ['human', 'ai']
                     and message.content.strip() != ""]
    
        
    return HistoryResponse(messages=formated_messages)


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile=File(...)):
    content = await file.read()
    transcription = transcript(file_name=file.filename,file_bytes=content)
    if transcription is None:
        return TranscriptionResponse(error="Transcription failed. Please try again.")
    return TranscriptionResponse(transcription=transcription)