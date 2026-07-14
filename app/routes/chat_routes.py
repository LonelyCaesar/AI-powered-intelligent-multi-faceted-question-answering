import uuid
from flask import request
from app.routes import chat_bp
from app.services.gemini_service import gemini_service, GeminiAPIError
from app.services.data_analyzer_service import data_analyzer_service
from app.utils.response import error_response, success_response
from app.utils.auth import login_required
from app.models import db, ChatRecord
from sqlalchemy import func

@chat_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    if request.is_json:
        user_message = request.json.get('message')
        session_id = request.json.get('session_id')
        chat_file = None
    else:
        user_message = request.form.get('message')
        session_id = request.form.get('session_id')
        chat_file = request.files.get('file')
        
    if not session_id:
        session_id = str(uuid.uuid4())
    
    if not user_message or not str(user_message).strip():
        return error_response('Message cannot be empty', 400)

    file_path = None
    full_path = None
    if chat_file and chat_file.filename:
        import os
        from werkzeug.utils import secure_filename
        from flask import current_app
        upload_folder = os.path.join(current_app.static_folder, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filename = secure_filename(chat_file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        full_path = os.path.join(upload_folder, unique_filename)
        chat_file.save(full_path)
        file_path = f"/static/uploads/{unique_filename}"

    try:
        # 1. 取得 AI 的回覆內容與建議問題 (整合 RAG 與數據分析功能)
        if full_path:
            ext = full_path.lower().split('.')[-1]
            if ext in ['pdf', 'txt']:
                ai_result = gemini_service.generate_rag_response(user_message, full_path)
            elif ext in ['csv', 'xls', 'xlsx']:
                ai_result = data_analyzer_service.analyze_csv(full_path, user_message)
            else:
                ai_result = gemini_service.generate_chat_response(user_message)
        else:
            ai_result = gemini_service.generate_chat_response(user_message)
            
        response_text = ai_result.get('response', '')
        suggestions = ai_result.get('suggestions', [])
        
        # 2. 將問答紀錄獨立寫入 SSMS 資料庫的 chat_records 資料表
        new_chat = ChatRecord(session_id=session_id, user_message=user_message, ai_response=response_text, file_path=file_path)
        db.session.add(new_chat)
        db.session.commit()
        
        return success_response({'response': response_text, 'session_id': session_id, 'suggestions': suggestions})
    except GeminiAPIError as e:
        return error_response(str(e), 503) # Service Unavailable
    except Exception as e:
        # Avoid leaking full raw exception details in production
        return error_response('An unexpected error occurred while processing the chat.', 500)

@chat_bp.route('/chat/sessions', methods=['GET'])
@login_required
def get_chat_sessions():
    try:
        # 取得不重複的 session_id，並用每個 session_id 第一筆紀錄的 user_message 當作 title
        # 使用 subquery 來找到每個 session_id 的第一筆紀錄的 id
        subquery = db.session.query(func.min(ChatRecord.id).label('min_id')).group_by(ChatRecord.session_id).subquery()
        first_records = db.session.query(ChatRecord).join(subquery, ChatRecord.id == subquery.c.min_id).order_by(ChatRecord.created_at.desc()).all()
        
        sessions = []
        for record in first_records:
            title = record.user_message[:30] + '...' if len(record.user_message) > 30 else record.user_message
            sessions.append({
                'session_id': record.session_id,
                'title': title,
                'timestamp': record.created_at.strftime('%Y-%m-%d %H:%M')
            })
            
        return success_response(sessions)
    except Exception as e:
        return error_response('Failed to fetch chat sessions', 500)

@chat_bp.route('/chat/sessions/<session_id>', methods=['GET'])
@login_required
def get_chat_session(session_id):
    try:
        if session_id in ['null', 'None']:
            records = ChatRecord.query.filter(ChatRecord.session_id.is_(None)).order_by(ChatRecord.created_at.asc()).all()
        else:
            records = ChatRecord.query.filter_by(session_id=session_id).order_by(ChatRecord.created_at.asc()).all()
        return success_response([record.to_dict() for record in records])
    except Exception as e:
        return error_response('Failed to fetch chat session', 500)

@chat_bp.route('/chat/sessions/<session_id>', methods=['DELETE'])
@login_required
def delete_chat_session(session_id):
    try:
        if session_id in ['null', 'None']:
            ChatRecord.query.filter(ChatRecord.session_id.is_(None)).delete(synchronize_session=False)
        else:
            ChatRecord.query.filter_by(session_id=session_id).delete(synchronize_session=False)
        db.session.commit()
        return success_response({'message': 'Session deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete chat session: {str(e)}', 500)
