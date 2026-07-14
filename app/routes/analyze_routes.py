from flask import request
from app.routes import analyze_bp
from app.services.gemini_service import gemini_service, GeminiAPIError
from app.utils.response import error_response, success_response
from app.utils.auth import login_required
from app.models import db, AnalysisRecord

@analyze_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_text():
    if not request.is_json:
        return error_response('Invalid JSON format', 400)
        
    data = request.json
    text = data.get('text')
    
    if not text or not str(text).strip():
        return error_response('Please provide complaint text to analyze', 400)

    try:
        import re
        # 取得分析結果
        result_text = gemini_service.analyze_sentiment(text)
        
        # 嘗試解析分數和標籤以及其他欄位
        score = None
        label = None
        appeal = None
        reply = None
        
        score_match = re.search(r'情緒分數[：:]\s*([^\n]+)', result_text)
        if score_match: score = score_match.group(1).strip()
            
        label_match = re.search(r'情緒標籤[：:]\s*([^\n]+)', result_text)
        if label_match: label = label_match.group(1).strip()
        
        appeal_match = re.search(r'關鍵訴求[：:]\s*([^\n]+)', result_text)
        if appeal_match: appeal = appeal_match.group(1).strip()
        
        reply_match = re.search(r'建議回覆[：:]\s*([^\n]+)', result_text)
        if reply_match: reply = reply_match.group(1).strip()

        # Generate a timestamp similar to what is seen in the user's SSMS (e.g., mm:ss.f format of current time)
        from datetime import datetime
        now = datetime.now()
        analysis_time_str = f"{now.minute:02d}:{now.second:02d}.{now.microsecond // 100000}"

        # 寫入 SSMS 資料庫中新建的 analysis_records 資料表
        new_record = AnalysisRecord(
            text_input=text, 
            emotion_score=score,
            emotion_label=label,
            key_appeal=appeal,
            suggested_reply=reply,
            analysis_result=analysis_time_str
        )
        db.session.add(new_record)
        db.session.commit()
        
        return success_response({'result': result_text, 'id': new_record.id})
    except GeminiAPIError as e:
        return error_response(str(e), 503)
    except Exception as e:
        return error_response(f'An unexpected error occurred: {str(e)}', 500)

@analyze_bp.route('/analyze/history', methods=['GET'])
@login_required
def get_analyze_history():
    try:
        records = AnalysisRecord.query.order_by(AnalysisRecord.created_at.desc()).all()
        return success_response([record.to_dict() for record in records])
    except Exception as e:
        return error_response('Failed to fetch analysis history', 500)

@analyze_bp.route('/analyze/<int:record_id>', methods=['DELETE'])
@login_required
def delete_analyze_record(record_id):
    try:
        record = AnalysisRecord.query.get(record_id)
        if not record:
            return error_response('Record not found', 404)
        db.session.delete(record)
        db.session.commit()
        return success_response({'message': 'Record deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to delete record', 500)

@analyze_bp.route('/analyze/<int:id>/chat', methods=['POST'])
@login_required
def chat_with_analysis(id):
    if not request.is_json:
        return error_response('Invalid JSON format', 400)
        
    data = request.json
    message = data.get('message')
    if not message or not str(message).strip():
        return error_response('Please provide a message', 400)
        
    record = AnalysisRecord.query.get(id)
    if not record:
        return error_response('Analysis record not found', 404)
        
    import json
    try:
        history = json.loads(record.chat_history) if record.chat_history else []
    except:
        history = []
        
    # Build original analysis text
    analysis_text = f"情緒分數：{record.emotion_score}\n情緒標籤：{record.emotion_label}\n關鍵訴求：{record.key_appeal}\n建議回覆：{record.suggested_reply}"
    
    # Call Gemini
    response_text = gemini_service.analyze_chat(record.text_input, analysis_text, history, message)
    
    # Update history
    history.append({'role': 'user', 'content': message})
    history.append({'role': 'ai', 'content': response_text})
    record.chat_history = json.dumps(history, ensure_ascii=False)
    db.session.commit()
    
    return success_response({'response': response_text, 'history': history})
