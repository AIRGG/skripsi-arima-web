from fastapi import Request
async def check_user_login(request: Request):
    if request.session.get('token') and request.session.get('refresh_token'):
        return True
    request.session.clear()
    return False