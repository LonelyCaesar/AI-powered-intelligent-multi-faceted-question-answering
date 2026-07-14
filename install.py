import subprocess
import sys

def run_script(script_name, description):
    print(f"\n[📦 正在執行] {description} ({script_name})...")
    try:
        # Run the script and capture the output
        result = subprocess.run([sys.executable, script_name], check=True, text=True)
        print(f"✅ {description} 完成！")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗！請檢查錯誤訊息。")
        sys.exit(1)

def install():
    print("="*50)
    print("🚀 AI 客訴系統 - 一鍵安裝與初始化 (類似 npm install)")
    print("="*50)
    
    # 1. 初始化資料庫與預設帳號
    run_script("setup_user.py", "初始化資料庫與 admin 帳號")
    
    # 2. 下載本地 AI 解析模型 (確保後續能離線執行)
    run_script("download_model.py", "下載本地 RAG 嵌入模型")
    
    print("\n" + "="*50)
    print("🎉 所有安裝步驟已完成！系統已準備就緒。")
    print("👉 接下來請輸入： py run.py  (這就像 npm run dev 一樣)")
    print("="*50)

if __name__ == "__main__":
    install()
