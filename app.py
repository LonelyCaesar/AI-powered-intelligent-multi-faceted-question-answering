import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 初始化環境與配置
load_dotenv()
app = Flask(__name__)

# 資料庫配置 (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///complaints.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# AI 模型配置
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 2. 資料模型 (Schema Design)
class Complaint(db.Model):
    """
    工單資料模型
    status: 'pending' (待處理) | 'resolved' (已結案)
    """
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='pending') 
    admin_reply = db.Column(db.Text, nullable=True)

# 初始化資料庫
with app.app_context():
    db.create_all()

# 3. 路由視圖 (Routes)
@app.route('/')
def index():
    return render_template('index.html')

# --- 功能模組 A: AI 輿情分析 (Sentiment Analysis) ---
@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """
    [API] AI 輿情分析核心接口
    技術邏輯：接收非結構化文本 -> 構建結構化 Prompt -> Gemini 推論 -> 回傳 JSON
    """
    data = request.json
    text = data.get('text')
    if not text: return jsonify({'error': '請輸入文字'}), 400

    try:
        # Prompt Engineering: 使用 Role-Playing 與 One-Shot 技巧確保格式
        prompt = f"""
        你是一位資深客服數據分析師。請分析以下客訴內容：
        "{text}"
        
        請嚴格依照以下格式回傳結果 (Plain Text Only，不要 Markdown)：
        情緒分數：(1-10分，10為最憤怒)
        情緒標籤：(例如：憤怒、失望、焦慮、平靜)
        關鍵訴求：(一句話摘要)
        建議回覆：(50字以內的專業安撫回覆)
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return jsonify({'result': response.text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 功能模組 B: 客訴工單系統 (Ticketing CRUD) ---
@app.route('/api/complaints', methods=['GET', 'POST'])
def handle_complaints():
    if request.method == 'POST':
        # 提交新工單
        data = request.json
        content = data.get('content')
        if not content: return jsonify({'error': '內容不能為空'}), 400
        
        new_complaint = Complaint(content=content, status='pending')
        db.session.add(new_complaint)
        db.session.commit()
        return jsonify({'message': '提交成功'}), 201
    
    else: # GET
        # 獲取工單列表 (按時間倒序)
        complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
        output = [{
            'id': c.id,
            'content': c.content,
            'timestamp': c.created_at.strftime('%Y-%m-%d %H:%M'),
            'status': c.status,
            'admin_reply': c.admin_reply
        } for c in complaints]
        return jsonify(output)

@app.route('/api/complaints/<int:id>', methods=['DELETE'])
def delete_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    db.session.delete(complaint)
    db.session.commit()
    return jsonify({'message': '已刪除'})

@app.route('/api/complaints/<int:id>/reply', methods=['POST'])
def reply_complaint(id):
    """模擬管理員回覆並結案"""
    complaint = Complaint.query.get_or_404(id)
    data = request.json
    complaint.admin_reply = data.get('reply')
    complaint.status = 'resolved'
    db.session.commit()
    return jsonify({'message': '已回覆'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """提供儀表板所需的統計數據"""
    total = Complaint.query.count()
    pending = Complaint.query.filter_by(status='pending').count()
    resolved = Complaint.query.filter_by(status='resolved').count()
    return jsonify({'total': total, 'pending': pending, 'resolved': resolved})

# --- 功能模組 C: 一般 AI 聊天 ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message')
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(user_message)
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)