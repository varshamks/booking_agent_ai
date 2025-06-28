# import uvicorn
# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def root():
#     return {"message": "AI Booking Agent Backend Running ✅"}

# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)


# from fastapi import FastAPI, Request
# from pydantic import BaseModel
# from agent.langgraph_agent import app

# class UserInput(BaseModel):
#     user_input: str

# fast_app = FastAPI()

# @fast_app.post("/chat")
# async def chat(data: UserInput):
#     response = app(data.user_input)
#     return {"response": response}








from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent.langgraph_agent import app
import uvicorn

class UserInput(BaseModel):
    user_input: str

class ChatResponse(BaseModel):
    response: str
    status: str = "success"

fast_app = FastAPI(
    title="AI Booking Agent API",
    description="API for AI-powered calendar booking assistant",
    version="1.0.0"
)

# Add CORS middleware
fast_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@fast_app.get("/")
async def root():
    return {
        "message": "AI Booking Agent API is running!",
        "endpoints": {
            "/chat": "POST - Send chat messages to the booking agent",
            "/health": "GET - Check API health status"
        }
    }

@fast_app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Booking Agent"}

@fast_app.post("/chat", response_model=ChatResponse)
async def chat(data: UserInput):
    try:
        response = app(data.user_input)
        return ChatResponse(response=response, status="success")
    except Exception as e:
        return ChatResponse(
            response=f"Sorry, I encountered an error: {str(e)}. Please try again.",
            status="error"
        )

@fast_app.post("/reset")
async def reset_conversation():
    """Reset the conversation state"""
    from agent.langgraph_agent import reset_conversation_state
    reset_conversation_state()
    return {"message": "Conversation state reset successfully"}

if __name__ == "__main__":
    uvicorn.run(fast_app, host="0.0.0.0", port=8000)
