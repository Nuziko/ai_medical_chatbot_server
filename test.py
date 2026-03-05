from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from agent.graph_builder import builder
from rich import print

from dotenv import load_dotenv
import utils
load_dotenv()  


config = {"configurable": {"thread_id":156}}
state={"query":"how many patient died with covid-19 in algeria "}
async def stream_chat():
    async with AsyncSqliteSaver.from_conn_string("./medical_chatbot.db") as checkpointer:
        app=builder.compile(checkpointer=checkpointer)
        async for output in app.astream(state,config=config):
            if output.get('brain'):
                print(f"[bold bright_green ] Brain is active [bold bright_green ]")
            if output.get('web search'):
                print(f"[bold bright_blue ] Do a web search [bold bright_blue ]")
            if output.get('patient lookup'):
                print(f"[bold bright_blue ] Looking for patients [bold bright_blue ]")
            if output.get('summarize'):
                print(f"[bold bright_magenta ] New Summary: {output['summarize']['summary']} [bold bright_magenta ]")
            if output.get('helper tools'):
                print(f"[bold bright_cyan ] Using Helper Tools [bold bright_cyan ]")
            if output.get('guard'):
                print(f"[bold bright_red ] Guard Decision: {output['guard']['safety_status']} [bold bright_red ]")
            if output.get('final answer'):
                print(f"[bold bright_green ] Final Answer: {output['final answer']['answer']} [bold bright_green ]")
        #async for output in utils.stream_app_output(app,state,config):
        # print(output)
        
async def normal_chat():
    async with AsyncSqliteSaver.from_conn_string("./medical_chatbot.db") as checkpointer:
        app=builder.compile(checkpointer=checkpointer)
        result =await  utils.get_answer(app,state,config)
        print(result)
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(stream_chat())
    #asyncio.run(normal_chat())
    