import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from google import genai  # 👈 ✨ 換成全新一代的 SDK 引入方式

# 1. 初始化與環境變數載入
load_dotenv(override=True)
app = Flask(__name__)

# 2. 資料庫配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///complaints.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 3. 初始化全新 Gemini Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("⚠️ 警告：未偵測到 GEMINI_API_KEY，請檢查 .env 檔案")
client = genai.Client(api_key=api_key)  # 👈 ✨ 新版的連線寫法

# 4. 資料庫模型定義 (Schema)
class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='pending')
    admin_reply = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'status': self.status,
            'admin_reply': self.admin_reply
        }

with app.app_context():
    db.create_all()

# ================= 路由與 API 實作 =================

@app.route('/')
def index():
    return render_template('index.html')

# [模組 A] AI 輿情分析 API
@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    data = request.json
    text = data.get('text')
    if not text:
        return jsonify({'error': '請輸入客訴文字'}), 400

    try:
        prompt = f"""
        你是一位資深客服數據分析師。請分析以下客訴內容：
        "{text}"
        
        請嚴格依照以下格式回傳結果 (Plain Text Only，不要使用 Markdown 語法)：
        情緒分數：(1-10分，10為最憤怒)
        情緒標籤：(例如：憤怒、失望、焦慮、平靜)
        關鍵訴求：(一句話摘要)
        建議回覆：(50字以內的專業安撫回覆)
        """
        # 👈 ✨ 使用新版 API 呼叫方式，並換上最新的 2.5 版模型
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return jsonify({'result': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# [模組 B] 工單 CRUD 管理 (維持不變)
@app.route('/api/complaints', methods=['GET', 'POST'])
def handle_complaints():
    if request.method == 'POST':
        data = request.json
        content = data.get('content')
        if not content: return jsonify({'error': '內容不能為空'}), 400
        new_complaint = Complaint(content=content)
        db.session.add(new_complaint)
        db.session.commit()
        return jsonify({'message': '工單建立成功', 'id': new_complaint.id}), 201
    else:
        complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
        return jsonify([c.to_dict() for c in complaints])

@app.route('/api/complaints/<int:id>', methods=['DELETE'])
def delete_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    db.session.delete(complaint)
    db.session.commit()
    return jsonify({'message': '工單已刪除'})

@app.route('/api/complaints/<int:id>/reply', methods=['POST'])
def reply_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    complaint.admin_reply = request.json.get('reply', '')
    complaint.status = 'resolved'
    db.session.commit()
    return jsonify({'message': '已回覆並結案'})

# [模組 C] 儀表板數據統計 (維持不變)
@app.route('/api/stats', methods=['GET'])
def get_stats():
    total = Complaint.query.count()
    pending = Complaint.query.filter_by(status='pending').count()
    resolved = Complaint.query.filter_by(status='resolved').count()
    return jsonify({'total': total, 'pending': pending, 'resolved': resolved})

# [模組 D] 智能助手 Chat API
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message: return jsonify({'error': '訊息不能為空'}), 400

    try:
        # 👈 ✨ 使用新版 API 呼叫方式
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message
        )
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)