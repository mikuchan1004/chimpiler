##########
# 필요한 모듈 호출 영역
##########
from sqlmodel import create_engine, Session
from fastapi import FastAPI, Depends, Request, Form   
from fastapi.templating import Jinja2Templates         
from fastapi.responses import RedirectResponse        
from sqlalchemy import text, URL                         
from fastapi.staticfiles import StaticFiles

app = FastAPI()  # FastAPI 웹 서버 인스턴스 생성
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='.')  

DATABASE_URL = URL.create(
    drivername = 'mysql+pymysql',
    username = 'chimplier_team',
    password='chimpiler!@#',
    host='192.168.0.65',
    port='3306',
    database='chimpiler'
)
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session: 
        yield session     
        session.commit()   

##########
# 페이지 이동 라우터
##########
# 관리자 대시보드 페이지
@app.get('/dashboard')
def dashboard(request: Request, session: Session = Depends(get_session)):
    print('/dashboard 실행')
    return templates.TemplateResponse(request, 'admin-dashboard.html')

# 관리자 문의관리 페이지
@app.get('/inquiries')
def inquiries (request: Request, session: Session = Depends(get_session)):
    print('/inquiries 실행')
    return templates.TemplateResponse(request, 'admin-inquiries.html')

# 관리자 회원관리 페이지
@app.get('/users')
def users (request: Request, session: Session = Depends(get_session)):
    print('/users 실행')
    return templates.TemplateResponse(request, 'admin-users.html')

# 관리자 상품/재고관리 페이지 
@app.get('/products')
def products (request:Request, session: Session = Depends(get_session)):
    print('/products 실행')
    return templates.TemplateResponse(request, 'admin-products.html' )

# 관리자 주문/배송관리 페이지 
@app.get('/orders')
def orders(request:Request, session: Session = Depends(get_session)):
    print('/orders 실행')
    return templates.TemplateResponse(request, 'admin-orders.html')

# 관리자 예약관리 페이지 
@app.get('/reservations')
def reservations (request:Request, session: Session = Depends(get_session)):
    print('reservations 실행')
    return templates.TemplateResponse(request, 'admin-reservations.html')

# 메인 페이지 이동 
@app.get('/main')
def main (request:Request, session:Session = Depends(get_session)):
    print('/main 실행')
    return templates.TemplateResponse(request, 'main.html')
##########
# 페이지 이동 라우터 끝
##########

#########
# uvicorn 서버 실행 
#########
if __name__ == "__main__":
    import uvicorn
    
    # Uvicorn 서버 실행
    # "파일이름:FastAPI객체명" -> "03_crud:app"
    # host="0.0.0.0": 외부 접속 허용
    # port=8085: 웹 서버가 사용할 포트 번호 (8000번 대신 지정)
    # reload=True: 코드 변경 시 서버 자동 재시작 (개발용 옵션)
    uvicorn.run("admin:app", port=8085, reload=True, host="0.0.0.0")
    #########
    #  uvicorn  서버 실행 끝. 여기가 코드의 마지막입니다.
    #########