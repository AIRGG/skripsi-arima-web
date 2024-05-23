from typing import List, Union, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status as HttpStatus
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_sqlalchemy import sqlalchemy_to_pydantic
from contextlib import suppress

from starlette.applications import Starlette
from starlette.routing import Route

from utils.utility import check_user_login

import json,time,os,joblib,pathlib
import httpx
import jwt