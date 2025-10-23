from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

app = FastAPI(title="Agent HTTP Wrapper")

class AgentRequest(BaseModel):
    user_id: str
    payload: Dict[str, Any]

@app.post("/")
async def handle_agent(req: AgentRequest):
    # Simple wrapper: if you have a local ZMQ agent, you can forward the payload there.
    # For now, we will simulate by returning a canned response or echoing back.
    workflow_json = req.payload.get('workflow_json')
    nlp_data = req.payload.get('nlp_data')

    # TODO: integrate with actual agent (ZMQ RPC or direct call)
    bot_response = {
        "response": "(Agent) Tôi đã nhận: '" + (nlp_data.get('text') or '') + "'",
        "action": "continue"
    }

    return bot_response

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=4242)
