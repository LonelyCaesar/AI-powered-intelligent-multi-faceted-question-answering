from typing import List, Dict, Any
from app.models import db, Complaint

class ComplaintService:
    
    @staticmethod
    def get_all_complaints(user_id: int = None) -> List[Dict[str, Any]]:
        query = Complaint.query
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        complaints = query.order_by(Complaint.created_at.desc()).all()
        return [c.to_dict() for c in complaints]
        
    @staticmethod
    def create_complaint(content: str, image_path: str = None, customer_name: str = None, account: str = None, department: str = None, email: str = None, user_id: int = None) -> Complaint:
        if not content or not content.strip():
            raise ValueError("Complaint content cannot be empty.")
        new_complaint = Complaint(
            content=content.strip(), 
            image_path=image_path,
            customer_name=customer_name,
            account=account,
            department=department,
            email=email,
            user_id=user_id
        )
        db.session.add(new_complaint)
        db.session.commit()
        return new_complaint
        
    @staticmethod
    def delete_complaint(complaint_id: int) -> bool:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False
        db.session.delete(complaint)
        db.session.commit()
        return True
        
    @staticmethod
    def reply_complaint(complaint_id: int, reply_text: str, sender_name: str = 'Admin') -> bool:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False
            
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        formatted_reply = f"[{timestamp}] {sender_name}: {reply_text}"
        
        if complaint.admin_reply:
            complaint.admin_reply += f"\n\n{formatted_reply}"
        else:
            complaint.admin_reply = formatted_reply
            
        db.session.commit()
        return True
        
    @staticmethod
    def resolve_complaint(complaint_id: int) -> bool:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False
        complaint.status = 'resolved'
        db.session.commit()
        return True
        
    @staticmethod
    def get_statistics(user_id: int = None) -> Dict[str, int]:
        query = Complaint.query
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
            
        total = query.count()
        pending = query.filter_by(status='pending').count()
        resolved = query.filter_by(status='resolved').count()
        return {
            'total': total,
            'pending': pending,
            'resolved': resolved
        }
