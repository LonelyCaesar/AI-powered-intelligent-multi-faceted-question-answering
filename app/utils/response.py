from flask import jsonify

def success_response(data=None, message="Success", status_code=200):
    """
    Standardize success responses.
    """
    response = {
        "status": "success",
        "message": message
    }
    if data is not None:
        # If data is a dictionary containing a specific format, we might unpack it or return it directly.
        # To maintain compatibility with existing frontend, we'll return data directly if it's already formatted,
        # or merge it. For exact compatibility, some endpoints expect raw lists or dicts.
        pass
    
    # We will adjust this to be flexible but structured.
    return jsonify(data), status_code

def error_response(message="An error occurred", status_code=400):
    """
    Standardize error responses.
    """
    return jsonify({"error": message}), status_code
