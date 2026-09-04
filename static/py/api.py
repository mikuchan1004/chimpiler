from sqlmodel import create_engine, Session # DB 연결 및 테이블 관리를 위한 SQLModel 모듈
from fastapi import FastAPI, Depends, Request, Form    # FastAPI 기본 기능, 의존성 주입(Depends), 요청 객체(Request), 폼 데이터 처리(Form)
from fastapi.templating import Jinja2Templates         # HTML 템플릿(Jinja2) 연동을 위한 모듈
from fastapi.responses import RedirectResponse         # 작업 완료 후 다른 페이지로 이동(리다이렉트)시키는 모듈
from sqlalchemy import text                           # 원시 SQL(Raw SQL) 문장을 안전하게 실행하기 위한 함수

app = FastAPI()  # FastAPI 웹 서버 인스턴스 생성
templates = Jinja2Templates(directory='.')  # HTML 파일들이 위치한 폴더 경로 지정

DATABASE_URL = 'mysql+pymysql://chimpiler_team:chimpiler!@#@192.168.0.65:3306/chimpiler'

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session: 
        yield session       # 라우터 함수에 DB 세션을 전달
        session.commit()    # 요청 처리가 무사히 끝나면 변경
        
@app.get('/list')
def list(request: Request, session: Session = Depends(get_session)):
    print('/list 실행')
    # 전체 사원 조회를 위한 SQL 문 작성
    sql = text('''
        select * from emp3
    ''')
    # .mappings().fetchall(): 쿼리 결과를 딕셔너리 형태로 변환하여 전체 목록을 가져옴
    results = session.execute(sql).mappings().fetchall()
    
    # list.html 파일에 emp_list 변수 이름으로 조회 결과를 전달하여 화면 렌더링
    return templates.TemplateResponse(request, 'list.html', {
        'emp_list': results
    })