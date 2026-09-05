
# from fastapi import FastAPI, Depends, Request, Form
# from fastapi.templating import Jinja2Templates
# from fastapi.responses import RedirectResponse
# from sqlmodel import select


# from fastapi.staticfiles import StaticFiles

# from sqlmodel import create_engine, Session
# from sqlalchemy import text
# from sqlalchemy.engine import URL

# from DTO.userDTO import users
# import traceback



# # 서버
# app = FastAPI()
# templates = Jinja2Templates(directory='.')
# app.mount("/static", StaticFiles(directory="static"), name="static")



# # DB 설정
# DATABASE_URL = URL.create(
#     drivername="mysql+pymysql",
#     username="chimpiler_team",
#     password="chimpiler!@#",
#     host="192.168.0.65",
#     port=3306,
#     database="chimpiler",
# )

# engine = create_engine(DATABASE_URL, echo=True)
# with Session(engine) as session:
#     print("DB:", session.exec(text("SELECT DATABASE()")).one())
#     print("USER:", session.exec(text("SELECT USER()")).one())

# def get_session ():
#     with Session(engine) as session :
#         yield session
#         session.commit()

# # @app.get('/signup')
# # def signup_loading(request: Request):
# #     return templates.TemplateResponse(request, 'signup.html')

# @app.get('/signup')
# def signup_loading(request: Request):
#     with Session(engine) as session:
#         count = len(session.exec(select(users)).all())
#         print("현재 회원 수:", count)

#     return templates.TemplateResponse(request, 'signup.html')



# @app.get('/terms')
# def terms_loading(request: Request):
#     return templates.TemplateResponse(request, 'terms.html')

# @app.get('/login')
# def terms_loading(request: Request):
#     return templates.TemplateResponse(request, 'login.html')

# @app.get('/main')
# def main_loading(request: Request):
#     return templates.TemplateResponse(request, 'main.html')

# @app.post("/signup")
# def signup(
#     user_id: str = Form(),
#     user_password: str = Form(),
#     user_password_chk: str = Form(),
#     user_name: str = Form(),
#     user_phone: int = Form(),
#     user_addr: str = Form(),
#     user_addr_detail: str = Form(),
#     user_email: str = Form(),
#     session: Session = Depends(get_session)
# ):
#     user_addr = user_addr + " " + user_addr_detail

#     user = users(
#         user_id=user_id,
#         user_password=user_password,
#         user_name=user_name,
#         user_phone=user_phone,
#         user_addr=user_addr,
#         user_email=user_email,
#         user_warning_count=0,
#         user_status="정상",
#     )
#     session.add(user)
#     session.commit()


#     return RedirectResponse("/main", status_code=303)


    
#     # print('user_id : ', user_id)
#     # print('user_password : ', user_password)
#     # print('user_password_chk : ', user_password_chk)
#     # print('user_name : ', user_name)
#     # print('user_addr : ', user_addr)
#     # print('user_addr_detail : ', user_addr_detail)
#     # print('user_email : ', user_email)
#     # print('user_phone : ', user_phone)


# # 템플릿(jinja) 설정


# # 일단 dto로 py에서 db로 가는 포장지는 완성함
# # 지금 회원가입 py에서 필요한건 db 통로
# # html에서 보낸 값을 받아야함




# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("gicho:app", port=8000, reload=True, host="0.0.0.0")

from fastapi import FastAPI, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import select

from fastapi.staticfiles import StaticFiles

from sqlmodel import create_engine, Session
from sqlalchemy import text
from sqlalchemy.engine import URL

from DTO.userDTO import users
import traceback


# 서버
app = FastAPI()
templates = Jinja2Templates(directory='.')
app.mount("/static", StaticFiles(directory="static"), name="static")


# DB 설정
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username="chimpiler_team",
    password="chimpiler!@#",
    host="192.168.0.65",
    port=3306,
    database="chimpiler",
)

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session


@app.get('/signup')
def signup_loading(request: Request):
    with Session(engine) as session:
        users_list = session.exec(select(users)).all()
        print("현재 회원 수:", len(users_list))

    return templates.TemplateResponse(request, 'signup.html')


@app.get('/terms')
def terms_loading(request: Request):
    return templates.TemplateResponse(request, 'terms.html')


@app.get('/login')
def login_loading(request: Request):
    return templates.TemplateResponse(request, 'login.html')


@app.get('/main')
def main_loading(request: Request):
    return templates.TemplateResponse(request, 'main.html')


@app.post("/signup")
def signup(
    user_id: str = Form(),
    user_password: str = Form(),
    user_password_chk: str = Form(),
    user_name: str = Form(),
    user_phone: int = Form(),
    user_addr: str = Form(),
    user_addr_detail: str = Form(),
    user_email: str = Form(),
    session: Session = Depends(get_session)
):
    user_addr = user_addr + " " + user_addr_detail

    user = users(
        user_id=user_id,
        user_password=user_password,
        user_name=user_name,
        user_phone=user_phone,
        user_addr=user_addr,
        user_email=user_email,
        user_warning_count=0,
        user_status="정상",
    )

    session.add(user)
    session.commit()
    return RedirectResponse("/main", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gicho:app", port=8000, reload=True, host="0.0.0.0")