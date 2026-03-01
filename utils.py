import json


async def stream_app_output(app,input,config):
    async for output in app.astream(input,config=config):
        if output.get('web search'):
            result = json.loads(output['web search']['messages'][-1].content)
            query = result.get('query')
            urls = [res['url'] for res in result.get('results',[])]
            yield f"data: {json.dumps({'type':'web_search_output','query':query,'urls':urls})}\n"
        if output.get('guard'):
            yield f"data: {json.dumps({'type':'guard_output','content':output['guard']['safety_status']})}\n"
        if output.get('final answer'):
            yield f"data: {json.dumps({'type':'final_answer','content':output['final answer']['answer']})}\n"