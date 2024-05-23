from routes.imports import *

routes_mainview = APIRouter()
# schema_device = sqlalchemy_to_pydantic(TblDevice)

@routes_mainview.get("/", response_class=HTMLResponse)
async def view_homepage(
    request: Request,
):
    if not await check_user_login(request): return RedirectResponse('/login?status=belum_login', status_code=HttpStatus.HTTP_303_SEE_OTHER)
    templates: Jinja2Templates = request.state.templates
    context = {
        'request': request,
    }
    context['data'] = [1,2,3,4,5]
    print(request.session)
    return templates.TemplateResponse(name="dashboard/index.html", context=context)

@routes_mainview.get("/login", response_class=HTMLResponse)
async def view_login(
    request: Request,
):
    templates: Jinja2Templates = request.state.templates
    context = {
        'request': request,
    }
    context['data'] = [1,2,3,4,5]
    return templates.TemplateResponse(name="login.html", context=context)


