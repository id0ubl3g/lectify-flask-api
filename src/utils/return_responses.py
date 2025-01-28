def create_success_return_response(message: str = None, data: str = None) -> dict:
    response = {
        'message': message,
        'data': data
    }
    return response

def create_error_return_response(message:str = None, data: str = None) -> dict:
    response = {
        'message': message,
        'data': data
    }
    return response