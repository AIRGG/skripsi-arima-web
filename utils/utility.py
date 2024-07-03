from fastapi import Request
async def check_user_login(request: Request):
    if request.session.get('token') and request.session.get('refresh_token'):
        return True
    request.session.clear()
    return False

async def convert_uuid(idnya):
    # 1261be20-40c3-11ee-8c68-d371b81349fd -> 1ee40c31261be208c68d371b81349fd
    parts = idnya.split("-")
    back = f'{parts[0]}{"".join(parts[3:])}'
    front = f'{"".join(parts[2][1:])}{parts[1]}'
    return front + back