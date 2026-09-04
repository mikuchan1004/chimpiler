from sqlmodel import create_engine, Session # DB 연결 및 테이블 관리를 위한 SQLModel 모듈
from fastapi import FastAPI, Depends, Request, Form    # FastAPI 기본 기능, 의존성 주입(Depends), 요청 객체(Request), 폼 데이터 처리(Form)
from fastapi.templating import Jinja2Templates         # HTML 템플릿(Jinja2) 연동을 위한 모듈
from fastapi.responses import RedirectResponse         # 작업 완료 후 다른 페이지로 이동(리다이렉트)시키는 모듈
from sqlalchemy import text                           # 원시 SQL(Raw SQL) 문장을 안전하게 실행하기 위한 함수
from fastapi.staticfiles import StaticFiles

app = FastAPI()  # FastAPI 웹 서버 인스턴스 생성
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='.')  

DATABASE_URL = 'mysql+pymysql://chimpiler_team:chimpiler!@#@192.168.0.65:3306/chimpiler'

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session: 
        yield session       # 라우터 함수에 DB 세션을 전달
        session.commit()    # 요청 처리가 무사히 끝나면 변경

###########
# 페이지 이동
###########

# 관리자 대시보드 
@app.get('/dashboard')
def list(request: Request, session: Session = Depends(get_session)):
    print('/dashboard 실행')
    return templates.TemplateResponse(request, 'admin-dashboard.html')

if __name__ == "__main__":
    import uvicorn
    
    # Uvicorn 서버 실행
    # "파일이름:FastAPI객체명" -> "03_crud:app"
    # host="0.0.0.0": 외부 접속 허용
    # port=8085: 웹 서버가 사용할 포트 번호 (8000번 대신 지정)
    # reload=True: 코드 변경 시 서버 자동 재시작 (개발용 옵션)
    uvicorn.run("api:app", port=8085, reload=True, host="0.0.0.0")