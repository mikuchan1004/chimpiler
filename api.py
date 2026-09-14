"""
================================================================================
프로젝트명: 쇼핑몰 & 관리자 시스템 백엔드 API (FastAPI)
설명: 사용자 쇼핑(상품, 장바구니, 예약, 주문), 마이페이지, AI 건강체크,
      고객센터(공지, FAQ, 문의), 관리자 기능(상품, 주문, 문의, 예약, 회원) 총괄
================================================================================
"""

# [DB 및 ORM 설정 모듈]
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy import text, URL

# [FastAPI 핵심 및 웹 관련 모듈]
from fastapi import FastAPI, Request, Depends, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# [세션 및 보안, 유틸리티 모듈]
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime, timedelta
import shutil
import random
from pathlib import Path
from passlib.context import CryptContext

# [DTO 모듈]
from DTO.ProductDTO import Product

# 이미지 업로드 디렉터리 경로 설정
image_dir = Path('static/images')
image_dir.mkdir(parents=True, exist_ok=True)

# FastAPI 애플리케이션 인스턴스 초기화
app = FastAPI()

# 세션 미들웨어 등록 (세션 쿠키 암호화 키 설정)
app.add_middleware(
    SessionMiddleware,
    secret_key='chimpiler-session-key'
)

# 정적 파일(/static 경로) 마운트 및 템플릿 엔진 디렉터리 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='.')

# MariaDB 연결 URL 및 엔진 구성
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username="chimpiler_team",
    password="chimpiler!@#",
    host="192.168.0.65",
    port=3306,
    database="chimpiler",
)
engine = create_engine(DATABASE_URL, echo=True)

# 데이터베이스 세션 제너레이터 (의존성 주입용)
def get_session():
    with Session(engine) as session:
        yield session


####################################
#          공통 설정 및 함수        
####################################

# Jinja2 템플릿 필터: 숫자에 1,000단위 콤마 추가
def price(value):
    return f'{int(value):,}'
templates.env.filters['price'] = price

# 비밀번호 암호화 컨텍스트 설정 (Argon2)
ctx_pw = CryptContext(
    schemes=['argon2'],
    deprecated='auto'
)

def passwordHash(password):
    return ctx_pw.hash(password)

def passwordVerify(input_password, saved_password):
    return ctx_pw.verify(input_password, saved_password)


####################################
#          레이아웃 / 챗봇        
####################################

@app.get('/chat')
def chatBot(answer: str, session: Session = Depends(get_session)):
    """[간이 AI 챗봇 API] 사전 답변 데이터 조회"""
    sql = text('''
        select chat_answer
        from ai_chatbot
        where chat_keyword = :answer
    ''')
    result = session.execute(sql, {'answer': answer})
    chat_result = result.mappings().fetchone()
    return {'chat_result': chat_result}


####################################
#          로그인 관련 구역        
####################################

@app.get('/login')
def login_loading(request: Request):
    """로그인 화면 렌더링"""
    return templates.TemplateResponse(request, 'login.html')

@app.post('/login')
def login(request: Request, user_id: str = Form(), user_password: str = Form(), session: Session = Depends(get_session)):
    """[사용자 로그인 처리] Argon2 검증 및 평문 비밀번호 자동 마이그레이션"""
    sql = text('''
        select * from users
        where user_id = :user_id
    ''')
    result = session.execute(sql, {'user_id': user_id})
    login_check = result.mappings().fetchone()

    if login_check:
        saved_password = login_check['user_password']

        if saved_password is not None:
            if saved_password.startswith('$argon2'):
                password_check = passwordVerify(user_password, saved_password)
            else:
                password_check = (user_password == saved_password)
                if password_check:
                    sql_password_upgrade = text('''
                        update users
                        set user_password = :user_password
                        where user_id = :user_id
                    ''')
                    session.execute(
                        sql_password_upgrade,
                        {
                            'user_password': passwordHash(user_password),
                            'user_id': user_id
                        }
                    )
                    session.commit()

            if password_check:
                request.session['isLogin'] = True
                request.session['user_id'] = user_id
                request.session['user_name'] = login_check['user_name']
                return RedirectResponse(url='/', status_code=303)

    return templates.TemplateResponse(
        request,
        'login.html',
        {'login_error': '아이디 또는 비밀번호가 일치하지 않습니다.'},
        status_code=401
    )


####################################
#          로그아웃 관련 구역        
####################################

@app.get('/logout')
def logout(request: Request):
    """세션 초기화 후 메인 페이지 이동"""
    request.session.clear()
    return RedirectResponse(url='/', status_code=303)


####################################
#          회원가입 관련 구역        
####################################

@app.get('/signup')
def signup(request: Request):
    """회원가입 화면 렌더링"""
    return templates.TemplateResponse(request, 'signup.html')

@app.post('/signup/idcheck')
async def signupIDChk(request: Request, session: Session = Depends(get_session)):
    """[아이디 중복 확인 비동기 API]"""
    data = await request.json()
    request.session.pop('signup_checked_id', None)

    signupUserId = data.get('signupUserId', '').strip()

    if signupUserId == '' or len(signupUserId) > 12 or not signupUserId.isalnum():
        return {
            'result': '아이디 형식을 확인해 주세요.',
            'check': 'failed'
        }

    sql_idcheck = text('select user_id from users where user_id = :user_id')
    result_idcheck = session.execute(sql_idcheck, {'user_id': signupUserId})
    idcheck = result_idcheck.mappings().fetchone()

    if idcheck is None:
        request.session['signup_checked_id'] = signupUserId
        return {
            'result': '사용 가능한 아이디입니다.',
            'check': 'success'
        }

    return {
        'result': '이미 사용 중인 아이디입니다.',
        'check': 'failed'
    }

@app.post('/signup')
def signupData(
    request: Request,
    user_id: str = Form(),
    user_password: str = Form(),
    user_password_confirm: str = Form(),
    user_name: str = Form(),
    user_addr: str = Form(),
    user_addr_detail: str = Form(),
    user_email: str = Form(),
    user_phone: str = Form(),
    session: Session = Depends(get_session)
):
    """[회원가입 처리] 입력값 검증 후 Argon2 암호화 저장"""
    user_id = user_id.strip()
    user_name = user_name.strip()
    user_addr = user_addr.strip()
    user_addr_detail = user_addr_detail.strip()
    user_email = user_email.strip()
    user_phone = user_phone.strip().replace('-', '')

    if not user_phone.isdigit() or len(user_phone) != 11 or not user_phone.startswith('010'):
        return RedirectResponse(url='/signup', status_code=303)

    if not all([user_id, user_password, user_name, user_addr, user_addr_detail, user_email, user_phone]):
        return RedirectResponse(url='/signup', status_code=303)

    if user_password != user_password_confirm:
        return RedirectResponse(url='/signup', status_code=303)

    checked_user_id = request.session.get('signup_checked_id')
    if checked_user_id != user_id:
        return RedirectResponse(url='/signup', status_code=303)

    sql_idcheck = text('select user_id from users where user_id = :user_id')
    result_idcheck = session.execute(sql_idcheck, {'user_id': user_id})
    if result_idcheck.mappings().fetchone() is not None:
        request.session.pop('signup_checked_id', None)
        return RedirectResponse(url='/signup', status_code=303)

    sql_signup = text('''
        insert into users (
            user_id, user_password, user_name, user_email,
            user_phone, user_addr, user_addr_detail
        )
        values (
            :user_id, :user_password, :user_name, :user_email,
            :user_phone, :user_addr, :user_addr_detail
        )
    ''')

    session.execute(sql_signup, {
        'user_id': user_id,
        'user_password': passwordHash(user_password),
        'user_name': user_name,
        'user_email': user_email,
        'user_phone': user_phone,
        'user_addr': user_addr,
        'user_addr_detail': user_addr_detail
    })
    session.commit()

    request.session.pop('signup_checked_id', None)
    return RedirectResponse(url='/login', status_code=303)

@app.get('/terms')
def terms(request: Request):
    """이용약관 페이지 렌더링"""
    return templates.TemplateResponse(request, 'terms.html')


####################################
#          메인 페이지 관련 구역       
####################################

@app.get('/')
def mainPage(request: Request, session: Session = Depends(get_session)):
    """[메인 페이지] 추천 상품 4개 및 조회수 상위 10개 상품 로드"""
    sql = text('select * from product')
    product_list_main = session.execute(sql).mappings().fetchall()

    product_random_main = []
    if len(product_list_main) >= 4:
        while len(product_random_main) < 4:
            check = product_list_main[random.randint(0, len(product_list_main) - 1)].get('product_id', 0)
            if check not in product_random_main:
                product_random_main.append(check)
    else:
        product_random_main = [p.get('product_id', 0) for p in product_list_main] + [0] * (4 - len(product_list_main))

    sql_view = text('''
        select * from product
        order by product_view_count desc
        limit 10
    ''')
    product_view_main = session.execute(sql_view).mappings().fetchall()

    return templates.TemplateResponse(request, 'main.html', {
        'product_list_main': product_list_main,
        'product_view_main': product_view_main,
        'product_view_main_len': len(product_view_main),
        'product_random_1': product_random_main[0],
        'product_random_2': product_random_main[1],
        'product_random_3': product_random_main[2],
        'product_random_4': product_random_main[3],
    })

@app.get('/random_product')
def mainRandomProduct(session: Session = Depends(get_session)):
    """[AJAX/API] 메인 페이지용 무작위 추천 상품 4개 반환"""
    sql = text('select * from product')
    product_list = session.execute(sql).mappings().fetchall()

    product_random = []
    if len(product_list) >= 4:
        while len(product_random) < 4:
            check = product_list[random.randint(0, len(product_list) - 1)].get('product_id', 0)
            if check not in product_random:
                product_random.append(check)
    else:
        product_random = [p.get('product_id', 0) for p in product_list] + [0] * (4 - len(product_list))

    return {
        'product_list': product_list,
        'product_random_1': product_random[0],
        'product_random_2': product_random[1],
        'product_random_3': product_random[2],
        'product_random_4': product_random[3]
    }


####################################
#          전체 상품 관련 구역       
####################################

@app.get('/products')
def products(
    request: Request, 
    page: int = 1,
    category_id: int = 0,
    align: str = 'align_view',
    keyword: str = '',
    session: Session = Depends(get_session)
):
    """[상품 목록] 카테고리/키워드 필터링, 정렬, 페이징(8개씩)"""
    if page < 1:
        page = 1

    if align == 'align_price_low':
        order = 'product_price'
    elif align == 'align_price_high':
        order = 'product_price desc'
    elif align == 'align_name':
        order = 'product_name'
    else:
        order = 'product_view_count desc'

    page_view = (page * 8) - 8

    sql = text(f'''
        select * from product
        where (:category_id = 0 or category_id = :category_id)
        and (:keyword = '' or product_name like :search_keyword)
        order by {order}, product_id
        limit :page_view, 8
    ''')

    result = session.execute(sql, {
        'category_id': category_id,
        'keyword': keyword,
        'search_keyword': '%' + keyword + '%',
        'page_view': page_view
    }) 
    product_list = result.mappings().fetchall()

    sql_count = text('''
        select count(*) as product_count
        from product
        where (:category_id = 0 or category_id = :category_id)
        and (:keyword = '' or product_name like :search_keyword)
    ''')
    result_count = session.execute(sql_count, {
        'category_id': category_id,
        'keyword': keyword,
        'search_keyword': '%' + keyword + '%'
    })
    product_count = result_count.mappings().fetchall()[0]['product_count']

    total_page = int(product_count / 8) + (1 if product_count % 8 != 0 else 0)

    return templates.TemplateResponse(request, 'products.html', {
        'product_list': product_list,
        'product_count': product_count,
        'total_page': total_page,
        'page': page,
        'category_id': category_id,
        'align': align,
        'keyword': keyword
    })


####################################
#          상품 상세 관련 구역        
####################################

@app.get('/product/detail/{product_id}')
def productsDetail(request: Request, product_id: int, reservation: str = None, session: Session = Depends(get_session)):
    """[상품 상세] 조회수 1 증가, 상품 정보, 리뷰 목록, 평균 별점, 예약 대기 순번 조회"""
    sql = text('''
        select * from product p
        join category as c on (p.category_id = c.category_id)
        where product_id = :product_id
    ''')
    product_list = session.execute(sql, {'product_id': product_id}).mappings().fetchall()

    # 조회수 증가
    sql_view_count = text('''
        update product
        set product_view_count = product_view_count + 1
        where product_id = :product_id
    ''')
    session.execute(sql_view_count, {'product_id': product_id})
    session.commit()

    # 리뷰 및 평점 조회
    sql_review = text('''
        select pr.* , us.user_name from product_review as pr
        join users as us on (pr.user_id = us.user_id)
        where pr.product_id = :product_id
        order by pr.product_review_id desc
    ''')
    review_list = session.execute(sql_review, {'product_id': product_id}).mappings().fetchall()

    sql_rating = text('''
        select round(avg(product_rating), 1) as rating_avg, count(*) as review_count
        from product_review
        where product_id = :product_id
    ''')
    rating = session.execute(sql_rating, {'product_id': product_id}).mappings().fetchone()
    rating_avg = rating['rating_avg'] if rating['rating_avg'] is not None else 0

    # 신규 예약 배정 순번 계산
    sql_reservation_turn = text('''
        select count(*) + 1 as reservation_turn from reservation 
        where product_id = :product_id and reservation_status_id = 3
    ''')
    reservation_turn = session.execute(sql_reservation_turn, {'product_id': product_id}).mappings().fetchone()

    return templates.TemplateResponse(request, 'product-detail.html', {
        'product_list': product_list,
        'review_list': review_list,
        'rating_avg': rating_avg,
        'review_count': rating['review_count'],
        'reservation': reservation,
        'reservation_turn': reservation_turn
    })

@app.post('/product/review')
def productReview(
    request: Request,
    product_id: int = Form(), 
    review_score: int = Form(), 
    review_content: str = Form(),
    session: Session = Depends(get_session)
):
    """[상품 리뷰 등록]"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    if review_score < 1 or review_score > 5 or review_content.strip() == '':
        return RedirectResponse(url=f'/product/detail/{product_id}', status_code=303)

    sql = text('''
        insert into product_review (product_review, product_rating, product_id, user_id)
        values (:product_review, :product_rating, :product_id, :user_id)
    ''')
    session.execute(sql, {
        'product_review': review_content,
        'product_rating': review_score,
        'product_id': product_id,
        'user_id': user_id
    })
    session.commit()

    return RedirectResponse(url=f'/product/detail/{product_id}', status_code=303)

@app.post('/product/review/report')
def productReviewReport(
    request: Request,
    product_review_id: int = Form(), 
    product_id: int = Form(), 
    report_detail: str = Form(),
    session: Session = Depends(get_session)
):
    """[불량 리뷰 신고 접수]"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    report_detail = report_detail.strip()
    if report_detail == '':
        return RedirectResponse(url=f'/product/detail/{product_id}', status_code=303)

    sql_report = text('''
        insert into review_report(report_detail, product_review_id)
        values (:report_detail, :product_review_id)
    ''')
    session.execute(sql_report, {
        'report_detail': report_detail,
        'product_review_id': product_review_id
    })
    session.commit()

    return RedirectResponse(url=f'/product/detail/{product_id}', status_code=303)

@app.post('/product/reservation')
def productReservation(
    request: Request,
    product_id: int = Form(), 
    reservation_quantity: int = Form(),
    session: Session = Depends(get_session)
):
    """[상품 예약 신청] 상태: 3(예약대기)"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    if reservation_quantity <= 0 or reservation_quantity > 10:
        return RedirectResponse(url=f'/product/detail/{product_id}?reservation=failed', status_code=303)

    sql_reservation = text('''
        insert into reservation(reservation_date, reservation_quantity, product_id, user_id, reservation_status_id)
        values(:reservation_date, :reservation_quantity, :product_id, :user_id, :reservation_status_id)
    ''')
    session.execute(sql_reservation, {
        'reservation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
        'reservation_quantity': reservation_quantity, 
        'product_id': product_id, 
        'user_id': user_id, 
        'reservation_status_id': 3
    })
    session.commit()

    return RedirectResponse(url=f'/product/detail/{product_id}?reservation=success', status_code=303)


####################################
#          장바구니 관련 구역       
####################################

@app.get('/cart')
def cart(request: Request, session: Session = Depends(get_session)):
    """[장바구니 목록 조회]"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    sql_cart = text('''
        select
            ca.cart_id, ca.product_quantity, pr.product_id,
            pr.product_name, pr.product_image, pr.product_price,
            pr.product_sale_stock, pr.product_active
        from cart as ca
        join product as pr on ca.product_id = pr.product_id
        where ca.user_id = :user_id
        order by ca.cart_id desc
    ''')
    cart_list = session.execute(sql_cart, {'user_id': user_id}).mappings().fetchall()

    sql_cart_total_price = text('''
        select sum(ca.product_quantity * pr.product_price) as total_price
        from cart as ca
        join product as pr on ca.product_id = pr.product_id
        where ca.user_id = :user_id
        order by ca.cart_id desc;
    ''')
    result_cart_total_price = session.execute(sql_cart_total_price, {'user_id': user_id}).mappings().fetchone()
    cart_total_price = result_cart_total_price['total_price'] if result_cart_total_price['total_price'] is not None else 0

    return templates.TemplateResponse(request, 'cart.html', {
        'cart_list': cart_list,
        'cart_total_price': cart_total_price
    })

@app.post('/cart')
def cartAdd(
    request: Request,
    cart_quantity: int = Form(),
    product_id: int = Form(),
    session: Session = Depends(get_session)
):
    """[장바구니 담기] 기존 상품 수량 누적 또는 신규 등록"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    if cart_quantity < 1:
        return RedirectResponse(url=f'/product/detail/{product_id}', status_code=303)

    sql_cart_get = text('''
        select * from cart
        where user_id = :user_id and product_id = :product_id
    ''')
    result_cart = session.execute(sql_cart_get, {'user_id': user_id, 'product_id': product_id}).mappings().fetchone()

    if result_cart is None:
        sql_cart_add = text('''
            insert into cart(user_id, product_id, product_quantity)
            values(:user_id, :product_id, :product_quantity)
        ''')
        session.execute(sql_cart_add, {
            'user_id': user_id,
            'product_id': product_id,
            'product_quantity': cart_quantity
        })
    else:
        sql_cart_update = text('''
            update cart
            set product_quantity = product_quantity + :product_quantity
            where user_id = :user_id and product_id = :product_id
        ''')
        session.execute(sql_cart_update, {
            'product_quantity': cart_quantity,
            'user_id': user_id,
            'product_id': product_id
        })
    session.commit()

    return RedirectResponse(url='/cart', status_code=303)

@app.post('/cart/delete')
def cartDelete(request: Request, cart_id: int = Form(), session: Session = Depends(get_session)):
    """[장바구니 개별 삭제]"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    sql_delete = text('delete from cart where cart_id = :cart_id and user_id = :user_id')
    session.execute(sql_delete, {'cart_id': cart_id, 'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/cart', status_code=303)

@app.post('/cart/update')
def cartUpdate(
    request: Request, 
    cart_id: int = Form(), 
    product_quantity: int = Form(),
    session: Session = Depends(get_session)
):
    """[장바구니 수량 수정] (1~10개 제한)"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    if product_quantity < 1 or product_quantity > 10:
        return RedirectResponse(url='/cart', status_code=303)

    sql_update = text('''
        update cart
        set product_quantity = :product_quantity
        where cart_id = :cart_id and user_id = :user_id 
    ''')
    session.execute(sql_update, {
        'cart_id': cart_id,
        'user_id': user_id,
        'product_quantity': product_quantity
    })
    session.commit()

    return RedirectResponse(url='/cart', status_code=303)

@app.post('/cart/deleteSelect')
def cartDeleteSelect(
    request: Request,
    deleteSelectList: list[int],
    session: Session = Depends(get_session)
):
    """[장바구니 다중 선택 삭제 API]"""
    if len(deleteSelectList) == 0:
        return {'result': '삭제할 상품을 선택해 주세요.'}

    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    deleteList = ','.join(map(str, deleteSelectList))

    sql_deleteSelect = text(f'''
        select count(*) as deleteCount from cart
        where user_id = :user_id
        and cart_id in ({deleteList})
    ''')
    deleteSelect = session.execute(sql_deleteSelect, {'user_id': user_id}).mappings().fetchone()
    deleteCount = deleteSelect['deleteCount']

    sql_delete = text(f'''
        delete from cart
        where user_id = :user_id
        and cart_id in ({deleteList})
    ''')
    session.execute(sql_delete, {'user_id': user_id})
    session.commit()

    return {'result': f'총 {deleteCount}건이 삭제되었습니다.'}


####################################
#          관리자 페이지 관련 구역       
####################################

@app.get('/admin')
def dashboard(request: Request, session: Session = Depends(get_session)):
    """[관리자 대시보드]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    sql1 = text('select count(*) from product where product_sale_stock = 0;')
    results1 = session.execute(sql1).mappings().fetchall()

    sql2 = text('select count(*) from inquiry where inquiry_status_id = 1;')
    results2 = session.execute(sql2).mappings().fetchall()

    sql3 = text('''
        select 
            o.order_sheet_id, o.user_id, o.order_name, os.order_total_price,
            st.order_status_name, ds.delivery_status_name, ps.payment_status_name
        from orders o 
        left join order_sheet os on o.order_sheet_id = os.order_sheet_id
        left join order_status st on o.order_status_id = st.order_status_id
        left join delivery d on os.order_sheet_id = d.order_sheet_id
        left join delivery_status ds on d.delivery_status_id = ds.delivery_status_id
        left join payment as p on os.order_sheet_id = p.order_sheet_id
        left join payment_status as ps on p.payment_status_id = ps.payment_status_id
    ''')
    results3 = session.execute(sql3).mappings().fetchall()

    sql4 = text('select count(*) from orders')
    results4 = session.execute(sql4).mappings().fetchall()

    sql5 = text('select count(*) from reservation')
    results5 = session.execute(sql5).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-dashboard.html', {
        'sold_count': results1[0]['count(*)'],
        'inquiry_count': results2[0]['count(*)'],
        'recent_orders': results3,
        'order_count': results4[0]['count(*)'],
        'reservation_count': results5[0]['count(*)']
    })

@app.get('/error-404')
def adminError(request: Request):
    """접근 제한 화면"""
    return templates.TemplateResponse(request, 'error-404.html')

@app.get('/admin/inquiries')
def inquiry_list(request: Request, session: Session = Depends(get_session)):
    """[관리자] 1:1 문의 목록"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    sql = text('select * from inquiry')
    results = session.execute(sql).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-inquiries.html', {
        'inquiry_list': results
    })

@app.post('/admin/inquiries/answer/{inquiry_id}')
def answer_inquiry(inquiry_id: int, inquiry_answer: str = Form(), session: Session = Depends(get_session)):
    """[관리자] 문의 답변 등록 (상태: 2 답변완료)"""
    sql = text('''
        update inquiry
        set 
            inquiry_answer = :inquiry_answer,
            inquiry_status_id = 2,
            inquiry_answer_date = NOW()
        where inquiry_id = :inquiry_id
    ''')
    session.execute(sql, {
        'inquiry_id': inquiry_id,
        'inquiry_answer': inquiry_answer
    })
    session.commit()

    return RedirectResponse(url='/admin/inquiries', status_code=303)

@app.get('/admin/orders')
def order_list(request: Request, session: Session = Depends(get_session)):
    """[관리자] 주문 목록 조회"""
    sql = text('''
        select 
            o.order_sheet_id, o.user_id, o.order_name, os.order_total_price,
            st.order_status_name, ds.delivery_status_name, ps.payment_status_name
        from orders o
        left join order_sheet os on o.order_sheet_id = os.order_sheet_id
        left join order_status st on o.order_status_id = st.order_status_id
        left join delivery d on os.order_sheet_id = d.order_sheet_id
        left join delivery_status ds on d.delivery_status_id = ds.delivery_status_id
        left join payment as p on os.order_sheet_id = p.order_sheet_id
        left join payment_status as ps on p.payment_status_id = ps.payment_status_id
    ''')
    results = session.execute(sql).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-orders.html', {
        'order_list': results
    })

@app.get('/admin/orders/refund_product/{order_sheet_id}')
def repund_product(order_sheet_id: int, session: Session = Depends(get_session)):
    """[관리자] 결제완료 주문 환불/취소 처리"""
    sql = text('''
        update orders as o 
        left join order_sheet as os on o.order_sheet_id = os.order_sheet_id 
        left join payment as p on os.order_sheet_id = p.order_sheet_id
        left join payment_status as ps on p.payment_status_id = ps.payment_status_id
        set p.payment_status_id = 4
        where ps.payment_status_name = '결제완료' and o.order_sheet_id = :order_sheet_id
    ''')
    session.execute(sql, {'order_sheet_id': order_sheet_id})
    session.commit()

    return RedirectResponse(url='/admin/orders', status_code=303)

@app.get('/admin/orders/delivery_complete/{order_sheet_id}')
def delivery_complete(order_sheet_id: int, session: Session = Depends(get_session)):
    """[관리자] 배송 완료 처리"""
    sql = text('''
        update orders as o 
        left join order_sheet as ot on o.order_sheet_id = ot.order_sheet_id
        left join order_status as os on o.order_sheet_id = os.order_status_id
        left join delivery as d on ot.order_sheet_id = d.order_sheet_id
        left join delivery_status as ds on d.delivery_status_id = ds.delivery_status_id
        left join payment as p on ot.order_sheet_id = p.order_sheet_id
        left join payment_status as ps on p.payment_status_id = ps.payment_status_id
        set
            d.delivery_status_id = 3,
            d.delivery_start_date = IFNULL(d.delivery_start_date, NOW()), 
            d.delivery_complete_date = NOW()
        where ps.payment_status_id = 2 and o.order_sheet_id = :order_sheet_id
    ''')
    session.execute(sql, {'order_sheet_id': order_sheet_id})
    session.commit()

    return RedirectResponse(url='/admin/orders', status_code=303)

@app.get('/admin/products')
def product_list(request: Request, session: Session = Depends(get_session)):
    """[관리자] 상품 목록"""
    sql = text('select * from product')
    results = session.execute(sql).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-products.html', {
        'product_list': results
    })

@app.post('/admin/product/add')
def add_product(
    product: Product = Depends(Product.as_form),
    product_image: UploadFile = File(),
    session: Session = Depends(get_session)
):
    """[관리자] 신규 상품 추가 (고유 타임스탬프 파일명 저장)"""
    try:
        params = product.model_dump()

        if product_image is not None and product_image.filename:
            original_filename = Path(product_image.filename).name
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{original_filename}"
            image_path = image_dir / filename

            with image_path.open('wb') as buffer:
                shutil.copyfileobj(product_image.file, buffer)

            params['product_image'] = f'static/images/{filename}'
        else:
            params['product_image'] = ''

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
        session.rollback()
        print('상품 추가 중 오류 발생:', e)

    return RedirectResponse(url='/admin/products', status_code=303)

@app.post('/admin/product/modify')
def update_product(
    product: Product = Depends(Product.as_form),
    product_image: UploadFile = File(None),
    session: Session = Depends(get_session)
):
    """[관리자] 상품 수정 (새 이미지가 있을 때만 파일 저장 및 업데이트)"""
    try:
        params = product.model_dump()
        params['product_image'] = None

        if product_image is not None and product_image.filename:
            original_filename = Path(product_image.filename).name
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{original_filename}"
            image_path = image_dir / filename

            with image_path.open('wb') as buffer:
                shutil.copyfileobj(product_image.file, buffer)

            params['product_image'] = f'static/images/{filename}'

        sql = text('''
            update product
            set 
                product_brand = :product_brand,
                product_name = :product_name,
                product_detail = :product_detail, 
                product_image = coalesce(:product_image, product_image),
                product_price = :product_price, 
                product_sale_stock = :product_sale_stock,
                product_reservation_stock = :product_reservation_stock,
                category_id = :category_id
            where product_id = :product_id
        ''')
        session.execute(sql, params)
        session.commit()
    except Exception as e:
        session.rollback()
        print('상품 수정 중 오류 발생:', e)

    return RedirectResponse(url='/admin/products', status_code=303)

@app.get('/admin/product/{product_id}')
def delete_product(product_id: int, session: Session = Depends(get_session)):
    """[관리자] 상품 삭제"""
    try:
        sql = text('delete from product where product_id = :product_id')
        session.execute(sql, {'product_id': product_id})
        session.commit()
    except Exception as e:
        session.rollback()
        print('상품 삭제 중 오류 발생:', e)

    return RedirectResponse(url='/admin/products', status_code=303)

@app.get('/admin/product/soldout/{product_id}')
def soldout_product(product_id: int, session: Session = Depends(get_session)):
    """[관리자] 상품 품절(2) 처리"""
    try:
        sql = text('update product set product_active = 2 where product_id = :product_id')
        session.execute(sql, {'product_id': product_id})
        session.commit()
    except Exception as e:
        session.rollback()
        print('품절 변경 실패:', e)
        return RedirectResponse(url='/admin/products?result=failed', status_code=303)

    return RedirectResponse(url='/admin/products', status_code=303)

@app.get('/admin/product/available/{product_id}')
def available_product(product_id: int, session: Session = Depends(get_session)):
    """[관리자] 상품 판매중(1) 처리"""
    try:
        sql = text('update product set product_active = 1 where product_id = :product_id')
        session.execute(sql, {'product_id': product_id})
        session.commit()
    except Exception as e:
        session.rollback()
        print('판매중 변경 실패:', e)
        return RedirectResponse(url='/admin/products?result=failed', status_code=303)

    return RedirectResponse(url='/admin/products', status_code=303)

@app.post('/admin/product/restock')
def restock_product(
    product_id: int = Form(),
    product_sale_stock: int = Form(),
    product_reservation_stock: int = Form(),
    session: Session = Depends(get_session)
):
    """[관리자] 재고 변경"""
    try:
        sql = text('''
            update product 
            set
                product_sale_stock = :product_sale_stock,
                product_reservation_stock = :product_reservation_stock
            where product_id = :product_id
        ''')
        session.execute(sql, {
            'product_id': product_id,
            'product_sale_stock': product_sale_stock,
            'product_reservation_stock': product_reservation_stock
        })
        session.commit()
    except Exception as e:
        session.rollback()
        print('재고 수정 실패:', e)
        return RedirectResponse(url='/admin/products?result=failed', status_code=303)

    return RedirectResponse(url='/admin/products', status_code=303)

@app.get('/admin/product/search')
def search_product(request: Request, keyword: str = "", session: Session = Depends(get_session)):
    """[관리자] 상품명 검색"""
    sql = text('''
        select * from product
        where (:keyword = '' or product_name like :search_keyword)
    ''')
    result = session.execute(sql, {
        'keyword': keyword,
        'search_keyword': '%' + keyword + '%'
    })
    search_product_list = result.mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-products.html', {
        'product_list': search_product_list
    })

@app.get('/admin/reservations')
def reservation_list(request: Request, session: Session = Depends(get_session)):
    """[관리자] 예약 목록 및 대기 순번 조회"""
    sql = text('''
        select 
            r.reservation_id, u.user_name, p.product_name, p.product_id,
            p.product_reservation_stock, r.reservation_quantity,
            rs.reservation_status_name, r.reservation_date, r.reservation_expiration,
            (
                select count(*) from reservation 
                where product_id = p.product_id
                and reservation_status_id = 3
                and reservation_id <= r.reservation_id
            ) as reservation_turn
        from reservation as r
        left join product as p on r.product_id = p.product_id
        left join reservation_status as rs on r.reservation_status_id = rs.reservation_status_id
        left join users as u on r.user_id = u.user_id
    ''')

    sql2 = text('''
        select count(*) from reservation as r 
        left join reservation_status as rs on r.reservation_status_id = rs.reservation_status_id
        where rs.reservation_status_name = '예약대기'
    ''')

    results = session.execute(sql).mappings().fetchall()
    results2 = session.execute(sql2).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-reservations.html', {
        'reservation_list': results,
        'reservation_wait': results2[0]['count(*)']
    })

@app.get('/admin/reservations/delete/{reservation_id}') 
def delete_reservation(reservation_id: int, session: Session = Depends(get_session)):
    """[관리자] 예약 삭제"""
    sql = text('delete from reservation where reservation_id = :reservation_id')
    session.execute(sql, {'reservation_id': reservation_id})
    session.commit()

    return RedirectResponse(url='/admin/reservations', status_code=303)

@app.get('/admin/reservations/process_purchase/{reservation_id}') 
def process_purchace(reservation_id: int, session: Session = Depends(get_session)):
    """[관리자] 예약 대기 1순위 구매 허용 승인 (유효기간 1일 부여)"""
    sql = text('''
        update reservation as r 
        left join product as p on r.product_id = p.product_id
        set 
            reservation_status_id = 2,
            reservation_expiration = DATE_ADD(NOW(), INTERVAL 1 DAY)
        where 
            p.product_reservation_stock >= r.reservation_quantity and r.reservation_id = :reservation_id
        and (
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

@app.get('/admin/users')
def user_list(request: Request, session: Session = Depends(get_session)):
    """[관리자] 회원 및 불량 리뷰 신고 내역 조회"""
    sql1 = text('select * from users')
    results1 = session.execute(sql1).mappings().fetchall()

    sql2 = text('''
        select rr.report_id, pr.user_id, us.user_name, pr.product_review, pr.product_review_id, rr.report_detail 
        from product_review as pr
        join review_report as rr on (pr.product_review_id = rr.product_review_id)
        join users as us on (pr.user_id = us.user_id)
    ''')
    results2 = session.execute(sql2).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-users.html', {
        'user_list': results1,
        'review_report_list': results2
    }) 

@app.post("/admin/users/report/delete/{product_review_id}")
def report_delete(product_review_id: int, session: Session = Depends(get_session)):
    """[관리자] 리뷰 신고 내역 삭제"""
    sql = text('delete from review_report where product_review_id = :product_review_id')
    session.execute(sql, {'product_review_id': product_review_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)

@app.get('/admin/users/warning/{user_id}')
def user_warning(user_id: str, session: Session = Depends(get_session)):
    """[관리자] 회원 경고 누적 및 자동 상태 변경 (5회 경고, 10회 정지)"""
    sql = text('''
        update users
        set user_warning_count = user_warning_count + 1
        where user_id = :user_id
    ''')
    sql2 = text('''
        update users
        set user_status = '경고'
        where user_warning_count >= 5 and user_id = :user_id
    ''')
    sql3 = text('''
        update users 
        set user_status = '정지'
        where user_warning_count >= 10 and user_id = :user_id
    ''')

    session.execute(sql, {'user_id': user_id})
    session.execute(sql2, {'user_id': user_id})
    session.execute(sql3, {'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)

@app.get('/admin/users/warning/delete/{user_id}')
def user_warning_delete(user_id: str, session: Session = Depends(get_session)):
    """[관리자] 회원 경고 1회 차감"""
    sql = text('''
        update users 
        set user_warning_count = user_warning_count - 1
        where user_id = :user_id and user_warning_count >= 1
    ''')
    session.execute(sql, {'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)

@app.get('/admin/users/suspension/{user_id}')
def user_suspension(user_id: str, session: Session = Depends(get_session)):
    """[관리자] 회원 정지"""
    sql = text("update users set user_status = '정지' where user_id = :user_id")
    session.execute(sql, {'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)

@app.get('/admin/users/unsuspend/{user_id}')
def user_unsuspend(user_id: str, session: Session = Depends(get_session)):
    """[관리자] 회원 정지 해제"""
    sql = text("update users set user_status = '정상' where user_id = :user_id")
    session.execute(sql, {'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/admin/users', status_code=303)

@app.get('/admin/users/search')
def search_user(request: Request, keyword: str = "", session: Session = Depends(get_session)):
    """[관리자] 회원 검색"""
    sql = text('''
        select *
        from users
        where (
            :keyword = ''
            or user_name like :search_keyword
            or user_id like :search_keyword
        )
        order by user_id
    ''')
    result = session.execute(sql, {
        'keyword': keyword,
        'search_keyword': f'%{keyword}%'
    })
    search_list = result.mappings().fetchall()

    sql_report = text('''
        select
            rr.report_id, pr.user_id, us.user_name, pr.product_review,
            pr.product_review_id, rr.report_detail
        from product_review as pr
        join review_report as rr on pr.product_review_id = rr.product_review_id
        join users as us on pr.user_id = us.user_id
    ''')
    review_report_list = session.execute(sql_report).mappings().fetchall()

    return templates.TemplateResponse(
        request,
        'admin-users.html',
        {
            'user_list': search_list,
            'review_report_list': review_report_list
        }
    )

@app.get('/admin/users/delete/{user_id}')
def delete_user(user_id: str, session: Session = Depends(get_session)):
    """[관리자] 회원 영구 삭제 (오류 수정 완료)"""
    try:
        sql = text('delete from users where user_id = :user_id')
        session.execute(sql, {'user_id': user_id})
        session.commit()
        return RedirectResponse(url='/admin/users?delete_result=success', status_code=303)
    except Exception as e:
        session.rollback()
        print('회원 삭제 오류:', e)
        return RedirectResponse(url='/admin/users?delete_result=failed', status_code=303)


####################################
#          AI 건강진단 관련 구역       
####################################

@app.get('/ai-health')
def aiHealth(request: Request):
    """AI 건강 체크 진단 폼"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    return templates.TemplateResponse(
        request,
        'ai-health.html',
        {
            'health_result': None,
            'recommended_product_list': [],
            'clinic_search_keyword': ''
        }
    )

@app.post('/ai-health')
def aiHealthData(
    request: Request,
    health_weight: float = Form(),
    health_age: int = Form(),
    health_gender: str = Form(),
    health_sleep: float = Form(),
    health_activity: int = Form(),
    session: Session = Depends(get_session)
):
    """[AI 건강 체크] 키워드 분류 및 상품 추천"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    if not (20 <= health_weight <= 300) or not (1 <= health_age <= 120) or \
       health_gender not in ['남성', '여성', '기타'] or not (0 <= health_sleep <= 24) or \
       not (0 <= health_activity <= 14):
        return RedirectResponse(url='/ai-health', status_code=303)

    if health_sleep < 6:
        health_keyword = 'sleep'
    elif health_age >= 60:
        health_keyword = 'health_device'
    elif health_activity < 2:
        health_keyword = 'fitness'
    else:
        health_keyword = 'nutrition'

    sql_health_keyword = text('''
        select health_keyword_id, health_keyword, health_answer, clinic_search_keyword
        from ai_health_keyword
        where health_keyword = :health_keyword
    ''')
    result_health_keyword = session.execute(sql_health_keyword, {'health_keyword': health_keyword})
    health_keyword_result = result_health_keyword.mappings().fetchone()

    if health_keyword_result is None:
        return RedirectResponse(url='/ai-health', status_code=303)

    health_keyword_id = health_keyword_result['health_keyword_id']
    health_result = health_keyword_result['health_answer']
    clinic_search_keyword = health_keyword_result['clinic_search_keyword']

    sql_health_insert = text('''
        insert into ai_health
        (
            health_weight, health_age, health_gender, health_sleep,
            health_activity, health_result, health_keyword_id, user_id
        )
        values
        (
            :health_weight, :health_age, :health_gender, :health_sleep,
            :health_activity, :health_result, :health_keyword_id, :user_id
        )
    ''')
    result_health_insert = session.execute(sql_health_insert, {
        'health_weight': health_weight,
        'health_age': health_age,
        'health_gender': health_gender,
        'health_sleep': health_sleep,
        'health_activity': health_activity,
        'health_result': health_result,
        'health_keyword_id': health_keyword_id,
        'user_id': user_id
    })
    health_id = result_health_insert.lastrowid

    sql_recommended_product = text('''
        select pr.product_id, pr.product_name, pr.product_image,
               pr.product_price, pr.product_sale_stock, pr.product_active
        from product_health_keyword as phk
        join product as pr on phk.product_id = pr.product_id
        where phk.health_keyword_id = :health_keyword_id
        and pr.product_active = 1
        order by rand()
        limit 3
    ''')
    result_recommended_product = session.execute(sql_recommended_product, {
        'health_keyword_id': health_keyword_id
    })
    recommended_product_list = result_recommended_product.mappings().fetchall()

    sql_recommendation_insert = text('''
        insert into ai_health_recommendation (health_id, product_id, recommendation_rank)
        values (:health_id, :product_id, :recommendation_rank)
    ''')

    for rank, prod in enumerate(recommended_product_list, start=1):
        session.execute(sql_recommendation_insert, {
            'health_id': health_id,
            'product_id': prod['product_id'],
            'recommendation_rank': rank
        })

    session.commit()

    return templates.TemplateResponse(
        request,
        'ai-health.html',
        {
            'health_result': health_result,
            'recommended_product_list': recommended_product_list,
            'clinic_search_keyword': clinic_search_keyword
        }
    )


####################################
#          상품 주문 관련 구역       
####################################

@app.get('/checkout')
def checkout(request: Request, session: Session = Depends(get_session)):
    """[주문서 작성 페이지]"""
    user_id = request.session.get('user_id')
    checkout_type = request.session.get('checkout_type')
    product_id = request.session.get('checkout_product_id')
    buy_quantity = request.session.get('checkout_quantity')
    cartBuyList = request.session.get('checkout_cart_ids')

    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    if checkout_type in ['direct', 'reservation']:
        if product_id is None or buy_quantity is None:
            redirect_target = '/products' if checkout_type == 'direct' else '/mypage/reservations'
            return RedirectResponse(url=redirect_target, status_code=303)
    elif checkout_type == 'cart':
        if cartBuyList is None or len(cartBuyList) == 0:
            return RedirectResponse(url='/cart', status_code=303)
    else:
        return RedirectResponse(url='/products', status_code=303)

    if checkout_type in ['direct', 'reservation']:
        sql_checkout = text('select * from product where product_id = :product_id')
        checkout_product = session.execute(sql_checkout, {'product_id': product_id}).mappings().fetchone()
        if checkout_product is None:
            return RedirectResponse(url='/products', status_code=303)

    elif checkout_type == 'cart':
        cartList = ','.join(map(str, cartBuyList))
        sql_checkout = text(f'''
            select
                ca.cart_id, ca.product_quantity, pr.product_id, pr.product_name,
                pr.product_image, pr.product_price, pr.product_sale_stock, pr.product_active
            from cart as ca
            join product as pr on ca.product_id = pr.product_id
            where ca.user_id = :user_id and ca.cart_id in ({cartList})
        ''')
        checkout_product = session.execute(sql_checkout, {'user_id': user_id}).mappings().fetchall()

        if len(checkout_product) != len(cartBuyList):
            return RedirectResponse(url='/cart', status_code=303)

    sql_checkout_user = text('select * from users where user_id = :user_id')
    checkout_user = session.execute(sql_checkout_user, {'user_id': user_id}).mappings().fetchone()
    if checkout_user is None:
        request.session.clear()
        return RedirectResponse(url='/login', status_code=303)

    if checkout_type == 'cart':
        checkout_total_price = sum(prod['product_price'] * prod['product_quantity'] for prod in checkout_product)
    else:
        checkout_total_price = checkout_product['product_price'] * buy_quantity

    return templates.TemplateResponse(request, 'checkout.html', {
        'checkout_type': checkout_type,
        'checkout_product': checkout_product,
        'buy_quantity': buy_quantity,
        'checkout_total_price': checkout_total_price,
        'checkout_user': checkout_user
    })

@app.post('/checkout/direct')
def checkoutBuy(request: Request, buy_quantity: int = Form(), product_id: int = Form(), session: Session = Depends(get_session)):
    """[바로구매 세션 등록]"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    if buy_quantity < 1:
        return RedirectResponse(url=f'/product/detail/{product_id}', status_code=303)

    sql_checkout = text('select * from product where product_id = :product_id')
    product = session.execute(sql_checkout, {'product_id': product_id}).mappings().fetchone()

    if product is None or product['product_active'] != 1 or buy_quantity > product['product_sale_stock']:
        return RedirectResponse(url=f'/product/detail/{product_id}', status_code=303)

    request.session['checkout_product_id'] = product_id
    request.session['checkout_quantity'] = buy_quantity
    request.session['checkout_type'] = 'direct'

    return RedirectResponse(url='/checkout', status_code=303)

@app.post('/checkout/reservation')
def checkOutReservation(
    request: Request, 
    product_id: int = Form(), 
    reservation_quantity: int = Form(), 
    reservation_id: int = Form(),
    session: Session = Depends(get_session)
):
    """[예약 구매 세션 등록] 상태: 2(구매가능) 검증"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    sql_reservation_check = text('''
        select *
        from reservation
        where reservation_id = :reservation_id
        and user_id = :user_id
        and product_id = :product_id
        and reservation_quantity = :reservation_quantity
        and reservation_status_id = 2
    ''')
    result_reservation_check = session.execute(sql_reservation_check, {
        'reservation_id': reservation_id,
        'user_id': user_id,
        'product_id': product_id,
        'reservation_quantity': reservation_quantity
    })
    if result_reservation_check.mappings().fetchone() is None or reservation_quantity < 1:
        return RedirectResponse(url='/mypage/reservations', status_code=303)

    sql_checkout = text('select * from product where product_id = :product_id')
    product = session.execute(sql_checkout, {'product_id': product_id}).mappings().fetchone()

    if product is None or product['product_active'] != 1 or reservation_quantity > product['product_reservation_stock']:
        return RedirectResponse(url='/mypage/reservations', status_code=303)

    request.session['checkout_product_id'] = product_id
    request.session['checkout_quantity'] = reservation_quantity
    request.session['checkout_type'] = 'reservation'
    request.session['checkout_reservation_id'] = reservation_id

    return RedirectResponse(url='/checkout', status_code=303)

@app.post('/checkout/cart')
def cartCheckoutSelect(request: Request, cartBuyList: list[int], session: Session = Depends(get_session)):
    """[장바구니 선택 상품 주문 세션 등록]"""
    if len(cartBuyList) == 0:
        return {'result': '주문하실 상품을 선택해 주세요.'}

    user_id = request.session.get('user_id')
    if user_id is None:
        return {'result': 'login'}

    cartList = ','.join(map(str, cartBuyList))
    sql_cartSelect = text(f'''
        select count(*) as buyCount from cart
        where user_id = :user_id and cart_id in ({cartList})
    ''')
    cartSelect = session.execute(sql_cartSelect, {'user_id': user_id}).mappings().fetchone()

    if cartSelect['buyCount'] != len(cartBuyList):
        return {'result': 'failed', 'message': '선택한 장바구니 정보를 확인할 수 없습니다.'}

    request.session['checkout_cart_ids'] = cartBuyList
    request.session['checkout_type'] = 'cart'

    return {'result': 'success'}

@app.post('/checkout/card')
def checkOutCard(
    request: Request,
    order_name: str = Form(),
    order_phone: str = Form(),
    order_addr: str = Form(),
    order_addr_detail: str = Form(),
    payment_method: str = Form(),
    session: Session = Depends(get_session)
):
    """[카드 결제 및 주문 최종 처리 트랜잭션]"""
    product_id = request.session.get('checkout_product_id')
    buy_quantity = request.session.get('checkout_quantity')
    checkout_type = request.session.get('checkout_type')
    reservation_id = request.session.get('checkout_reservation_id')
    user_id = request.session.get('user_id')

    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    if checkout_type in ['direct', 'reservation']:
        if product_id is None or buy_quantity is None:
            return RedirectResponse(url='/products', status_code=303)

        sql_checkout_stock = text('select * from product where product_id = :product_id')
        checkout_stock = session.execute(sql_checkout_stock, {'product_id': product_id}).mappings().fetchone()

        if checkout_stock is None or checkout_stock['product_active'] != 1 or buy_quantity < 1:
            return RedirectResponse(url=f'/product/detail/{product_id}', status_code=303)

        if checkout_type == 'direct' and checkout_stock['product_sale_stock'] < buy_quantity:
            return RedirectResponse(url=f'/product/detail/{product_id}', status_code=303)
        if checkout_type == 'reservation' and checkout_stock['product_reservation_stock'] < buy_quantity:
            return RedirectResponse(url='/mypage/reservations', status_code=303)

    elif checkout_type == 'cart':
        cartBuyList = request.session.get('checkout_cart_ids')
        if not cartBuyList:
            return RedirectResponse(url='/cart', status_code=303)

        cartList = ','.join(map(str, cartBuyList))
        sql_checkout_cart = text(f'''
            select ca.cart_id, ca.product_quantity, pr.product_id, pr.product_price,
                   pr.product_sale_stock, pr.product_active
            from cart as ca
            join product as pr on ca.product_id = pr.product_id
            where ca.user_id = :user_id and ca.cart_id in ({cartList})
        ''')
        checkout_cart_list = session.execute(sql_checkout_cart, {'user_id': user_id}).mappings().fetchall()

        if len(checkout_cart_list) != len(cartBuyList):
            return RedirectResponse(url='/cart', status_code=303)

        for cartProduct in checkout_cart_list:
            if cartProduct['product_active'] != 1 or cartProduct['product_quantity'] < 1:
                return RedirectResponse(url='/cart', status_code=303)
            if cartProduct['product_sale_stock'] < cartProduct['product_quantity']:
                return RedirectResponse(url='/cart?checkout=stock_failed', status_code=303)
    else:
        return RedirectResponse(url='/products', status_code=303)

    checkoutDate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if checkout_type == 'cart':
        checkout_total_price = sum(prod['product_price'] * prod['product_quantity'] for prod in checkout_cart_list)
    else:
        checkout_total_price = checkout_stock['product_price'] * buy_quantity

    sql_checkout_sheet = text('''
        insert into order_sheet (order_sheet_date, order_total_price)
        values (:checkoutDate, :checkout_total_price)
    ''')
    result_checkout_sheet = session.execute(sql_checkout_sheet, {
        'checkoutDate': checkoutDate,
        'checkout_total_price': checkout_total_price
    })
    checkout_sheet_id = result_checkout_sheet.lastrowid

    sql_orders = text('''
        insert into orders
        (user_id, order_status_id, order_name, order_addr, order_phone, product_id, order_quantity, order_sheet_id, order_price)
        values
        (:user_id, :order_status_id, :order_name, :order_addr, :order_phone, :product_id, :order_quantity, :order_sheet_id, :order_price)
    ''')

    if checkout_type == 'cart':
        for cartProduct in checkout_cart_list:
            session.execute(sql_orders, {
                'user_id': user_id,
                'order_status_id': 1,
                'order_name': order_name,
                'order_addr': f'{order_addr} {order_addr_detail}',
                'order_phone': order_phone,
                'product_id': cartProduct['product_id'],
                'order_quantity': cartProduct['product_quantity'],
                'order_sheet_id': checkout_sheet_id,
                'order_price': cartProduct['product_price']
            })
    else:
        session.execute(sql_orders, {
            'user_id': user_id,
            'order_status_id': 1,
            'order_name': order_name,
            'order_addr': f'{order_addr} {order_addr_detail}',
            'order_phone': order_phone,
            'product_id': product_id,
            'order_quantity': buy_quantity,
            'order_sheet_id': checkout_sheet_id,
            'order_price': checkout_stock['product_price']
        })

    sql_payment = text('''
        insert into payment (payment_method, payment_failure_reason, payment_status_id, order_sheet_id)
        values (:payment_method, null, 2, :order_sheet_id)
    ''')
    session.execute(sql_payment, {
        'payment_method': payment_method,
        'order_sheet_id': checkout_sheet_id
    })

    if checkout_type == 'direct':
        sql_stock_update = text('''
            update product
            set product_sale_stock = product_sale_stock - :order_quantity
            where product_id = :product_id
            and product_sale_stock >= :order_quantity
            and product_active = 1
        ''')
        res_stock = session.execute(sql_stock_update, {'order_quantity': buy_quantity, 'product_id': product_id})
        if res_stock.rowcount == 0:
            session.rollback()
            return RedirectResponse(url=f'/product/detail/{product_id}', status_code=303)

    elif checkout_type == 'reservation':
        sql_stock_update = text('''
            update product
            set product_reservation_stock = product_reservation_stock - :order_quantity
            where product_id = :product_id
            and product_reservation_stock >= :order_quantity
            and product_active = 1
        ''')
        res_stock = session.execute(sql_stock_update, {'order_quantity': buy_quantity, 'product_id': product_id})
        if res_stock.rowcount == 0:
            session.rollback()
            return RedirectResponse(url='/mypage/reservations', status_code=303)

    elif checkout_type == 'cart':
        sql_stock_update = text('''
            update product
            set product_sale_stock = product_sale_stock - :order_quantity
            where product_id = :product_id
            and product_sale_stock >= :order_quantity
            and product_active = 1
        ''')
        for cartProduct in checkout_cart_list:
            res_stock = session.execute(sql_stock_update, {
                'order_quantity': cartProduct['product_quantity'],
                'product_id': cartProduct['product_id']
            })
            if res_stock.rowcount == 0:
                session.rollback()
                return RedirectResponse(url='/cart', status_code=303)

    sql_delivery = text('''
        insert into delivery (delivery_receiver, delivery_addr, delivery_phone, delivery_status_id, order_sheet_id)
        values (:delivery_receiver, :delivery_addr, :delivery_phone, 1, :order_sheet_id)
    ''')
    session.execute(sql_delivery, {
        'delivery_receiver': order_name,
        'delivery_addr': f'{order_addr} {order_addr_detail}',
        'delivery_phone': order_phone,
        'order_sheet_id': checkout_sheet_id
    })

    if checkout_type == 'reservation':
        if reservation_id is None:
            session.rollback()
            return RedirectResponse(url='/mypage/reservations', status_code=303)

        sql_reservation_delete = text('''
            delete from reservation
            where reservation_id = :reservation_id
            and user_id = :user_id and product_id = :product_id
            and reservation_status_id = 2
        ''')
        res_res_del = session.execute(sql_reservation_delete, {
            'reservation_id': reservation_id,
            'user_id': user_id,
            'product_id': product_id
        })
        if res_res_del.rowcount == 0:
            session.rollback()
            return RedirectResponse(url='/mypage/reservations', status_code=303)

    if checkout_type == 'cart':
        sql_cart_delete = text(f'''
            delete from cart
            where user_id = :user_id and cart_id in ({cartList})
        ''')
        res_cart_del = session.execute(sql_cart_delete, {'user_id': user_id})
        if res_cart_del.rowcount != len(cartBuyList):
            session.rollback()
            return RedirectResponse(url='/cart', status_code=303)

    session.commit()

    for key in ['checkout_product_id', 'checkout_quantity', 'checkout_type', 'checkout_reservation_id', 'checkout_cart_ids']:
        request.session.pop(key, None)

    return RedirectResponse(url=f'/payment/result?order_sheet_id={checkout_sheet_id}', status_code=303)


####################################
#          상품 결제 결과 구역       
####################################

@app.get('/payment/result')
def paymentResult(request: Request, order_sheet_id: int, session: Session = Depends(get_session)):
    """[결제 완료 영수증 화면]"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    sql_order = text('''
        select os.order_sheet_id, os.order_sheet_date, os.order_total_price, od.order_name
        from order_sheet as os
        join orders as od on os.order_sheet_id = od.order_sheet_id
        where os.order_sheet_id = :order_sheet_id and od.user_id = :user_id
        limit 1
    ''')
    result_order = session.execute(sql_order, {'order_sheet_id': order_sheet_id, 'user_id': user_id})
    payment_result = result_order.mappings().fetchone()

    if payment_result is None:
        return RedirectResponse(url='/', status_code=303)

    return templates.TemplateResponse(request, 'payment-result.html', {'payment_result': payment_result})


####################################
#          커뮤니티 / 공지사항       
####################################

@app.get('/notice')
def commNotice(request: Request, keyword: str = '', page: int = 1, session: Session = Depends(get_session)):
    """[공지사항 목록]"""
    keyword = keyword.strip()
    if page < 1:
        page = 1

    page_size = 10
    page_start = (page - 1) * page_size

    sql_notice = text('''
        select notice_id, notice_title, notice_detail, notice_date, user_id
        from notice
        where (:keyword = '' or notice_title like :search_keyword or notice_detail like :search_keyword)
        order by notice_id desc
        limit :page_start, :page_size
    ''')
    result_notice = session.execute(sql_notice, {
        'keyword': keyword,
        'search_keyword': '%' + keyword + '%',
        'page_start': page_start,
        'page_size': page_size
    })
    notice_list = result_notice.mappings().fetchall()

    sql_notice_count = text('''
        select count(*) as notice_count
        from notice
        where (:keyword = '' or notice_title like :search_keyword or notice_detail like :search_keyword)
    ''')
    notice_count = session.execute(sql_notice_count, {
        'keyword': keyword,
        'search_keyword': '%' + keyword + '%'
    }).mappings().fetchone()['notice_count']

    total_page = int(notice_count / page_size) + (1 if notice_count % page_size != 0 else 0)

    return templates.TemplateResponse(request, 'notice.html', {
        'notice_list': notice_list,
        'keyword': keyword,
        'page': page,
        'total_page': total_page
    })

@app.get('/notice/write')
def noticeWrite(request: Request):
    """[공지사항 작성 화면]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    return templates.TemplateResponse(request, 'notice-editor.html', {'editor_mode': 'write', 'notice': None})

@app.post('/notice/write')
def noticeWriteData(
    request: Request,
    notice_title: str = Form(),
    notice_detail: str = Form(),
    session: Session = Depends(get_session)
):
    """[공지사항 등록]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    notice_title = notice_title.strip()
    notice_detail = notice_detail.strip()

    if not notice_title or not notice_detail:
        return RedirectResponse(url='/notice/write', status_code=303)

    sql_notice_write = text('''
        insert into notice (notice_title, notice_detail, notice_date, user_id)
        values (:notice_title, :notice_detail, :notice_date, :user_id)
    ''')
    session.execute(sql_notice_write, {
        'notice_title': notice_title,
        'notice_detail': notice_detail,
        'notice_date': datetime.now().strftime('%Y-%m-%d'),
        'user_id': request.session.get('user_id')
    })
    session.commit()

    return RedirectResponse(url='/notice', status_code=303)

@app.get('/notice/edit/{notice_id}')
def noticeEdit(request: Request, notice_id: int, session: Session = Depends(get_session)):
    """[공지사항 수정 화면]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    sql_notice = text('select * from notice where notice_id = :notice_id')
    notice = session.execute(sql_notice, {'notice_id': notice_id}).mappings().fetchone()

    if notice is None:
        return RedirectResponse(url='/notice', status_code=303)

    return templates.TemplateResponse(request, 'notice-editor.html', {'editor_mode': 'edit', 'notice': notice})

@app.post('/notice/edit/{notice_id}')
def noticeEditData(
    request: Request,
    notice_id: int,
    notice_title: str = Form(),
    notice_detail: str = Form(),
    session: Session = Depends(get_session)
):
    """[공지사항 수정 저장]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    notice_title = notice_title.strip()
    notice_detail = notice_detail.strip()

    if not notice_title or not notice_detail:
        return RedirectResponse(url=f'/notice/edit/{notice_id}', status_code=303)

    sql_notice_update = text('''
        update notice
        set notice_title = :notice_title, notice_detail = :notice_detail
        where notice_id = :notice_id
    ''')
    session.execute(sql_notice_update, {
        'notice_title': notice_title,
        'notice_detail': notice_detail,
        'notice_id': notice_id
    })
    session.commit()

    return RedirectResponse(url='/notice', status_code=303)

@app.post('/notice/delete')
def noticeDelete(request: Request, notice_id: int = Form(), session: Session = Depends(get_session)):
    """[공지사항 삭제]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    sql_notice_delete = text('delete from notice where notice_id = :notice_id')
    session.execute(sql_notice_delete, {'notice_id': notice_id})
    session.commit()

    return RedirectResponse(url='/notice', status_code=303)


####################################
#          커뮤니티 / FAQ           
####################################

@app.get('/faq')
def commFaq(request: Request, keyword: str = '', page: int = 1, session: Session = Depends(get_session)):
    """[FAQ 목록]"""
    keyword = keyword.strip()
    if page < 1:
        page = 1

    page_size = 10
    page_start = (page - 1) * page_size

    sql_faq = text('''
        select faq_id, faq_title, faq_detail, faq_date, user_id
        from faq
        where (:keyword = '' or faq_title like :search_keyword or faq_detail like :search_keyword)
        order by faq_id desc
        limit :page_start, :page_size
    ''')
    faq_list = session.execute(sql_faq, {
        'keyword': keyword,
        'search_keyword': '%' + keyword + '%',
        'page_start': page_start,
        'page_size': page_size
    }).mappings().fetchall()

    sql_faq_count = text('''
        select count(*) as faq_count
        from faq
        where (:keyword = '' or faq_title like :search_keyword or faq_detail like :search_keyword)
    ''')
    faq_count = session.execute(sql_faq_count, {
        'keyword': keyword,
        'search_keyword': '%' + keyword + '%'
    }).mappings().fetchone()['faq_count']

    total_page = int(faq_count / page_size) + (1 if faq_count % page_size != 0 else 0)

    return templates.TemplateResponse(request, 'faq.html', {
        'faq_list': faq_list,
        'keyword': keyword,
        'page': page,
        'total_page': total_page
    })

@app.get('/faq/write')
def faqWrite(request: Request):
    """[FAQ 작성 화면]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)
    return templates.TemplateResponse(request, 'faq-editor.html', {'editor_mode': 'write', 'faq': None})

@app.post('/faq/write')
def faqWriteData(
    request: Request,
    faq_title: str = Form(),
    faq_detail: str = Form(),
    session: Session = Depends(get_session)
):
    """[FAQ 등록]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    faq_title = faq_title.strip()
    faq_detail = faq_detail.strip()
    if not faq_title or not faq_detail:
        return RedirectResponse(url='/faq/write', status_code=303)

    sql_faq_write = text('''
        insert into faq (faq_title, faq_detail, faq_date, user_id)
        values (:faq_title, :faq_detail, :faq_date, :user_id)
    ''')
    session.execute(sql_faq_write, {
        'faq_title': faq_title,
        'faq_detail': faq_detail,
        'faq_date': datetime.now().strftime('%Y-%m-%d'),
        'user_id': request.session.get('user_id')
    })
    session.commit()

    return RedirectResponse(url='/faq', status_code=303)

@app.get('/faq/edit/{faq_id}')
def faqEdit(request: Request, faq_id: int, session: Session = Depends(get_session)):
    """[FAQ 수정 화면]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    sql_faq = text('select * from faq where faq_id = :faq_id')
    faq = session.execute(sql_faq, {'faq_id': faq_id}).mappings().fetchone()
    if faq is None:
        return RedirectResponse(url='/faq', status_code=303)

    return templates.TemplateResponse(request, 'faq-editor.html', {'editor_mode': 'edit', 'faq': faq})

@app.post('/faq/edit/{faq_id}')
def faqEditData(
    request: Request,
    faq_id: int,
    faq_title: str = Form(),
    faq_detail: str = Form(),
    session: Session = Depends(get_session)
):
    """[FAQ 수정 저장]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    faq_title = faq_title.strip()
    faq_detail = faq_detail.strip()
    if not faq_title or not faq_detail:
        return RedirectResponse(url=f'/faq/edit/{faq_id}', status_code=303)

    sql_faq_update = text('''
        update faq
        set faq_title = :faq_title, faq_detail = :faq_detail
        where faq_id = :faq_id
    ''')
    session.execute(sql_faq_update, {
        'faq_title': faq_title,
        'faq_detail': faq_detail,
        'faq_id': faq_id
    })
    session.commit()

    return RedirectResponse(url='/faq', status_code=303)

@app.post('/faq/delete')
def faqDelete(request: Request, faq_id: int = Form(), session: Session = Depends(get_session)):
    """[FAQ 삭제]"""
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(url='/error-404', status_code=303)

    sql_faq_delete = text('delete from faq where faq_id = :faq_id')
    session.execute(sql_faq_delete, {'faq_id': faq_id})
    session.commit()

    return RedirectResponse(url='/faq', status_code=303)


####################################
#          1:1 문의 접수             
####################################

@app.get('/inquiry/write')
def commInquiryWrite(request: Request):
    """1:1 문의 작성 폼"""
    if request.session.get('user_id') is None:
        return RedirectResponse(url='/login', status_code=303)
    return templates.TemplateResponse(request, 'inquiry-write.html')

@app.post('/inquiry/write')
def commInquiryWriteData(
    request: Request,
    inquiry_type: str = Form(),
    inquiry_title: str = Form(),
    inquiry_detail: str = Form(),
    session: Session = Depends(get_session)
):
    """[1:1 문의 등록]"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    inquiry_type = inquiry_type.strip()
    inquiry_title = inquiry_title.strip()
    inquiry_detail = inquiry_detail.strip()

    valid_types = ['상품문의', '배송문의', '예약문의', '기타문의']
    if inquiry_type not in valid_types or not inquiry_title or not inquiry_detail or \
       len(inquiry_title) > 200 or len(inquiry_detail) > 3000:
        return RedirectResponse(url='/inquiry/write', status_code=303)

    sql_inquiry_write = text('''
        insert into inquiry (
            inquiry_title, inquiry_detail, inquiry_attachment, inquiry_date,
            inquiry_answer, inquiry_answer_date, user_id, inquiry_status_id, inquiry_type
        )
        values (
            :inquiry_title, :inquiry_detail, null, :inquiry_date,
            null, null, :user_id, 1, :inquiry_type
        )
    ''')
    session.execute(sql_inquiry_write, {
        'inquiry_title': inquiry_title,
        'inquiry_detail': inquiry_detail,
        'inquiry_date': datetime.now().strftime('%Y-%m-%d'),
        'user_id': user_id,
        'inquiry_type': inquiry_type
    })
    session.commit()

    return RedirectResponse(url='/mypage/inquiries?write_result=success', status_code=303)


####################################
#          마이페이지 관련 구역       
####################################

@app.get('/mypage')
def mypage(request: Request, session: Session = Depends(get_session)):
    """[마이페이지 대시보드] (로그인 세션 기반 user_id 연동 오류 수정 완료)"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    sql1 = text("select user_addr, user_phone from users where user_id = :user_id")
    result = session.execute(sql1, {'user_id': user_id}).mappings().fetchall()

    sql2 = text('''
        select count(*) as payment_completed
        from orders as o 
        left join payment as p on o.order_sheet_id = p.order_sheet_id
        left join payment_status as ps on p.payment_status_id = ps.payment_status_id
        where o.user_id = :user_id and ps.payment_status_name = '결제완료'
    ''')
    result2 = session.execute(sql2, {'user_id': user_id}).mappings().fetchall()

    sql3 = text('''
        select count(*) as delivery_completed
        from orders as o 
        left join delivery as d on o.order_sheet_id = d.order_sheet_id
        left join delivery_status as ds on d.delivery_status_id = ds.delivery_status_id 
        where o.user_id = :user_id and delivery_status_name = '배송완료'        
    ''')
    result3 = session.execute(sql3, {'user_id': user_id}).mappings().fetchall()

    sql4 = text('''
        select 
            u.user_id, p.product_name, p.product_image, r.reservation_id, rs.reservation_status_name,
            (
                select count(*) from reservation 
                where product_id = p.product_id
                and reservation_status_id = 3
                and reservation_id <= r.reservation_id
            ) as reservation_turn,
            r.reservation_expiration
        from reservation as r 
        left join users as u on r.user_id = u.user_id 
        left join product as p on r.product_id = p.product_id
        left join reservation_status as rs on r.reservation_status_id = rs.reservation_status_id
        where r.user_id = :user_id
    ''')
    result4 = session.execute(sql4, {'user_id': user_id}).mappings().fetchall()

    sql5 = text('''
        select count(*) as reservation_completed
        from reservation as r 
        left join reservation_status as rs on r.reservation_status_id = rs.reservation_status_id
        where r.user_id = :user_id
    ''')
    result5 = session.execute(sql5, {'user_id': user_id}).mappings().fetchall()

    sql6 = text('''
        select os.order_sheet_date, p.product_name, os.order_total_price, ds.delivery_status_name
        from orders as o 
        left join order_sheet as os on o.order_sheet_id = os.order_sheet_id
        left join delivery as d on o.order_sheet_id = d.order_sheet_id
        left join delivery_status as ds on d.delivery_status_id = ds.delivery_status_id
        left join product as p on o.product_id = p.product_id
        where o.user_id = :user_id
    ''')
    result6 = session.execute(sql6, {'user_id': user_id}).mappings().fetchall()

    sql7 = text('''
        select inq.inquiry_type, inq.inquiry_title, inqstat.inquiry_status_name, inq.inquiry_answer_date
        from inquiry as inq 
        left join inquiry_status as inqstat on inq.inquiry_status_id = inqstat.inquiry_status_id
        where inq.user_id = :user_id
    ''')
    result7 = session.execute(sql7, {'user_id': user_id}).mappings().fetchall()

    sql8 = text('''
        select count(*) as inquiry_repiled_count 
        from inquiry as inq 
        left join inquiry_status as inqstat on inq.inquiry_status_id = inqstat.inquiry_status_id
        where inq.user_id = :user_id
    ''')
    result8 = session.execute(sql8, {'user_id': user_id}).mappings().fetchall()

    return templates.TemplateResponse(request, 'mypage-dashboard.html', {
        'contact_details': result,
        'payment_completed_count': result2[0]['payment_completed'],
        'delivery_completed_count': result3[0]['delivery_completed'],
        'reservation_purchase_status': result4,
        'reservation_completed_count': result5[0]['reservation_completed'],
        'recent_order_history': result6,
        'recent_inquiry_history': result7,
        'inquiry_repiled_count': result8[0]['inquiry_repiled_count']
    })

@app.get('/mypage/inquiries')
def mypageInquiries(request: Request, page: int = 1, session: Session = Depends(get_session)):
    """[마이페이지] 내 1:1 문의 목록"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    if page < 1:
        page = 1
    page_size = 10
    page_start = (page - 1) * page_size

    sql_inquiry = text('''
        select
            iq.inquiry_id, iq.inquiry_type, iq.inquiry_title, iq.inquiry_detail,
            iq.inquiry_attachment, iq.inquiry_date, iq.inquiry_answer,
            iq.inquiry_answer_date, iq.inquiry_status_id, ist.inquiry_status_name
        from inquiry as iq
        join inquiry_status as ist on iq.inquiry_status_id = ist.inquiry_status_id
        where iq.user_id = :user_id
        order by iq.inquiry_id desc
        limit :page_start, :page_size
    ''')
    inquiry_list = session.execute(sql_inquiry, {
        'user_id': user_id,
        'page_start': page_start,
        'page_size': page_size
    }).mappings().fetchall()

    sql_inquiry_count = text('select count(*) as inquiry_count from inquiry where user_id = :user_id')
    inquiry_count = session.execute(sql_inquiry_count, {'user_id': user_id}).mappings().fetchone()['inquiry_count']

    total_page = int(inquiry_count / page_size) + (1 if inquiry_count % page_size != 0 else 0)

    return templates.TemplateResponse(request, 'mypage-inquiries.html', {
        'inquiry_list': inquiry_list,
        'page': page,
        'total_page': total_page
    })

@app.post('/mypage/inquiry/delete')
def mypageInquiryDelete(request: Request, inquiry_id: int = Form(), session: Session = Depends(get_session)):
    """[마이페이지] 내 문의 삭제"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    sql_inquiry_delete = text('delete from inquiry where inquiry_id = :inquiry_id and user_id = :user_id')
    session.execute(sql_inquiry_delete, {'inquiry_id': inquiry_id, 'user_id': user_id})
    session.commit()

    return RedirectResponse(url='/mypage/inquiries?delete_result=success', status_code=303)

@app.get('/mypage/orders')
def mypage_orders(request: Request, session: Session = Depends(get_session)):
    """[마이페이지] 내 주문/배송 조회"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    sql = text('''
        select count(*) as payment_completed
        from orders as o 
        left join payment as p on o.order_sheet_id = p.order_sheet_id
        left join payment_status as ps on p.payment_status_id = ps.payment_status_id
        where o.user_id = :user_id and ps.payment_status_name = '결제완료'
    ''')
    result = session.execute(sql, {'user_id': user_id}).mappings().fetchall()

    sql2 = text('''
        select count(*) as delivery_completed
        from orders as o 
        left join delivery as d on o.order_sheet_id = d.order_sheet_id
        left join delivery_status as ds on d.delivery_status_id = ds.delivery_status_id 
        where o.user_id = :user_id and delivery_status_name = '배송완료'        
    ''')
    result2 = session.execute(sql2, {'user_id': user_id}).mappings().fetchall()

    sql3 = text('''
        select u.user_id, ds.delivery_status_name, p.product_name, p.product_image, os.order_sheet_id, p.product_price
        from orders as o 
        left join users as u on o.user_id = u.user_id
        left join order_sheet as os on o.order_sheet_id = os.order_sheet_id
        left join delivery as d on os.order_sheet_id = d.order_sheet_id
        left join delivery_status as ds on d.delivery_status_id = ds.delivery_status_id
        left join product as p on o.product_id = p.product_id
        where o.user_id = :user_id
    ''')
    result3 = session.execute(sql3, {'user_id': user_id}).mappings().fetchall()

    sql4 = text('''
        select count(*) as refund_count
        from orders as o 
        left join payment as p on o.order_sheet_id = p.order_sheet_id
        left join payment_status as ps on p.payment_status_id = ps.payment_status_id
        where o.user_id = :user_id and payment_status_name = '결제취소'
    ''')
    result4 = session.execute(sql4, {'user_id': user_id}).mappings().fetchall()

    return templates.TemplateResponse(request, 'mypage-orders.html', {
        'payment_completed': result[0]['payment_completed'],
        'delivery_completed': result2[0]['delivery_completed'],
        'order_list': result3,
        'refund_count': result4[0]['refund_count']
    })

@app.get('/mypage/profile')
def mypageProfile(request: Request, session: Session = Depends(get_session)):
    """[마이페이지] 개인정보 확인"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    sql_profile = text('''
        select user_id, user_name, user_email, user_phone, user_addr, user_addr_detail
        from users
        where user_id = :user_id
    ''')
    user_profile = session.execute(sql_profile, {'user_id': user_id}).mappings().fetchone()
    if user_profile is None:
        request.session.clear()
        return RedirectResponse(url='/login', status_code=303)

    return templates.TemplateResponse(request, 'mypage-profile.html', {'user_profile': user_profile})

@app.post('/mypage/profile')
def mypageProfileUpdate(
    request: Request,
    user_name: str = Form(),
    user_addr: str = Form(),
    user_addr_detail: str = Form(),
    user_email: str = Form(),
    user_phone: str = Form(),
    session: Session = Depends(get_session)
):
    """[마이페이지] 개인정보 수정"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    user_name = user_name.strip()
    user_addr = user_addr.strip()
    user_addr_detail = user_addr_detail.strip()
    user_email = user_email.strip()
    user_phone = user_phone.strip().replace('-', '')

    if not all([user_name, user_addr, user_addr_detail, user_email]) or \
       not user_phone.isdigit() or len(user_phone) != 11 or not user_phone.startswith('010'):
        return RedirectResponse(url='/mypage/profile', status_code=303)

    sql_profile_update = text('''
        update users
        set user_name = :user_name, user_addr = :user_addr,
            user_addr_detail = :user_addr_detail, user_email = :user_email, user_phone = :user_phone
        where user_id = :user_id
    ''')
    session.execute(sql_profile_update, {
        'user_name': user_name,
        'user_addr': user_addr,
        'user_addr_detail': user_addr_detail,
        'user_email': user_email,
        'user_phone': user_phone,
        'user_id': user_id
    })
    session.commit()

    request.session['user_name'] = user_name

    return RedirectResponse(url='/mypage/profile', status_code=303)

@app.post('/mypage/profile/password')
def mypagePasswordUpdate(
    request: Request,
    current_password: str = Form(),
    new_password: str = Form(),
    new_password_confirm: str = Form(),
    session: Session = Depends(get_session)
):
    """[마이페이지] 비밀번호 변경"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    if not current_password or not new_password or new_password != new_password_confirm:
        return RedirectResponse(url='/mypage/profile', status_code=303)

    sql_password_check = text('select user_password from users where user_id = :user_id')
    password_data = session.execute(sql_password_check, {'user_id': user_id}).mappings().fetchone()
    saved_password = password_data['user_password']

    if saved_password.startswith('$argon2'):
        current_password_check = passwordVerify(current_password, saved_password)
    else:
        current_password_check = (current_password == saved_password)

    if not current_password_check:
        return RedirectResponse(url='/mypage/profile?password_result=wrong', status_code=303)

    sql_password_update = text('update users set user_password = :new_password where user_id = :user_id')
    session.execute(sql_password_update, {
        'new_password': passwordHash(new_password),
        'user_id': user_id
    })
    session.commit()

    return RedirectResponse(url='/mypage/profile?password_result=success', status_code=303)

@app.get('/mypage/reservations')
def mypageReservations(request: Request, session: Session = Depends(get_session)):
    """[마이페이지] 내 예약 현황"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    sql_mypage_reservation = text('''
        select * 
        from reservation as res
        join product as pr on res.product_id = pr.product_id
        join users as us on res.user_id = us.user_id
        join reservation_status as stat on res.reservation_status_id = stat.reservation_status_id
        where res.user_id = :user_id
        order by res.product_id, res.reservation_date, res.reservation_id;        
    ''')
    reservationList = session.execute(sql_mypage_reservation, {'user_id': user_id}).mappings().fetchall()

    return templates.TemplateResponse(request, 'mypage-reservations.html', {
        'reservationList': reservationList
    })

@app.post('/mypage/reservation/cancel')
def mypageReservationCancle(
    request: Request,
    reservation_id: int = Form(), 
    session: Session = Depends(get_session)
):
    """[마이페이지] 예약 취소"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return RedirectResponse(url='/login', status_code=303)

    sql_reservation_delete = text('delete from reservation where user_id = :user_id and reservation_id = :reservation_id')
    session.execute(sql_reservation_delete, {'user_id': user_id, 'reservation_id': reservation_id})
    session.commit()

    return RedirectResponse(url='/mypage/reservations', status_code=303)

@app.post('/mypage/reservation/turn')
def mypageReservationTurn(
    request: Request,
    reservation_id: int,
    session: Session = Depends(get_session)
):
    """[마이페이지] 실시간 예약 대기 순번 조회"""
    user_id = request.session.get('user_id')
    if user_id is None:
        return {'result': '로그인이 필요합니다.'}

    sql_reservation = text('''
        select reservation_id, product_id
        from reservation
        where reservation_id = :reservation_id and user_id = :user_id
    ''')
    reservation = session.execute(sql_reservation, {
        'reservation_id': reservation_id,
        'user_id': user_id
    }).mappings().fetchone()

    if reservation is None:
        return {'result': '예약정보를 찾을 수 없습니다.'}

    sql_reservation_turn = text('''
        select count(*) as reservation_turn from reservation 
        where product_id = :product_id 
        and reservation_status_id = 3
        and reservation_id <= :reservation_id
    ''')
    reservation_turn = session.execute(sql_reservation_turn, {
        'product_id': reservation['product_id'],
        'reservation_id': reservation['reservation_id']
    }).mappings().fetchone()

    return {
        'result': '성공',
        'reservation_count': reservation_turn['reservation_turn']
    }


####################################
#          서버 실행 엔트리포인트   
####################################
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('api:app', port=8000, reload=True, host="0.0.0.0")


# ==============================================================================
# 사용 없는 레거시/테스트 코드 정리본 (참조 및 아카이빙용)
# ==============================================================================
"""
# [미사용 라우트 1] 상품 정렬 API
# @app.get('/products/align')
# def productsAlign(value: str, category_id:int = 0, keyword:str = '', session: Session = Depends(get_session)):
#     if value == 'align_view' :
#         sql = text('''
#             select * from product
#             where (:category_id = 0 or category_id = :category_id)
#             and (:keyword = '' or product_name like :search_keyword)
#             order by product_view_count desc
#         ''')
#     elif value == 'align_price_low' :
#         sql = text('''
#             select * from product
#             where (:category_id = 0 or category_id = :category_id)
#             and (:keyword = '' or product_name like :search_keyword)
#             order by product_price
#         ''')
#     elif value == 'align_price_high' :
#         sql = text('''
#             select * from product
#             where (:category_id = 0 or category_id = :category_id)
#             and (:keyword = '' or product_name like :search_keyword)
#             order by product_price desc
#         ''')
#     elif value == 'align_name' :
#         sql = text('''
#             select * from product
#             where (:category_id = 0 or category_id = :category_id)
#             and (:keyword = '' or product_name like :search_keyword)
#             order by product_name
#         ''')
#     else:
#         sql = text('''
#             select * from product
#             where (:category_id = 0 or category_id = :category_id)
#             and (:keyword = '' or product_name like :search_keyword)
#             order by product_view_count desc
#         ''')
#     result = session.execute(sql, {
#         'category_id' : category_id,
#         'keyword': keyword,
#         'search_keyword': '%' + keyword + '%'
#     }) 
#     product_list = result.mappings().fetchall()
#     return {'product_list' : product_list}

# [미사용 라우트 2] 단순 상품 페이징 라우트
# @app.get('/products/page/{page}')
# def productsPage(request: Request, page: int, session: Session = Depends(get_session)):
#     sql = text('select * from product limit :page_view, 8')
#     result = session.execute(sql, {'page_view' : (page * 8) - 8})
#     product_page_list = result.mappings().fetchall()
#     sql_all = text('select * from product')
#     result_all = session.execute(sql_all)
#     product_list = result_all.mappings().fetchall()
#     product_count = len(product_list)
#     total_page = int(product_count / 8) + (1 if product_count % 8 != 0 else 0)
#     return templates.TemplateResponse(request, 'products.html', {
#         'product_list' : product_page_list,
#         'product_count' : product_count,
#         'total_page' : total_page,
#         'page' : page,
#         'category_id' : 0,
#         'keyword' : ''
#     })

# [미사용 라우트 3] 카테고리별 단독 조회
# @app.get('/product/category/{category_id}')
# def productsCategory(request: Request, category_id:int, session: Session = Depends(get_session)):
#     sql = text('select * from product where category_id = :category_id order by product_view_count desc')
#     result = session.execute(sql, {'category_id' : category_id})
#     product_category_list = result.mappings().fetchall()
#     return templates.TemplateResponse(request, 'products.html', {
#         'product_list' : product_category_list,
#         'product_count' : len(product_category_list),
#         'category_id' : category_id
#     })

# [미사용 라우트 4] 상품명 단순 검색 라우트
# @app.get('/product/search')
# def productSearch(request: Request, keyword: str, session: Session = Depends(get_session)):
#     sql_search = text('select * from product where product_name like :keyword order by product_view_count desc')
#     result = session.execute(sql_search, {'keyword' : '%' + keyword + '%'}) 
#     product_search_list = result.mappings().fetchall()
#     return templates.TemplateResponse(request, 'products.html', {
#         'product_list' : product_search_list,
#         'product_count' : len(product_search_list),
#         'category_id' : 0,
#         'keyword' : keyword
#     })

# [테스트 흔적 1] 사용자 이름 및 아이디 마스킹(*) 처리 로직 테스트
# aster = ''
# for i in range(len(request.session.get('user_name')[1:])) :
#     aster += '*' 
#     user_name = request.session.get('user_name')[0]
#     aster_name = user_name + aster
# for i in range(len(request.session.get('user_id')[3:])-1) :
#     aster += '*'
#     user_id = request.session.get('user_id')[:2]
#     aster_id = user_id + aster

# [테스트 흔적 2] 예약 재고 차감 및 24시간 만료일 테스트
# nowAfter = now + timedelta(days=1)
# reservationExpiration = nowAfter.strftime('%Y-%m-%d %H:%M:%S')

# [테스트 흔적 3] 장바구니 다중 선택 삭제 문자열 튜플 변환 시도 흔적
# test = "''".join(deleteSelectList)
# test2 = str(tuple(deleteSelectList))
"""