import json




async def stream_app_output(app,input,config):
    async for output in app.astream(input,config=config):
        if output.get('web search'):
            result = json.loads(output['web search']['messages'][-1].content)
            query = result.get('query')
            urls = [res['url'] for res in result.get('results',[])]
            yield f"{json.dumps({'step':'web search','query':query,'urls':urls})}\n"
        if output.get("patient lookup"):
            yield f"{json.dumps({'step':'patient lookup'})}\n"
        if output.get('helper tools'):
            yield f"{json.dumps({'step':'helper tools'})}\n"
        if output.get('guard'):
            yield f"{json.dumps({'step':'safety check','safety status':output['guard']['safety_status']})}\n"
        if output.get('final answer'):
            yield f"{json.dumps({'step':'answer written','answer':output['final answer']['answer']})}\n"


async def get_answer(app,input,config):
    output=await app.ainvoke(input,config=config)
    return output.get('answer',""),output.get('urls',[]),output.get("safety_status","safe")



    
