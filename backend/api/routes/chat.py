from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from services.chat_service import ChatService
from services.auth_service import AuthService
from services.database_service import DatabaseService
from ai_agents.chatbot import get_chat_response
from fastapi.responses import StreamingResponse
import json
import logging

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    window_id: str

async def setup_auth_session(request: Request):
    try:
        user_id = await AuthService.validate_user(request)
        access_token, refresh_token = await AuthService.get_tokens_from_request(request)
        await DatabaseService.set_auth_session(access_token, refresh_token)
        return user_id
    except Exception as e:
        logging.error(f"Auth setup error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.post("")
async def chat(request: Request, chat_request: ChatRequest):
    try:
        user_id = await setup_auth_session(request)
        window_id = chat_request.window_id
        
        async def generate():
            async for token in get_chat_response(user_id, chat_request.message, window_id):
                yield f"data: {json.dumps({'token': token})}\n\n"
                
        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        logging.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/window/create")
async def create_chat_window(request: Request):
    try:
        user_id = await setup_auth_session(request)
        window = await ChatService.create_chat_window(user_id)
        return window
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/windows")
async def get_chat_windows(request: Request):
    try:
        user_id = await setup_auth_session(request)
        windows = await ChatService.get_chat_windows(user_id)
        return windows
    except Exception as e:
        logging.error(f"Error getting chat windows: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{window_id}")
async def get_chat_history(window_id: str, request: Request):
    try:
        user_id = await setup_auth_session(request)
        history = await ChatService.get_chat_history(user_id, window_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/window/{window_id}")
async def delete_chat_window(window_id: str, request: Request):
    try:
        user_id = await setup_auth_session(request)
        success = await ChatService.delete_window(user_id, window_id)
        if success:
            return {"message": "Chat window deleted successfully"}
        raise HTTPException(status_code=404, detail="Chat window not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/window/{window_id}/rename")
async def rename_chat_window(window_id: str, request: Request, data: dict):
    try:
        user_id = await setup_auth_session(request)
        new_title = data.get("title")
        if not new_title:
            raise HTTPException(status_code=400, detail="Title is required")
        success = await ChatService.rename_window(user_id, window_id, new_title)
        if success:
            return {"message": "Chat window renamed successfully"}
        raise HTTPException(status_code=404, detail="Chat window not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
