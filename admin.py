#==============================================================================
# 1. 도구 상자 준비 (필요한 외부 부품 및 모듈 불러오기)
#==============================================================================
from sqlmodel import create_engine, Session  # DB 연결 및 작업 일꾼(Session) 생성 도구
from fastapi import FastAPI, Depends, Request, Form, UploadFile, File  # 웹 서버 및 요청 처리 도구
from fastapi.templating import Jinja2Templates   # HTML 화면(템플릿) 그려주는 도구
from fastapi.responses import RedirectResponse  # 다른 페이지로 넘겨주는(리다이렉트) 도구
from sqlalchemy import text, URL                 # 생(Raw) SQL 쿼리 작성 및 DB 주소 구성 도구
from fastapi.staticfiles import StaticFiles      # 이미지/CSS 같은 정적 파일 제공 도구
from pathlib import Path                         # 파일/폴더 경로 다루기 도구
import shutil                                    # 파일 복사/저장 라이브러리

from DTO.ProductDTO import Product               # 상품 데이터를 묶어서 검증할 데이터 틀(DTO)

# 이미지 파일을 저장할 폴더 위치 지정 ('static/images')
dir = Path('static/images') 

app = FastAPI()  # FastAPI 웹 서버의 핵심 본체 생성

# '/static' 주소로 요청이 오면 실제 'static' 폴더 안의 파일(이미지 등)을 보여주도록 연결
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTML 템플릿 파일들이 위치한 기본 경로를 현재 폴더('.')로 지정
templates = Jinja2Templates(directory='.')  

#==============================================================================
# 2. 데이터베이스(DB) 연결 설정
#==============================================================================
# DB 접속에 필요한 주소 정보 구성 (종류, 계정명, 비밀번호, IP, 포트, DB이름)
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username="chimpiler_team",
    password="chimpiler!@#",
    host="192.168.0.65",
    port=3306,
    database="chimpiler",
)

# DB 서버와의 연결 통로(엔진) 생성 (echo=True는 실행되는 SQL 문을 콘솔에 출력해줌)
engine = create_engine(DATABASE_URL, echo=True)

# 의존성 주입(Depends)용 함수: 요청이 올 때마다 DB 일꾼(session)을 하나 만들어 빌려주고,
# 작업이 끝나면 자동으로 저장(commit) 및 종료를 처리해 줌
def get_session():
    with Session(engine) as session: 
        yield session     # 컨트롤러에 DB 세션 대여
        session.commit()   # 요청 완료 시 DB 변경사항 최종 저장

#==============================================================================
# 3. 단순 페이지 이동 라우터 (화면 보여주기)
#==============================================================================
# [관리자 대시보드 페이지] http://주소/admin 접속 시
@app.get('/admin')
def dashboard(request: Request, session: Session = Depends(get_session)):
    print('/admin 실행')

    #===========================
    # 품절 상품의 수를 조회하는 SQL문
    #===========================
    sql1 = text('''
    select count(*)
    from product
    where product_sale_stock = 0;
    ''')
    results1 = session.execute(sql1).mappings().fetchall()

    print(results1)
    print(results1[0]['count(*)'])

    #=========================
    # 답변 대기중인 믄의의 수를 조회하는 SQL문
    #=========================
    sql2= text('''
    select count(*)
    from inquiry
    where inquiry_status_id = 1;
    ''')

    results2 = session.execute(sql2).mappings().fetchall()

    print(results2)
    print(results2[0]['count(*)'])

    #==========================
    # 최근 주문 
    #==========================
    sql3 = text ('''
            select 
                o.order_sheet_id,
                o.user_id,
                o.order_name,
                os.order_total_price,
                st.order_status_name,
                ds.delivery_status_name
            from orders o 
            left join order_sheet os 
                on o.order_sheet_id = os.order_sheet_id
            left join order_status st 
                on o.order_status_id = st.order_status_id
            left join delivery d 
                on os.order_sheet_id = d.order_sheet_id
            left join delivery_status ds 
                on d.delivery_status_id = ds.delivery_status_id
        ''')
    results3 = session.execute(sql3).mappings().fetchall()

    #=========================
    # 주문 건수 조회
    #=========================
    sql4 = text('''
        select count(*)
        from orders
    ''')
    results4  = session.execute(sql4).mappings().fetchall()

    #========================
    # 예약 건수 조회
    #========================
    sql5 = text('''
        select count(*)
        from reservation
    ''')
    results5 = session.execute(sql5).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-dashboard.html' , {
        'sold_count' : results1[0]['count(*)'], # 품절 상품의 수를 화면에 뿌려줍니다 
        'inquiry_count' : results2[0]['count(*)'], # 답변 대기중인 문의의 수를 화면에 뿌려줍나다.
        'recent_orders' : results3,
        'order_count' : results4[0]['count(*)'],
        'reservation_count' : results5[0]['count(*)']
    })

# [메인 페이지] http://주소/ 접속 시
@app.get('/')
def main (request:Request, session:Session = Depends(get_session)):
    print('/ 실행')
    # main.html 화면을 띄워줌
    return templates.TemplateResponse(request, 'main.html')

#==============================================================================
# 4. 상품 및 재고 관리 CRUD 기능 (Create, Read, Update, Delete)
#==============================================================================

# [상품 목록 조회]
@app.get('/admin/products')
def product_list (request: Request, session: Session = Depends(get_session)) :
    print('상품 목록 출력')
    # DB에서 모든 상품 데이터를 가져오는 SQL 문 작성
    sql = text ('''
        select * from product
    ''')
    # SQL 실행 후 결과를 파이썬 딕셔너리 리스트 형태로 싹 긁어옴
    results = session.execute(sql).mappings().fetchall()

    # admin-products.html 화면에 'product_list'라는 이름으로 조회 결과를 전달해 출력
    return templates.TemplateResponse(request, 'admin-products.html', {
        'product_list' : results
    })

# [상품 신규 등록]
@app.post('/api/add')
def add_product(
    # 💡 [핵심 해결 포인트] Form() 대신 Depends(Product.as_form)을 이용해 
    # HTML에서 낱개로 들어오는 폼 데이터를 Product DTO 객체로 바인딩합니다.
    product: Product = Depends(Product.as_form),             
    product_image: UploadFile = File(),    # 파일 데이터로 전송된 첨부 이미지 파일
    session: Session = Depends(get_session) # DB 일꾼
):
    print('/api/add 실행')
    try :
        # 1. 첨부된 이미지를 서버의 static/images 폴더에 실제로 저장하는 과정
        filename = product_image.filename
        image_path = dir / filename 
        with image_path.open('wb') as buffer :
            # UploadFile의 파일 객체(product_image.file)를 하드디스크 버퍼로 복사
            shutil.copyfileobj(product_image.file, buffer)
        
        # 2. 전달받은 상품 객체를 DB에 넣기 좋게 딕셔너리로 변환
        params = product.model_dump() 
        # 파일명이 아닌 'static/images/파일명' 으로 저장.
        params['product_image'] = f'static/images/{filename}'  

        # 3. DB에 상품 정보를 데이터로 추가하는 SQL 문
        sql = text ('''
            insert into product
            (
            product_brand, product_name, product_detail, 
            product_image, product_price, product_sale_stock,
            product_reservation_stock, category_id
            )
            values(
            :product_brand, :product_name, :product_detail, 
            :product_image, :product_price, :product_sale_stock,
            :product_reservation_stock, :category_id
            )
        ''')
        session.execute(sql, params)
        session.commit()
    except Exception as e :
        print(e)

    # 등록 후 상품 목록 페이지로 다시 이동
    return RedirectResponse(url='/admin/products', status_code=303)

# [상품 정보 수정]
@app.post('/api/modify')
def update_product(
    # 💡 [핵심 해결 포인트] 수정 요청도 폼 데이터이므로 Depends(Product.as_form)을 사용합니다.
    product: Product = Depends(Product.as_form), 
    product_image: UploadFile = File(),   # Form() -> File()로 수정하여 일관성 유지
    session: Session = Depends(get_session)
):
    print('/api/modify 실행' , product)
    try:
        # 1. 새 이미지 파일이 들어왔다면 서버 폴더에 다시 저장
        filename = product_image.filename
        image_path = dir / filename 
        with image_path.open('wb') as buffer :
            shutil.copyfileobj(product_image.file, buffer)

        # 2. 데이터를 딕셔너리로 묶고 이미지 이름 설정
        params = product.model_dump()
        params['product_image'] = f'static/images/{filename}'  

        # 3. DB의 해당 상품 ID(product_id)에 맞는 정보들을 최신 데이터로 업데이트하는 SQL
        sql = text('''
            update product
            set 
                product_id = :product_id,
                product_brand = :product_brand,
                product_name = :product_name,
                product_detail = :product_detail, 
                product_image = :product_image, 
                product_price = :product_price, 
                product_sale_stock = :product_sale_stock,
                product_reservation_stock = :product_reservation_stock,
                category_id = :category_id
            where
                product_id = :product_id
        ''')
        session.execute(sql, params)
        session.commit()

    except Exception as e :
        print(e)

    return RedirectResponse(url='/admin/products', status_code=303)

# [상품 삭제]
@app.get('/api/delete/{product_id}')
def delete_product(product_id: int, session: Session = Depends(get_session)):
    print('/api/delete 실행', product_id)
    try:
        # URL 주소로 들어온 ID에 해당하는 상품을 DB에서 제거
        sql = text('''
            delete from product
            where product_id = :product_id
        ''')
        session.execute(sql, {'product_id': product_id})
        session.commit()
    except Exception as e:
        print(e)

    return RedirectResponse(url='/admin/products', status_code=303)

# [일시 품절 처리] (상태 값을 2로 변경)
@app.get('/api/soldout/{product_id}')
def soldout_product(product_id: int, session: Session = Depends(get_session)):
    print('/api/soldout 실행' , product_id)
    try:
        # product_active 값을 2로 바꿔서 "품절" 상태로 변경
        sql = text('''
            update product 
            set product_active = 2
            where product_id = :product_id
        ''')
        session.execute(sql, {'product_id': product_id})
        session.commit()
    except Exception as e :
        print(e)

    return RedirectResponse(url='/admin/products', status_code=303)

# [일시 품절 해제] (상태 값을 다시 1로 변경)
@app.get('/api/available/{product_id}')
def available_product(product_id: int, session: Session = Depends(get_session)):
    print('api/available 실행' , product_id)
    try:
        # product_active 값을 1로 바꿔서 다시 "판매 중" 상태로 변경
        sql = text('''
            update product
            set product_active = 1
            where product_id = :product_id
        ''')
        session.execute(sql, {'product_id': product_id})
        session.commit()
    except Exception as e :
        print(e)

    return RedirectResponse(url='/admin/products', status_code=303)

# [재고 보충]
@app.post('/api/restock')
def restock_product(
    product_id: int = Form(), 
    product_sale_stock: int = Form(), 
    product_reservation_stock: int = Form(), 
    session: Session = Depends(get_session)
):
    print('api/restock 실행')
    try:
        # 판매 재고와 예약 재고 수량을 전달받은 새 값으로 변경
        sql = text('''
            update product 
            set
                product_id = :product_id,
                product_sale_stock = :product_sale_stock,
                product_reservation_stock = :product_reservation_stock
            where 
                product_id = :product_id
        ''')
        session.execute(sql, {
            'product_id': product_id,
            'product_sale_stock': product_sale_stock,
            'product_reservation_stock': product_reservation_stock
        })
        session.commit()
    except Exception as e :
        print(e)

    return RedirectResponse(url='/admin/products', status_code=303)

# [검색 기능]
@app.get('/api/product/search')
def search_product (request:Request, keyword: str = "", session:Session = Depends(get_session)):
    sql = text('''
        select * from product
        where (:keyword = '' or product_name like :search_keyword)
    ''')

    result = session.execute(sql, {
    'keyword' : keyword,
    'search_keyword' : '%' + keyword + '%'
    })

    search_product_list = result.mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-products.html', {
        'product_list' : search_product_list
    })

#==============================================================================
# 5. 회원 관리 기능
#==============================================================================

# [회원 및 후기 신고 내역 조회]
@app.get('/admin/users')
def user_list (request: Request, session: Session = Depends(get_session)):
    print('회원 및 후기 신고 내역 조회')
    sql1 = text ('''
        select * from users
    ''')
    
    results1 = session.execute(sql1).mappings().fetchall()

    sql2 = text ('''
        select rr.report_id, pr.user_id, us.user_name, pr.product_review, pr.product_review_id, rr.report_detail from product_review as pr
        join review_report as rr
        on (pr.product_review_id = rr.product_review_id)
        join users as us
        on (pr.user_id = us.user_id)
    ''')

    results2 = session.execute(sql2).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-users.html', {
        'user_list' : results1,
        'review_report_list' : results2
    })

# [후기 신고 삭제]
@app.post("/api/report/delete/{product_review_id}")
def report_delete(product_review_id:int, session: Session = Depends(get_session)):
    print('후기 신고 삭제 기능 실행', product_review_id)
    
    sql = text('''
        delete from review_report
        where product_review_id = :product_review_id
    ''')
    session.execute(sql,{'product_review_id' : product_review_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)


# [회원 경고 추가]
@app.get('/api/warning/{user_id}') 
def user_warning( user_id : str, session: Session = Depends(get_session)):
    sql = text('''
        update users
        set 
            user_warning_count = user_warning_count + 1
        where
            user_id = :user_id
    ''')
    session.execute(sql, {'user_id' : user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)

# [회원 경고 제거]
@app.get('/api/warning/delete/{user_id}') 
def user_warning( user_id : str , session: Session = Depends(get_session)):
    print('경고 제거 실행')
    sql_all = text('''
        select user_warning_count
        from users
        where user_id = :user_id
    ''')

    result  =  session.execute(sql_all, {
        'user_id' : user_id
    })

    warning_count = result.mappings().fetchone()
    print('경고 횟수 :', warning_count['user_warning_count'])

    sql = text('''
          update users 
          set user_warning_count = user_warning_count  - 1
          where user_id = :user_id and user_warning_count >= 1
    ''')
    session.execute(sql, {'user_id' : user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)

# [회원 정지]
@app.get('/api/suspension/{user_id}')
def user_suspension(user_id : str, session:Session = Depends(get_session)):
    print('회원 정지 실행')

    sql = text('''
        update users
        set user_status = '정지'
        where user_id = :user_id
    ''')
    session.execute(sql, {'user_id' : user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)

# [회원 정지  해제]
@app.get('/api/unsuspend/{user_id}')
def user_unsuspend(user_id : str, session:Session = Depends(get_session)):
    print('회원 정지 해제 실행')

    sql = text('''
        update users
        set user_status = '정상'
        where user_id = :user_id
    ''')
    session.execute(sql, {'user_id' : user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)

# [검색 기능]
@app.get('/api/user/search')
def search_user (request:Request, keyword: str = "", session:Session = Depends(get_session)):
    sql = text('''
        select * from users
        where (:keyword = '' or user_name or user_id like :search_keyword)
    ''')

    result = session.execute(sql, {
    'keyword' : keyword,
    'search_keyword' : '%' + keyword + '%'
    })

    search_list = result.mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-users.html', {
        'user_list' : search_list
    })

#==============================================================================
# 6. 문의관리 기능
#==============================================================================

# [문의 조회]
@app.get('/admin/inquiries')
def user_list (request: Request, session: Session = Depends(get_session)):
    print('문의 조회')
    sql = text ('''
        select * from inquiry
    ''')
    
    results = session.execute(sql).mappings().fetchall()
    
    return templates.TemplateResponse(request, 'admin-inquiries.html', {
            'inquiry_list' : results
        })

# [문의 답변 등록 및 수정 ]
@app.post('/api/answer/{inquiry_id}')
def answer_inquiry(inquiry_id : int, inquiry_answer : str = Form(), session:Session = Depends(get_session)):
    print('문의 답변 등록 실행')
    sql = text ('''
        update inquiry
        set 
            inquiry_answer = :inquiry_answer,
            inquiry_status_id = 2 
        where inquiry_id = :inquiry_id
    ''')
    session.execute(sql, {
        'inquiry_id' : inquiry_id,
        'inquiry_answer' : inquiry_answer
    })
    session.commit()

    return RedirectResponse(url='/admin/inquiries', status_code=303)

#==============================================================================
# 7. 주문/배송 관리
#==============================================================================

#[주문/배송 조회]
@app.get('/admin/orders')
def order_list (request: Request, session: Session = Depends(get_session)):
    print('주문/배송 조회')
    sql = text ('''
      select 
	    o.order_sheet_id,
	    o.user_id,
	    o.order_name,
	    os.order_total_price,
	    ot.order_status_name,
	    ds.delivery_status_name
    from orders o
    left join order_sheet os 
	    on o.order_sheet_id = os.order_sheet_id
    left join order_status ot
	    on o.order_status_id = ot.order_status_id
    left join delivery d 
	    on os.order_sheet_id = d.order_sheet_id
    left join delivery_status ds
	    on d.delivery_status_id = ds.delivery_status_id;
    ''')
    results = session.execute(sql).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-orders.html', {
        'order_list' : results
    })

#==============================================================================
# 8. 예약 관리
#==============================================================================

#[예약 목록 조회]
@app.get('/admin/reservations')
def reservation_list (request: Request, session: Session = Depends(get_session)):
    print ('예약 목록 조회')

    # 예약 목록 조회 SQL문 
    sql = text('''
        select 
            r.reservation_id,
            u.user_name,
            p.product_name,
            r.reservation_quantity,
            rs.reservation_status_name
        from reservation as r
        left join product as p 
            on r.product_id = p.product_id
        left join reservation_status as rs
            on r.reservation_status_id = rs.reservation_status_id
        left join users as u
            on r.user_id = u.user_id
    ''')
    # 대기 중인 예약 목록 조회 SQL문 
    sql2 = text('''
        select 
            count(*)
        from reservation as r 
        left join reservation_status as rs 
            on r.reservation_status_id = rs.reservation_status_id
        where 
            rs.reservation_status_name = '예약대기'
    ''')

    results = session.execute(sql).mappings().fetchall()

    results2 = session.execute(sql2).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-reservations.html', {
        'reservation_list' : results,
        'reservation_wait' : results2[0]['count(*)']
    })

@app.get('/api/delete/reservations/{reservation_id}')
def delete_reservation(reservation_id : int, session:Session = Depends(get_session)):
    print('예약 삭제 실행' , reservation_id)
    sql = text('''
        delete from reservation
        where  reservation_id = :reservation_id
    ''')
    session.execute(sql, {'reservation_id' : reservation_id})
    session.commit()

    return RedirectResponse(url='/admin/reservations', status_code=303)


#==============================================================================
# 웹 서버 직접 실행 구문
#==============================================================================
if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 주소와 8085 포트에서 서버를 실행하며, 코드 변경 시 자동 재시작(reload=True) 설정
    uvicorn.run("admin:app", port=8085, reload=True, host="0.0.0.0")