from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash
import getpass
import sys

def reset_admin_password():
    app = create_app()
    with app.app_context():
        # Find the superadmin user (usually username='admin')
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("錯誤：找不到 'admin' 帳號。")
            sys.exit(1)
            
        print("--- 超級管理員密碼重設工具 ---")
        print("此工具將重設 'admin' 帳號的密碼。")
        
        new_password = getpass.getpass("請輸入新的密碼 (不顯示字元): ")
        confirm_password = getpass.getpass("請再次輸入密碼確認: ")
        
        if new_password != confirm_password:
            print("錯誤：兩次輸入的密碼不一致，重設失敗。")
            sys.exit(1)
            
        if not new_password:
            print("錯誤：密碼不能為空。")
            sys.exit(1)
            
        admin_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        print("\n成功：'admin' 的密碼已重設完畢！您可以回到網頁重新登入了。")

if __name__ == '__main__':
    reset_admin_password()
