import os
from werkzeug.utils import secure_filename
from flask import request, current_app, session
from app.routes import complaint_bp
from app.services.complaint_service import ComplaintService
from app.utils.response import error_response, success_response
from app.utils.auth import login_required

@complaint_bp.route('/complaints', methods=['GET'])
@login_required
def get_complaints():
    user_id = session.get('user_id') if session.get('role') == 'member' else None
    complaints = ComplaintService.get_all_complaints(user_id=user_id)
    return success_response(complaints)

@complaint_bp.route('/complaints', methods=['POST'])
@login_required
def create_complaint():
    if request.is_json:
        content = request.json.get('content')
        customer_name = request.json.get('customer_name') or None
        account = request.json.get('account') or None
        department = request.json.get('department') or None
        email = request.json.get('email') or None
        image_path = None
    else:
        content = request.form.get('content')
        customer_name = request.form.get('customer_name') or None
        account = request.form.get('account') or None
        department = request.form.get('department') or None
        email = request.form.get('email') or None
        image_file = request.files.get('image')
        image_path = None
        
        if image_file and image_file.filename:
            # Ensure upload directory exists
            upload_folder = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            filename = secure_filename(image_file.filename)
            # Add a unique prefix to avoid overwriting
            import uuid
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(upload_folder, unique_filename)
            image_file.save(file_path)
            
            # Save relative path for frontend access
            image_path = f"/static/uploads/{unique_filename}"
            
    try:
        target_user_id = None
        if request.is_json:
            target_user_id = request.json.get('user_id')
        else:
            target_user_id = request.form.get('user_id')
                
        user_id = target_user_id if target_user_id else None
        
        if not user_id and session.get('role') == 'member':
            user_id = session.get('user_id')
        
        new_complaint = ComplaintService.create_complaint(
            content=content, 
            image_path=image_path,
            customer_name=customer_name,
            account=account,
            department=department,
            email=email,
            user_id=user_id
        )
        return success_response({'message': 'Complaint ticket created successfully', 'id': new_complaint.id}, status_code=201)
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f'Failed to create complaint ticket: {str(e)}', 500)

@complaint_bp.route('/complaints/<int:id>', methods=['DELETE'])
@login_required
def delete_complaint(id):
    success = ComplaintService.delete_complaint(id)
    if success:
        return success_response({'message': 'Complaint ticket deleted successfully'})
    return error_response('Complaint ticket not found', 404)

@complaint_bp.route('/complaints/<int:id>/reply', methods=['POST'])
@login_required
def reply_complaint(id):
    if not request.is_json:
        return error_response('Invalid JSON format', 400)
        
    reply_text = request.json.get('reply', '')
    
    sender_name = 'Admin'
    if session.get('role') == 'member':
        sender_name = session.get('name', session.get('username', 'Customer'))
    elif session.get('role') in ['admin', 'superadmin']:
        sender_name = session.get('name') or session.get('username', 'Admin')
        
    success = ComplaintService.reply_complaint(id, reply_text, sender_name)
    
    if success:
        return success_response({'message': 'Replied successfully'})
    return error_response('Complaint ticket not found', 404)

@complaint_bp.route('/complaints/<int:id>/resolve', methods=['POST'])
@login_required
def resolve_complaint(id):
    success = ComplaintService.resolve_complaint(id)
    if success:
        return success_response({'message': 'Complaint marked as resolved'})
    return error_response('Complaint ticket not found', 404)

@complaint_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    user_id = session.get('user_id') if session.get('role') == 'member' else None
    stats = ComplaintService.get_statistics(user_id=user_id)
    return success_response(stats)

@complaint_bp.route('/complaints/refine', methods=['POST'])
@login_required
def refine_complaint():
    if not request.is_json:
        return error_response('Invalid JSON format', 400)
    text = request.json.get('text')
    if not text:
        return error_response('Text is required', 400)
    
    from app.services.gemini_service import gemini_service
    refined_text = gemini_service.refine_complaint_text(text)
    return success_response({'refined_text': refined_text})

@complaint_bp.route('/complaints/refine_reply', methods=['POST'])
@login_required
def refine_reply():
    if not request.is_json:
        return error_response('Invalid JSON format', 400)
    original_complaint = request.json.get('original_complaint')
    draft_reply = request.json.get('draft_reply')
    if not draft_reply or not original_complaint:
        return error_response('Original complaint and draft reply are required', 400)
    
    from app.services.gemini_service import gemini_service
    refined_text = gemini_service.refine_reply_text(original_complaint, draft_reply)
    return success_response({'refined_text': refined_text})
