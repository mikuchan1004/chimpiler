from fastapi import FastAPI, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import select
from fastapi.responses import HTMLResponse
from DTO.userDTO import Users


from fastapi.staticfiles import StaticFiles

from sqlmodel import create_engine, Session
from sqlalchemy import text
from sqlalchemy.engine import URL

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
        users_list = session.exec(select(Users)).all()
        print("현재 회원 수:", len(users_list))

    return templates.TemplateResponse(request, 'signup.html')


@app.get('/terms')
def terms_loading(request: Request):
    return templates.TemplateResponse(request, 'terms.html')


@app.get('/login')
def login_loading(request: Request):
    return templates.TemplateResponse(request, 'login.html')
@app.get('/ai-health')
def login_loading(request: Request):
    return templates.TemplateResponse(request, 'ai-health.html')
@app.get('/notice')
def login_loading(request: Request):
    return templates.TemplateResponse(request, 'notice.html')
@app.get('/products')
def login_loading(request: Request):
    return templates.TemplateResponse(request, 'products.html')
@app.get('/mypage-dashboard')
def login_loading(request: Request):
    return templates.TemplateResponse(request, 'products.html')
@app.get('/cart')
def login_loading(request: Request):
    return templates.TemplateResponse(request, 'cart.html')


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

    user = Users(
        user_id=user_id,
        user_password=user_password,
        user_name=user_name,
        user_phone=user_phone,
        user_addr=user_addr,
        user_email=user_email,
        user_warning_count=0,
        user_status="정상",
    )
    if user_password != user_password_chk:
        return HTMLResponse("""
    <script>
        alert('비밀번호가 일치하지 않습니다.');
        history.back();
    </script>
    """)
    session.add(user)
    session.commit()
    return RedirectResponse("/main", status_code=303)


# @app.get('/login/check')
# def list(
#     alist: Request,
#     user_id: str,
#     user_password: str,
#     session:Session = Depends(get_session)
# ) :
@app.post('/login/check')
def list(
    alist: Request,
    user_id: str = Form(),
    user_password: str = Form(),
    session: Session = Depends(get_session)
):

    sql = text('''
        select * from users
    ''')

    result = session.execute(sql)
    user_list = result.mappings().fetchall()

    print(user_list)

    for users in user_list :
        login_id=users['user_id']
        login_ps=users['user_password']
        # html로부터 입력받는 값
        print('user_id 있는지?', user_id in str(users))
        print('user_password 있는지?', user_password in str(users))
        print('-------------------')
        # 프린트 3개는 확인용 없어도 그만
        if login_id == user_id and login_ps == user_password:
            response=templates.TemplateResponse( 
                        request=alist,
                        name='main.html',
                        context={
                            'user_name':users['user_name']
                        }

                        )
            response.set_cookie(
                        key='log_chk',
                        value='chk',
                        max_age=60 * 60,
                        path='/'
                    )
            # 로그인 성공하면 쿠키로 로그인 성공했다고 알림
            return response
        
    return HTMLResponse("""
<script>
    alert('아이디 또는 비밀번호가 틀렸습니다.');
    history.back();
</script>
""")





#     a = [1,2,3, 4]
#     print(1 in a)
#     print(5 in a)
    # User = session.exec(
    #     select(Users).where(Users.user_id == user_id).first()
        
    # )
    # if user and user.user_password == user_password:
    #     print("로그인 성공")
    # else:
    #     print("로그인 실패")
#     sql = text('''
#     select user_id,user_password
#     from users
#     ''')
#     result = session.execute(sql)
#     player_list = result.mappings().fetchall()
#     print(player_list,'list 확인용 @@@@@@')

    
#     return templates.TemplateResponse(
#     alist, 
#     'login.html',
#     {
#         'player_list': player_list
#     }
# )





if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", port=8000, reload=True, host="0.0.0.0")