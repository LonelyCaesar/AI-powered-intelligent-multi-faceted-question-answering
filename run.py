import os
import logging

# 模擬前端 npm run dev 的清爽體驗：強制離線模式並關閉所有模型載入的擾人訊息
os.environ['HF_HUB_OFFLINE'] = '1'                # 徹底斷開 HuggingFace 連線，確保百分百離線執行
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'  # 關閉 Loading weights 的進度條
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

# 關閉底層套件的 Info 級別日誌，只顯示 Error
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

from app import create_app

# 解決 Flask/Werkzeug 在 Windows 開發環境下，每次請求都會進行反向 DNS 查詢導致極度緩慢的問題
try:
    import werkzeug.serving
    werkzeug.serving.WSGIRequestHandler.address_string = lambda self: self.client_address[0]
except Exception:
    pass

# Get environment from FLASK_ENV, default to development
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    from waitress import serve
    import logging

    # 隱藏 waitress 內建的日誌 (包含警告與連線紀錄)
    logging.getLogger('waitress').setLevel(logging.ERROR)

    print("🚀 系統已啟動！")
    print("* Running on http://127.0.0.1:5000")
    print("* (生產級伺服器 Waitress 運作中，日誌已關閉以保持畫面整潔)")
    
    # 啟動生產級伺服器
    serve(app, host='0.0.0.0', port=5000, _quiet=True)
