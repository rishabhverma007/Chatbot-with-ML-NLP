import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file at startup
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.agent.graph import AgentStateGraph

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChatbotBackend")

app = FastAPI(
    title="Next-Gen 3D Agentic RAG Chatbot Platform",
    description="Asynchronous FastAPI service running a LangGraph-style agent loop with real-time WebSocket streaming.",
    version="1.0.0"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise Agent state graph
agent_graph = AgentStateGraph()

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Next-Gen Agentic RAG Platform Backend",
        "endpoints": {
            "root": "/",
            "websocket": "/chat"
        }
    }

@app.websocket("/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established with client.")
    
    try:
        while True:
            # Wait for text data from the client
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                user_message = payload.get("message", "").strip()
                user_mode = payload.get("mode", None)
            except json.JSONDecodeError:
                user_message = data.strip()
                user_mode = None
                
            if not user_message:
                await websocket.send_json({
                    "type": "error",
                    "content": "Empty prompt received."
                })
                continue
                
            logger.info(f"Received query from client: {user_message} (Mode: {user_mode})")
            
            # Execute the state machine and stream nodes / tokens
            try:
                async for update in agent_graph.execute(user_message, mode=user_mode):
                    # Forward status or token packets directly to the client
                    await websocket.send_json(update)
            except Exception as e:
                logger.error(f"Error during agent graph execution: {str(e)}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "content": f"An error occurred during process execution: {str(e)}"
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket encounter connection error: {str(e)}")
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
