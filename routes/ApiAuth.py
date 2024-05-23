from routes.imports import *

routes_auth = APIRouter()
# schema_device = sqlalchemy_to_pydantic(TblDevice)
class response_login(BaseModel):
    token: str = ''
    refreshToken: str = ''

@routes_auth.post("/login", response_class=RedirectResponse)
async def process_login(
    request: Request,
    response: Response
):
    http: httpx = request.state.httpx

    form = await request.form()
    print(form)

    hit_login = None
    url = f"{os.getenv('endpoint_gateway_iot')}/auth/login"
    with suppress(httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError): # handle error kalo kena tanpa try catch
        hit_login: httpx.Response = await http.post(url, json={
            "username": form.get('email'),
            "password": form.get('password')
        })
    if hit_login == None:
        request.session.clear()
        return RedirectResponse(f"/login?status=gagal_konek&email={form.get('email')}", status_code=HttpStatus.HTTP_303_SEE_OTHER)

    if(hit_login.status_code == 401):
        request.session.clear()
        return RedirectResponse(f"/login?status=gagal_login&email={form.get('email')}", status_code=HttpStatus.HTTP_303_SEE_OTHER)
    print(type(hit_login.text))
    resp_login = json.loads(hit_login.text)
    print(resp_login)

    token = resp_login.get('token', None)
    refresh_token = resp_login.get('refreshToken', None)
    user_identity = jwt.decode(token, options={"verify_signature": False})
    print(user_identity)

    # url = f"{os.getenv('endpoint_gateway_iot')}/user/{user_identity['id']['id']}"
    # hit_identity: httpx.Response = await http.get(url, headers={
    #     'X-Authorization', f'Bearer {token}'
    # })

    request.session.clear()
    request.session["identity"] = user_identity
    request.session["token"] = token
    request.session["refresh_token"] = refresh_token
    # response.set_cookie(key='token', value=resp.get('token', None))
    # response.set_cookie(key='refresh_token', value=resp.get('refreshToken', None))
    return RedirectResponse('/', status_code=HttpStatus.HTTP_303_SEE_OTHER)

@routes_auth.get("/logout", response_class=RedirectResponse)
async def process_logout(
    request: Request,
):
    request.session.clear()
    return RedirectResponse('/login?status=success_logout', status_code=HttpStatus.HTTP_303_SEE_OTHER)