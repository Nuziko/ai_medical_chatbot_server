from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from agent.graph_builder import builder
from rich import print

from dotenv import load_dotenv
import utils
load_dotenv()  




config = {"configurable": {"thread_id":4}}
state={"query":"give me the age of the patient P-005?"}
async def stream_chat():
    async with AsyncSqliteSaver.from_conn_string("./medical_chatbot.db") as checkpointer:
        app=builder.compile(checkpointer=checkpointer)
        # async for output in app.astream(state,config=config):
        #     if output.get('brain'):
        #         print(f"[bold bright_green ] Brain Output: {output['brain']['messages'][-1].content} [bold bright_green ]")
        #     if output.get('web_search'):
        #         print(f"[bold bright_blue ] Web Search Result: {output['web_search']['messages'][-1].content} [bold bright_blue ]")
        #     if output.get('patient_lookup'):
        #         print(f"[bold bright_blue ] Patient Lookup Result: {output['patient_lookup']['messages'][-1].content} [bold bright_blue ]")
        #     if output.get('summarize'):
        #         print(f"[bold bright_magenta ] New Summary: {output['summarize']['summary']} [bold bright_magenta ]")
        #     if output.get('helper tools'):
        #         print(f"[bold bright_cyan ] Helper Tools Output: {output['helper tools']['messages'][-1].content} [bold bright_cyan ]")
        #     if output.get('guard'):
        #         print(f"[bold bright_red ] Guard Decision: {output['guard']} [bold bright_red ]")
        async for output in utils.stream_app_output(app,state,config):
         print(output)
        
async def normal_chat():
    async with AsyncSqliteSaver.from_conn_string("./medical_chatbot.db") as checkpointer:
        app=builder.compile(checkpointer=checkpointer)
        result =await  utils.get_answer(app,state,config)
        print(result)
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(stream_chat())
    #asyncio.run(normal_chat())
    