# 이 파일에 적혀있는 주석들은 전부 Google Gemini가 남겨주었습니다 .

# ==============================================================================
# 1. 도구 상자 준비 (필요한 외부 부품 불러오기)
# ==============================================================================
# 데이터베이스(DB) 연결 및 실제 심부름을 해줄 일꾼(Session) 생성 도구
from sqlmodel import create_engine, Session

# 웹 사이트를 만들고 손님(사용자)의 요청을 처리하는 메인 프레임워크 도구들
from fastapi import FastAPI, Depends, Request, Form, UploadFile, File

# 사용자가 보게 될 HTML 웹 화면(템플릿)을 예쁘게 그려주는 도구
from fastapi.templating import Jinja2Templates

# 다른 웹 페이지 주소로 손님을 슝 이동(리다이렉트)시켜 주는 도구
from fastapi.responses import RedirectResponse

# 데이터베이스에 명령을 직접 내리는 'SQL 명령문' 및 DB 접속 주소 만드는 도구
from sqlalchemy import text, URL

# 이미지, CSS 같은 정적(고정) 파일을 웹 브라우저에 보여주기 위한 도구
from fastapi.staticfiles import StaticFiles

# 컴퓨터 안의 파일과 폴더 위치(경로)를 안전하게 다루는 도구
from pathlib import Path

# 파일 복사나 이동 등 컴퓨터 파일 작업을 도와주는 도구
import shutil

# 손님이 입력한 상품 정보를 규격에 맞게 묶어주는 데이터 서식(틀)
from DTO.ProductDTO import Product

# 손님이 올린 상품 사진들을 모아둘 서버 컴퓨터 안의 폴더 위치 ('static/images')
dir = Path('static/images')

# FastAPI를 이용해 우리 웹 사이트의 '본체(엔진)'를 생성
app = FastAPI()

# 웹 브라우저에서 '/static' 주소로 요청이 들어오면 실제 컴퓨터의 'static' 폴더 안의 파일들을 보여주도록 연결
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTML 화면 파일들이 모여 있는 기본 폴더 위치를 현재 폴더('.')로 지정
templates = Jinja2Templates(directory='.')


# ==============================================================================
# 2. 데이터베이스(DB: 정보 저장 창고) 연결 설정
# ==============================================================================
# 정보 저장 창고(DB)에 들어가기 위한 출입증(주소, 계정명, 비밀번호 등)을 준비
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",  # 사용할 DB 종류 및 통신 방식
    username="chimpiler_team",   # 관리자 계정 이름
    password="chimpiler!@#",    # 비밀번호
    host="192.168.0.65",        # DB 창고가 있는 컴퓨터 주소(IP)
    port=3306,                  # 접속할 통로 번호(포트)
    database="chimpiler",       # 사용할 저장 창고 이름
)

# 실제로 DB 창고 문을 열고 닫을 수 있는 '연결 통로(엔진)'를 생성
# (echo=True를 켜두면 창고에 내린 명령 내용이 터미널 화면에 그대로 찍혀요)
engine = create_engine(DATABASE_URL, echo=True)


# 손님이 요청을 보낼 때마다 DB 창고 심부름꾼(Session)을 1명 배정해 주고,
# 작업이 끝나면 안전하게 변경사항을 저장(commit)한 뒤 돌려보내는 함수
def get_session():
    with Session(engine) as session:
        yield session     # 일꾼 한 명을 기능 담당 함수에게 빌려줌
        session.commit()  # 심부름이 무사히 끝나면 변경된 내용을 창고에 최종 확정 저장!


# ==============================================================================
# 3. 단순 페이지 이동 및 대시보드 화면 보여주기
# ==============================================================================
# [관리자 대시보드 메인 화면] 인터넷 주소: /admin 접속 시 실행
@app.get('/admin')
def dashboard(request: Request, session: Session = Depends(get_session)):
    print('/admin 실행')

    # 1) 창고에서 '남은 판매 재고가 0개'인 품절 상품의 총개수를 세어옴
    sql1 = text('''
    select count(*)
    from product
    where product_sale_stock = 0;
    ''')
    results1 = session.execute(sql1).mappings().fetchall()
    print(results1)
    print(results1[0]['count(*)'])

    # 2) 손님이 문의를 남겼는데 아직 답변하지 않은(상태 번호 1번) 문의 개수를 세어옴
    sql2 = text('''
    select count(*)
    from inquiry
    where inquiry_status_id = 1;
    ''')
    results2 = session.execute(sql2).mappings().fetchall()
    print(results2)
    print(results2[0]['count(*)'])

    # 3) 최근 주문 내역(주문서 번호, 주문자, 총 결제 금액, 주문 상태, 배송 상태 등)을 한눈에 모아서 가져옴
    sql3 = text('''
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

    # 4) 지금까지 들어온 전체 주문 건수를 세어옴
    sql4 = text('''
        select count(*)
        from orders
    ''')
    results4 = session.execute(sql4).mappings().fetchall()

    # 5) 고객들이 예약해 둔 전체 예약 건수를 세어옴
    sql5 = text('''
        select count(*)
        from reservation
    ''')
    results5 = session.execute(sql5).mappings().fetchall()

    # 대시보드 화면(admin-dashboard.html)에 위에서 조사한 숫자와 내역들을 전달해서 화면에 띄워줌
    return templates.TemplateResponse(request, 'admin-dashboard.html', {
        'sold_count': results1[0]['count(*)'],      # 품절 상품 개수
        'inquiry_count': results2[0]['count(*)'],   # 답변 대기 문의 개수
        'recent_orders': results3,                  # 최근 주문 목록 리스트
        'order_count': results4[0]['count(*)'],     # 전체 주문 건수
        'reservation_count': results5[0]['count(*)'] # 전체 예약 건수
    })


# [일반 메인 홈 화면] 인터넷 주소: / 접속 시 실행
@app.get('/')
def main(request: Request, session: Session = Depends(get_session)):
    print('/ 실행')
    # main.html 첫 화면을 손님 웹 브라우저에 띄워줌
    return templates.TemplateResponse(request, 'main.html')


# ==============================================================================
# 4. 상품 관리 기능 (목록 보기, 새 상품 등록, 수정, 삭제, 품절 처리)
# ==============================================================================

# [상품 목록 화면 조회]
@app.get('/admin/products')
def product_list(request: Request, session: Session = Depends(get_session)):
    print('상품 목록 출력')
    # 창고(DB)에 저장된 모든 상품 정보를 몽땅 가져오는 명령
    sql = text('''
        select * from product
    ''')
    results = session.execute(sql).mappings().fetchall()

    # 상품 목록 화면(admin-products.html)에 방금 가져온 상품 데이터를 넘겨서 보여줌
    return templates.TemplateResponse(request, 'admin-products.html', {
        'product_list': results
    })


# [새 상품 등록하기]
@app.post('/api/add')
def add_product(
    product: Product = Depends(Product.as_form),  # 화면 폼에 적힌 상품 정보(이름, 가격 등)를 서식에 맞춰 가져옴
    product_image: UploadFile = File(),           # 함께 첨부한 이미지 파일
    session: Session = Depends(get_session)        # DB 일꾼
):
    print('/api/add 실행')
    try:
        # 1단계: 손님이 올린 이미지 파일을 서버 컴퓨터의 'static/images' 폴더에 실제로 복사해서 저장함
        filename = product_image.filename
        image_path = dir / filename
        with image_path.open('wb') as buffer:
            shutil.copyfileobj(product_image.file, buffer)

        # 2단계: 상품 정보를 정리하고, 이미지 파일이 저장된 위치 글자('static/images/파일명')를 기록함
        params = product.model_dump()
        params['product_image'] = f'static/images/{filename}'

        # 3단계: DB 창고의 product 칸에 새 상품 정보를 한 줄 추가하라고 명령
        sql = text('''
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
    except Exception as e:
        # 혹시 저장하다 에러가 나면 콘솔창에 오류 내용을 출력
        print(e)

    # 등록이 끝나면 다시 상품 목록 페이지(/admin/products)로 화면을 돌려보냄
    return RedirectResponse(url='/admin/products', status_code=303)


# [상품 정보 수정하기]
@app.post('/api/modify')
def update_product(
    product: Product = Depends(Product.as_form),  # 수정할 새 상품 정보들
    product_image: UploadFile = File(),           # 새로 바꿀 이미지 파일
    session: Session = Depends(get_session)
):
    print('/api/modify 실행', product)
    try:
        # 1단계: 새로 업로드한 이미지를 서버 폴더에 다시 저장
        filename = product_image.filename
        image_path = dir / filename
        with image_path.open('wb') as buffer:
            shutil.copyfileobj(product_image.file, buffer)

        # 2단계: 새 이미지 위치를 포함하여 수정할 데이터 정리
        params = product.model_dump()
        params['product_image'] = f'static/images/{filename}'

        # 3단계: 해당 상품 번호(product_id)를 찾아 적혀 있는 정보들을 새 내용으로 덮어쓰기(업데이트)
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

    except Exception as e:
        print(e)

    # 수정이 끝나면 상품 목록 페이지로 복귀
    return RedirectResponse(url='/admin/products', status_code=303)


# [상품 삭제하기]
@app.get('/api/delete/{product_id}')
def delete_product(product_id: int, session: Session = Depends(get_session)):
    print('/api/delete 실행', product_id)
    try:
        # 주소로 전달받은 상품 고유번호(product_id)를 창고에서 아예 지워버림
        sql = text('''
            delete from product
            where product_id = :product_id
        ''')
        session.execute(sql, {'product_id': product_id})
        session.commit()
    except Exception as e:
        print(e)

    # 삭제 후 상품 목록 화면으로 이동
    return RedirectResponse(url='/admin/products', status_code=303)


# [상품 일시 품절 처리]
@app.get('/api/soldout/{product_id}')
def soldout_product(product_id: int, session: Session = Depends(get_session)):
    print('/api/soldout 실행', product_id)
    try:
        # 상품 상태(product_active) 값을 '2'(품절 상태를 의미)로 변경
        sql = text('''
            update product 
            set product_active = 2
            where product_id = :product_id
        ''')
        session.execute(sql, {'product_id': product_id})
        session.commit()
    except Exception as e:
        print(e)

    return RedirectResponse(url='/admin/products', status_code=303)


# [상품 판매 재개 처리 (품절 해제)]
@app.get('/api/available/{product_id}')
def available_product(product_id: int, session: Session = Depends(get_session)):
    print('api/available 실행', product_id)
    try:
        # 상품 상태(product_active) 값을 다시 '1'(정상 판매 중)로 변경
        sql = text('''
            update product 
            set product_active = 1
            where product_id = :product_id
        ''')
        session.execute(sql, {'product_id': product_id})
        session.commit()
    except Exception as e:
        print(e)

    return RedirectResponse(url='/admin/products', status_code=303)


# [재고 수량 보충하기]
@app.post('/api/restock')
def restock_product(
    product_id: int = Form(),                 # 수량을 변경할 상품 고유번호
    product_sale_stock: int = Form(),        # 새로 지정할 일반 판매 재고 수량
    product_reservation_stock: int = Form(), # 새로 지정할 예약 재고 수량
    session: Session = Depends(get_session)
):
    print('api/restock 실행')
    try:
        # 지정한 상품의 일반 판매 재고와 예약 재고 개수를 입력한 새 숫자로 교체
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
    except Exception as e:
        print(e)

    return RedirectResponse(url='/admin/products', status_code=303)


# [상품 이름으로 검색하기]
@app.get('/api/product/search')
def search_product(request: Request, keyword: str = "", session: Session = Depends(get_session)):
    # 검색어가 비어있으면 전체를, 검색어가 있으면 상품 이름에 그 단어가 들어간 것만 쏙 골라오는 명령
    sql = text('''
        select * from product
        where (:keyword = '' or product_name like :search_keyword)
    ''')

    result = session.execute(sql, {
        'keyword': keyword,
        'search_keyword': '%' + keyword + '%'
    })

    search_product_list = result.mappings().fetchall()

    # 찾아낸 상품 검색 결과만 모아서 상품 관리 화면에 표시
    return templates.TemplateResponse(request, 'admin-products.html', {
        'product_list': search_product_list
    })


# ==============================================================================
# 5. 회원 관리 기능 (회원 조회, 경고 부여/차감, 정지, 삭제)
# ==============================================================================

# [회원 목록 및 리뷰 신고 내역 조회]
@app.get('/admin/users')
def user_list(request: Request, session: Session = Depends(get_session)):
    print('회원 및 후기 신고 내역 조회')
    # 1) 등록된 모든 회원 명단을 가져옴
    sql1 = text('''
        select * from users
    ''')
    results1 = session.execute(sql1).mappings().fetchall()

    # 2) 다른 사람의 불량 후기(리뷰)로 신고 접수된 내역과 신고 사유를 엮어서 가져옴
    sql2 = text('''
        select rr.report_id, pr.user_id, us.user_name, pr.product_review, pr.product_review_id, rr.report_detail from product_review as pr
        join review_report as rr
        on (pr.product_review_id = rr.product_review_id)
        join users as us
        on (pr.user_id = us.user_id)
    ''')
    results2 = session.execute(sql2).mappings().fetchall()

    # 회원 관리 화면(admin-users.html)에 회원 목록과 신고 내역을 같이 띄워줌
    return templates.TemplateResponse(request, 'admin-users.html', {
        'user_list': results1,
        'review_report_list': results2
    })


# [접수된 리뷰 신고 내역 삭제]
@app.post("/api/report/delete/{product_review_id}")
def report_delete(product_review_id: int, session: Session = Depends(get_session)):
    print('후기 신고 삭제 기능 실행', product_review_id)

    # 관리자가 확인 후 이상이 없거나 처리가 끝나 신고 내역을 목록에서 지움
    sql = text('''
        delete from review_report
        where product_review_id = :product_review_id
    ''')
    session.execute(sql, {'product_review_id': product_review_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)


# [회원에게 경고 1회 추가]
@app.get('/api/warning/{user_id}')
def user_warning(user_id: str, session: Session = Depends(get_session)):
    # 문제 행동을 한 회원의 누적 경고 횟수를 1 올림 (+1)
    sql = text('''
        update users
        set 
            user_warning_count = user_warning_count + 1
        where
            user_id = :user_id
    ''')
    session.execute(sql, {'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)


# [회원의 경고 1회 차감(취소)]
@app.get('/api/warning/delete/{user_id}')
def user_warning_delete(user_id: str, session: Session = Depends(get_session)):
    print('경고 제거 실행')
    # 회원의 현재 경고 횟수를 먼저 확인
    sql_all = text('''
        select user_warning_count
        from users
        where user_id = :user_id
    ''')
    result = session.execute(sql_all, {'user_id': user_id})
    warning_count = result.mappings().fetchone()
    print('경고 횟수 :', warning_count['user_warning_count'])

    # 경고가 1회 이상 있는 경우에만 경고를 1개 줄여줌 (-1) (0개 미만으로 내려가지 않게 방지)
    sql = text('''
          update users 
          set user_warning_count = user_warning_count - 1
          where user_id = :user_id and user_warning_count >= 1
    ''')
    session.execute(sql, {'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)


# [회원 이용 정지]
@app.get('/api/suspension/{user_id}')
def user_suspension(user_id: str, session: Session = Depends(get_session)):
    print('회원 정지 실행')

    # 해당 회원의 상태를 '정지'로 변경하여 서비스 이용을 제한
    sql = text('''
        update users
        set user_status = '정지'
        where user_id = :user_id
    ''')
    session.execute(sql, {'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)


# [회원 이용 정지 해제]
@app.get('/api/unsuspend/{user_id}')
def user_unsuspend(user_id: str, session: Session = Depends(get_session)):
    print('회원 정지 해제 실행')

    # 징계 기간이 끝난 회원의 상태를 다시 '정상'으로 원상 복구
    sql = text('''
        update users
        set user_status = '정상'
        where user_id = :user_id
    ''')
    session.execute(sql, {'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)


# [회원 이름/아이디로 검색]
@app.get('/api/user/search')
def search_user(request: Request, keyword: str = "", session: Session = Depends(get_session)):
    # 이름이나 아이디에 검색어가 포함된 회원을 찾아냄
    sql = text('''
        select * from users
        where (:keyword = '' or user_name or user_id like :search_keyword)
    ''')

    result = session.execute(sql, {
        'keyword': keyword,
        'search_keyword': '%' + keyword + '%'
    })

    search_list = result.mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-users.html', {
        'user_list': search_list
    })


# [회원 탈퇴/강제 삭제]
@app.get('/api/delete/user/{user_id}')
def delete_user(user_id: str, session: Session = Depends(get_session)):
    print('회원 삭제를 실행합니다', '삭제 ID : ', user_id)
    # 해당 회원의 정보를 창고(DB)에서 완전히 지워버림
    sql = text('''
        delete from users
        where user_id = :user_id
    ''')
    session.execute(sql, {'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)


# ==============================================================================
# 6. 고객 1:1 문의 관리 기능
# ==============================================================================

# [손님들의 문의 목록 조회]
@app.get('/admin/inquiries')
def inquiry_list(request: Request, session: Session = Depends(get_session)):
    print('문의 조회')
    # 고객들이 올린 모든 1:1 문의글을 창고에서 전부 가져옴
    sql = text('''
        select * from inquiry
    ''')
    results = session.execute(sql).mappings().fetchall()

    # 문의 관리 화면(admin-inquiries.html)에 목록을 표시
    return templates.TemplateResponse(request, 'admin-inquiries.html', {
        'inquiry_list': results
    })


# [문의에 관리자 답변 등록하기]
@app.post('/api/answer/{inquiry_id}')
def answer_inquiry(inquiry_id: int, inquiry_answer: str = Form(), session: Session = Depends(get_session)):
    print('문의 답변 등록 실행')
    # 관리자가 적은 답변 글을 저장하고, 문의 처리 상태를 '2'(답변 완료를 의미)로 변경
    sql = text('''
        update inquiry
        set 
            inquiry_answer = :inquiry_answer,
            inquiry_status_id = 2 
        where inquiry_id = :inquiry_id
    ''')
    session.execute(sql, {
        'inquiry_id': inquiry_id,
        'inquiry_answer': inquiry_answer
    })
    session.commit()

    # 답변 완료 후 다시 문의 목록 화면으로 복귀
    return RedirectResponse(url='/admin/inquiries', status_code=303)


# ==============================================================================
# 7. 주문 및 배송 현황 관리
# ==============================================================================

# [손님들의 주문 및 배송 목록 전체 조회]
@app.get('/admin/orders')
def order_list(request: Request, session: Session = Depends(get_session)):
    print('주문/배송 조회')
    # 주문 정보, 주문서, 결제 상태, 배송 상태 등 여러 테이블에 흩어진 정보를 한 번에 엮어서 모아옴
    sql = text('''
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
	    on d.delivery_status_id = ds.delivery_status_id;
    ''')
    results = session.execute(sql).mappings().fetchall()

    # 주문 관리 화면(admin-orders.html)에 목록을 전달해 출력
    return templates.TemplateResponse(request, 'admin-orders.html', {
        'order_list': results
    })


# ==============================================================================
# 8. 상품 예약 관리
# ==============================================================================

# [예약 목록 조회 및 대기 건수 확인]
@app.get('/admin/reservations')
def reservation_list( request: Request,session: Session = Depends(get_session)):
    print('예약 목록 조회')

    # 1) 손님이 신청한 예약 내역(예약자 이름, 상품 이름, 예약 수량, 처리 상태, 예약일, 예약만료일 , 예약순번)을 가져옴
    sql = text('''
        select 
            r.reservation_id,
            u.user_name,
            p.product_name,
            p.product_id,
            p.product_reservation_stock,
            r.reservation_quantity,
            rs.reservation_status_name,
            r.reservation_date,
            r.reservation_expiration,
            (
                select count(*) from reservation 
                where product_id = p.product_id
                and reservation_status_id = 3
                and reservation_id <= r.reservation_id
            ) as reservation_turn  /* 서브 쿼리의 별칭은 괄호 밖에다가 지정을 해야 함.*/
        from reservation as r
        left join product as p 
            on r.product_id = p.product_id
        left join reservation_status as rs
            on r.reservation_status_id = rs.reservation_status_id
        left join users as u
            on r.user_id = u.user_id
    ''')

    # 2) 아직 처리되지 않고 '예약대기' 중인 상태의 총건수를 계산함
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

    # 예약 관리 화면(admin-reservations.html)에 예약 명단과 대기 건수를 함께 표시
    return templates.TemplateResponse(request, 'admin-reservations.html', {
        'reservation_list': results,
        'reservation_wait': results2[0]['count(*)']
    })


# [예약 건 삭제/취소]
@app.get('/api/delete/reservations/{reservation_id}')
def delete_reservation(reservation_id: int, session: Session = Depends(get_session)):
    print('예약 삭제 실행', reservation_id)
    # 선택한 예약 번호를 창고에서 지워버림
    sql = text('''
        delete from reservation
        where  reservation_id = :reservation_id
    ''')
    session.execute(sql, {'reservation_id': reservation_id})
    session.commit()

    return RedirectResponse(url='/admin/reservations', status_code=303)

# [예약 구매 가능 처리]
@app.get('/api/process_purchase/{reservation_id}')
def process_purchace(reservation_id: int, session: Session = Depends(get_session)):
    print('예약 구매 가능 처리를 진행합니다' , '구매 가능 처리 대상 예약 아이디 : ' , reservation_id)
    sql = text('''
        /*
          SELECT로 조회한 내용과 UPDATE를 한 번에 처리하고 싶다면, MariaDB의 
          update ... join 구문을 올바르게 사용해야 하며. select 단어를 제거하고 update로 시작해야 한다고 합니다.
        */
        update reservation as r 
        left join product as p on r.product_id = p.product_id
        set reservation_status_id = 2 
        where 
            p.product_reservation_stock >= r.reservation_quantity and r.reservation_id = :reservation_id
        and (
            /*MariaDB 에러를 피하기 위해 테이블을 한번 감싸줌 (by Google Gemini) */
            /* 
            이렇게 해두면 DB가 알아서 "이 녀석이 정말 1순위가 맞나?" 꼼꼼하게 검사하고, 진짜 1번 대기자일 때만
            '구매 가능(2)' 상태로 허락을 해준다고 합니다. 조건이 안맞으면 아예 업데이트를 안하기 떄문에 
            새치기는 절대로 불가능하다고 합니다. (by Google Gemini)
            */
            select count(*)
            from (select * from reservation) as r2
            where r2.product_id = r.product_id
            and r2.reservation_status_id = 3
            and r2.reservation_id <= r.reservation_id
        ) = 1 
    ''')
    session.execute(sql, {'reservation_id': reservation_id})
    session.commit()
    
    return RedirectResponse(url='/admin/reservations', status_code=303)

# ==============================================================================
# 웹 서버 프로그램 실행 시작점
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    # 외부 접속이 가능하도록 '0.0.0.0' 주소와 '8000' 통로(포트)를 열고 서버를 실행
    # (reload=True는 파이썬 코드를 수정하고 저장하면 알아서 서버가 재시작되는 옵션)
    uvicorn.run("admin:app", port=8000, reload=True, host="0.0.0.0")