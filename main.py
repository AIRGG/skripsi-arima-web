from sqlalchemy.orm import close_all_sessions
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

import uvicorn, requests, json,time, traceback, os
import httpx

from dotenv import load_dotenv
load_dotenv()

from utils.koneksi import Connection

from routes.ViewRoutes import routes_mainview
from routes.ApiAuth import routes_auth
from routes.ApiArima import routes_arima

app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins="*",
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key='passwordnyapanjangbanget')

is_development = os.getenv('development', '1') == '1'
mainport = int(os.getenv('port', '9000'))

# -- db connection
conn = Connection()

@app.middleware("http")
async def session_middleware(request: Request, call_next):
	response = JSONResponse(status_code=500, content="server error #99")
	try:
		# cek jika masuk dashboard
		request.state.conn = conn
		async for item in conn.get_dbsession():
			request.state.dbsession = item

		request.state.httpx = httpx.AsyncClient()
		request.state.templates = Jinja2Templates(directory="templates", autoescape=False, auto_reload=True)
		# print(request.session.items())
		# if str(request.url).split('/')[-1] == '' and .get('token', None) and request.session.get('refresh_token', None):
		#     return RedirectResponse('/login', status_code=status.HTTP_303_SEE_OTHER)
		response = await call_next(request)
	except Exception as ex:
		print("[==========================]")
		print("START GLOBAL CATCH".center(50, "-"))
		print("[GLOBAL CATCH]", ex)
		print(traceback.format_exc())
		print("STOP GLOBAL CATCH".center(50, "-"))
		print("[==========================]")
		if hasattr(request.state, "dbsession"):
			if request.state.dbsession.is_active:
				await request.state.dbsession.rollback()
	finally:
		if hasattr(request.state, "dbsession"):
			if request.state.dbsession.is_active:
				await request.state.dbsession.close()
		if not request.state.httpx.is_closed:
			await request.state.httpx.aclose()
	return response

@app.get("/ping")
async def read_root():
	return {"Hello": "World"}


@app.on_event("shutdown")
async def app_shutdown():
	print("[SHUTDOWNING]...")
	close_all_sessions()
	await conn.dispose_engines()

# -- STATIC -- #
script_dir = os.path.dirname(__file__)
st_abs_file_path = os.path.join(script_dir, "static/")
app.mount("/static", StaticFiles(directory=st_abs_file_path), name="static")

prefix = "/api"
app.include_router(routes_mainview, tags=["view"])
app.include_router(routes_auth, prefix=prefix, tags=["auth"])
app.include_router(routes_arima, prefix=prefix, tags=["arima"])

def main():
	print('[RUN MODE]:', 'DEVELOPMENT' if is_development else 'PRODUCTION')
	uvicorn.run("main:app", host="0.0.0.0", port=mainport, reload=is_development)

if __name__ == "__main__":
	main()