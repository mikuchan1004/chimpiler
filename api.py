from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy import text, URL

from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from starlette.middleware.sessions import SessionMiddleware

from datetime import datetime, timedelta

import random

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key='chimpiler-session-key'
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='.')

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
    with Session(engine) as session :
        yield session

####################################
#          공통 설정 및 함수        
####################################
def price(value) :
    # Jinja에서 20000원 → 20,000원 으로 변경하기 위한 필터
    # print(random.randint(1,10))
    return f'{int(value):,}'
templates.env.filters['price'] = price

####################################
#          레이아웃 관련 구역        
####################################
@app.get('/chat')
def chatBot(answer:str, session: Session = Depends(get_session)) :
    print('''
    ========================================
    /chat : 챗봇 실행
    ========================================
    ''')
    # DB에 넣어둔 ai_chatbot 테이블의 chat_keyword 중 제미나이 keyword를 받아 진행
    sql = text('''
        select chat_answer
        from ai_chatbot
        where chat_keyword = :answer
    ''')

    result = session.execute(sql, {
        'answer' : answer
    })

    chat_result = result.mappings().fetchone()
    print('chat_result', chat_result)

    return {
        'chat_result' : chat_result
    }

####################################
#          로그인 관련 구역        
####################################
@app.get('/login')
def login_loading(request: Request):
    print('''
    ========================================
    /login : 로그인 페이지 로딩
    ========================================
    ''')
    return templates.TemplateResponse(request, 'login.html')

@app.post('/login')
def login(request: Request, user_id:str = Form(), user_password:str = Form(), session: Session = Depends(get_session)) :
    print('''
    ========================================
    /login : 로그인 페이지 실행
    ========================================
    ''')

    sql = text('''
        select * from users
        where user_id = :user_id
    ''')

    result = session.execute(sql, {
        'user_id' : user_id
    })
    login_check = result.mappings().fetchone()

    print(login_check)

    if login_check :
        if user_password == login_check['user_password'] :
            # print('ID PW 같아요!!!')

            request.session['isLogin'] = True
            request.session['user_id'] = user_id
            request.session['user_name'] = login_check['user_name']

            print('/login : 로그인 성공')
            return RedirectResponse(
                url='/',
                status_code=303
            )

    print('/login : 로그인 실패')
    return templates.TemplateResponse(request, 'login.html', {
        'login_error': '아이디 또는 비밀번호가 일치하지 않습니다.'
    })

@app.get('/logout')
def logout(request:Request):
    print('''
    ========================================
    /logout : 로그아웃 페이지 실행
    ========================================
    ''')
    request.session.clear()

    return RedirectResponse(
        url='/',
        status_code=303
    )

@app.get('/signup')
def signup(request: Request):
    print('''
    ========================================
    /signup : 회원가입 페이지 실행
    ========================================
    ''')

    return templates.TemplateResponse(
        request,
        'signup.html'
    )

@app.post('/signup/idcheck')
async def signupIDChk(
    request: Request,
    session: Session = Depends(get_session)
):
    data = await request.json()

    request.session.pop(
        'signup_checked_id',
        None
    )

    signupUserId = data.get(
        'signupUserId',
        ''
    ).strip()

    if (
        signupUserId == ''
        or len(signupUserId) > 12
        or not signupUserId.isalnum()
    ):
        return {
            'result': '아이디 형식을 확인해 주세요.',
            'check': 'failed'
        }

    sql_idcheck = text('''
        select user_id
        from users
        where user_id = :user_id
    ''')

    result_idcheck = session.execute(
        sql_idcheck,
        {
            'user_id': signupUserId
        }
    )

    idcheck = (
        result_idcheck
        .mappings()
        .fetchone()
    )

    if idcheck is None:
        request.session[
            'signup_checked_id'
        ] = signupUserId

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
    print('''
    ========================================
    /signup : 회원가입 실행
    ========================================
    ''')

    user_id = user_id.strip()
    user_name = user_name.strip()
    user_addr = user_addr.strip()
    user_addr_detail = user_addr_detail.strip()
    user_email = user_email.strip()
    user_phone = user_phone.strip()

    # 휴대폰 번호에서 하이픈 제거
    user_phone = user_phone.replace('-', '')

    # 010으로 시작하는 숫자 11자리 검사
    if (
        not user_phone.isdigit()
        or len(user_phone) != 11
        or not user_phone.startswith('010')
    ):
        return RedirectResponse(
            url='/signup',
            status_code=303
        )

    # 필수 입력값 검사
    if (
        user_id == ''
        or user_password == ''
        or user_name == ''
        or user_addr == ''
        or user_addr_detail == ''
        or user_email == ''
        or user_phone == ''
    ):
        return RedirectResponse(
            url='/signup',
            status_code=303
        )

    # 비밀번호 확인
    if user_password != user_password_confirm:
        return RedirectResponse(
            url='/signup',
            status_code=303
        )

    # 중복확인을 받은 아이디와 제출한 아이디 비교
    checked_user_id = request.session.get(
        'signup_checked_id'
    )

    if checked_user_id != user_id:
        return RedirectResponse(
            url='/signup',
            status_code=303
        )

    # 회원가입 직전 아이디 중복 재검사
    sql_idcheck = text('''
        select user_id
        from users
        where user_id = :user_id
    ''')

    result_idcheck = session.execute(sql_idcheck, {
        'user_id': user_id
    })

    idcheck = result_idcheck.mappings().fetchone()

    if idcheck is not None:
        request.session.pop('signup_checked_id', None)

        return RedirectResponse(
            url='/signup',
            status_code=303
        )

    sql_signup = text('''
        insert into users (
            user_id,
            user_password,
            user_name,
            user_email,
            user_phone,
            user_addr,
            user_addr_detail
        )
        values (
            :user_id,
            :user_password,
            :user_name,
            :user_email,
            :user_phone,
            :user_addr,
            :user_addr_detail
        )
    ''')

    session.execute(sql_signup, {
        'user_id': user_id,
        'user_password': user_password,
        'user_name': user_name,
        'user_email': user_email,
        'user_phone': user_phone,
        'user_addr': user_addr,
        'user_addr_detail': user_addr_detail
    })

    session.commit()

    # 회원가입 완료 후 중복확인 기록 제거
    request.session.pop('signup_checked_id', None)

    return RedirectResponse(
        url='/login',
        status_code=303
    )

@app.get('/terms')
def terms(request: Request) :
    return templates.TemplateResponse(request, 'terms.html')

####################################
#          메인 페이지 관련 구역       
####################################
@app.get('/')
def mainPage(request: Request, session: Session = Depends(get_session)) :
    print('''
    ========================================
    / : 메인 페이지 실행
    ========================================
    ''')

    # print(request.session.get('isLogin'))
    # print(request.session.get('id'))

    # 전체 상품 로드구간
    sql = text('''
        select * from product
    ''')

    result = session.execute(sql) 
    product_list_main = result.mappings().fetchall()
    # print(product_list_main)

    product_random_main = []
    # 4개의 랜덤 product_id를 받아 중복이 없을 때 append 진행
    while len(product_random_main) < 4 :
        check = product_list_main[random.randint(0,len(product_list_main)-1)].get('product_id', 0)
        
        if check not in product_random_main:
            product_random_main.append(check)

    # 조회순 상품 로드구간
    sql_view = text('''
        select * from product
        order by product_view_count desc
        limit 10
    ''')

    result_view = session.execute(sql_view)
    product_view_main = result_view.mappings().fetchall()
    # print('product_view_main', product_view_main)

    # print(product_view_main[0])

    # print(product_view_main[0]['product_price'])
    # print(len(product_view_main))

    return templates.TemplateResponse(request, 'main.html', {
        'product_list_main' : product_list_main,
        'product_view_main' : product_view_main,
        'product_view_main_len' : len(product_view_main),
        'product_random_1' : product_random_main[0],
        'product_random_2' : product_random_main[1],
        'product_random_3' : product_random_main[2],
        'product_random_4' : product_random_main[3],
    })

@app.get('/random_product')
def mainRandomProduct(session: Session = Depends(get_session)):
    print('''
    ========================================
    /random_product : 메인페이지 랜덤 상품 실행
    ========================================
    ''')

    sql = text('''
        select * from product
    ''')

    result = session.execute(sql) 
    product_list = result.mappings().fetchall()

    # print('랜덤', random.randint(1,len(product_list)))

    # print('product_list[0]', product_list[0])
    # print('product_list[0]', product_list[0].get('product_id'))
    # print('product_list[0]', product_list[random.randint(0,len(product_list)-1)].get('product_id', 0))

    product_random = []

    while len(product_random) < 4 :
        check = product_list[random.randint(0,len(product_list)-1)].get('product_id', 0)
        
        if check not in product_random:
            product_random.append(check)

    # print('product_random', product_random)

    return {
        'product_list' : product_list,
        'product_random_1' : product_random[0],
        'product_random_2' : product_random[1],
        'product_random_3' : product_random[2],
        'product_random_4' : product_random[3]
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
    session: Session = Depends(get_session)) :
    print('''
    ========================================
    /products : 전체 상품목록 실행
    ========================================
    ''')

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

    product_count_list = result_count.mappings().fetchall()
    product_count = product_count_list[0]['product_count']

    # 전체 페이지 수 계산
    total_page = int(product_count / 8)

    if product_count % 8 != 0:
        total_page += 1

    return templates.TemplateResponse(request, 'products.html', {
        'product_list': product_list,
        'product_count': product_count,
        'total_page': total_page,
        'page': page,
        'category_id': category_id,
        'align': align,
        'keyword': keyword
    })

@app.get('/product/detail/{product_id}')
def productsDetail(request: Request, product_id:int, reservation: str = None, session: Session = Depends(get_session)) :
    print('''
    ========================================
    /product/detail : 상품 상세 실행
    ========================================
    ''')

    sql = text('''
        select * from product p
        join category as c on (p.category_id = c.category_id)
        where product_id = :product_id
    ''')

    result = session.execute(sql, {
        'product_id' : product_id
    }) 
    product_list = result.mappings().fetchall()

    sql_view_count = text('''
        update product
        set product_view_count = product_view_count + 1
        where product_id = :product_id
    ''')
    session.execute(sql_view_count, {
        'product_id' : product_id
    })
    session.commit()

    sql_review = text('''
        select pr.* , us.user_name from product_review as pr
        join users as us on (pr.user_id = us.user_id)
        where pr.product_id = :product_id
        order by pr.product_review_id desc
    ''')

    review_result = session.execute(sql_review, {
        'product_id' : product_id
    })

    review_list = review_result.mappings().fetchall()

    sql_rating = text('''
        select round(avg(product_rating), 1) as rating_avg, count(*) as review_count
        from product_review
        where product_id = :product_id
    ''')

    rating_result = session.execute(sql_rating, {
        'product_id' : product_id
    })

    rating = rating_result.mappings().fetchone()

    rating_avg = rating['rating_avg']

    if rating_avg == None :
        rating_avg = 0

    sql_reservation_turn = text('''
        select count(*) + 1 as reservation_turn from reservation 
        where product_id = :product_id and reservation_status_id = 3
    ''')

    reservation_turn_result = session.execute(sql_reservation_turn, {
        'product_id' : product_id
    })
    reservation_turn = reservation_turn_result.mappings().fetchone()
    print(reservation_turn)

    # print('reservation : ', reservation)

    return templates.TemplateResponse(request, 'product-detail.html', {
        'product_list' : product_list,
        'review_list' : review_list,
        'rating_avg' : rating_avg,
        'review_count' : rating['review_count'],
        'reservation' : reservation,
        'reservation_turn' : reservation_turn
    })

@app.post('/product/review')
def productReview (
    request:Request,
    product_id:int = Form(), 
    review_score:int = Form(), 
    review_content:str = Form(),
    session: Session = Depends(get_session)):
    print('''
    ========================================
    /product/review : 리뷰 작성 실행
    ========================================
    ''')
    user_id = request.session.get('user_id')

    print(product_id)
    print(review_score)
    print(review_content)
    print(user_id)

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    if review_score < 1 or review_score > 5:
        return RedirectResponse(
            url=f'/product/detail/{product_id}',
            status_code=303
        )

    if review_content.strip() == '':
        return RedirectResponse(
            url=f'/product/detail/{product_id}',
            status_code=303
        )

    sql = text('''
        insert into product_review (product_review, product_rating, product_id, user_id)
        values (:product_review, :product_rating, :product_id, :user_id)
    ''')

    session.execute(sql, {
        'product_review' : review_content,
        'product_rating' : review_score,
        'product_id' : product_id,
        'user_id' : user_id
    })
    session.commit()

    return RedirectResponse(
        url=f'/product/detail/{product_id}',
        status_code=303
    )

@app.post('/product/review/report')
def productReviewReport(
    product_review_id:int = Form(), 
    product_id:int = Form(), 
    report_detail: str = Form(),
    session: Session = Depends(get_session)) :
    print('''
    ========================================
    /product/review/report : 후기 신고 실행
    ========================================
    ''')
    sql_report = text('''
        insert into review_report(report_detail, product_review_id)
        value (:report_detail, :product_review_id)
    ''')

    session.execute(sql_report, {
        'report_detail' : report_detail,
        'product_review_id' : product_review_id
    })
    session.commit()

    return RedirectResponse(
        url=f'/product/detail/{product_id}',
        status_code=303
    )

@app.post('/product/reservation')
def productReservation (
    request: Request,
    product_id:int = Form(), 
    reservation_quantity: int = Form(),
    session: Session = Depends(get_session)):
    print('''
    ========================================
    /product/reservation : 상품 예약 실행
    ========================================
    ''')

    user_id = request.session.get('user_id')

    if user_id == None :
        return RedirectResponse(
            url='/login',
            status_code=303
        )
    
    now = datetime.now()
    reservationDate = now.strftime('%Y-%m-%d %H:%M:%S')

    if reservation_quantity <= 0 or reservation_quantity > 10 :
        return RedirectResponse(
            url=f'/product/detail/{product_id}?reservation=failed',
            status_code=303
        )
    
    sql_reservation = text('''
        insert into reservation(reservation_date, reservation_quantity, product_id, user_id, reservation_status_id)
        values(:reservation_date, :reservation_quantity, :product_id, :user_id, :reservation_status_id)
    ''')

    session.execute(sql_reservation, {
        'reservation_date' : reservationDate, 
        'reservation_quantity' : reservation_quantity, 
        'product_id' : product_id, 
        'user_id' : user_id, 
        'reservation_status_id' : 3
    })

    session.commit()

    return RedirectResponse(
        url=f'/product/detail/{product_id}?reservation=success',
        status_code=303
    )

####################################
#          장바구니 관련 구역       
####################################
@app.get('/cart')
def cart(
    request: Request,
    session: Session = Depends(get_session)) :
    print('''
    ========================================
    /cart : 장바구니 실행
    ========================================
    ''')

    user_id = request.session.get('user_id')

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    print('장바구니에 담긴 ID : ',user_id)

    sql_cart = text('''
        select
            ca.cart_id,
            ca.product_quantity,
            pr.product_id,
            pr.product_name,
            pr.product_image,
            pr.product_price,
            pr.product_sale_stock,
            pr.product_active
        from cart as ca
        join product as pr
            on ca.product_id = pr.product_id
        where ca.user_id = :user_id
        order by ca.cart_id desc
    ''')

    result_cart = session.execute(sql_cart, {
        'user_id' : user_id
    })
    cart_list = result_cart.mappings().fetchall()

    sql_cart_total_price = text('''
        select sum(ca.product_quantity * pr.product_price) as total_price
        from cart as ca
        join product as pr 
        on ca.product_id = pr.product_id
        where ca.user_id = :user_id
        order by ca.cart_id desc;
    ''')

    result_cart_total_price = session.execute(sql_cart_total_price, {
        'user_id' : user_id
    })

    cart_total_price_result = result_cart_total_price.mappings().fetchone()
    # print(cart_total_price)

    cart_total_price = cart_total_price_result['total_price']

    if cart_total_price == None:
        cart_total_price = 0

    return templates.TemplateResponse(request, 'cart.html', {
        'cart_list' : cart_list,
        'cart_total_price' : cart_total_price
    })

@app.post('/cart')
def cartAdd(
    request: Request,
    cart_quantity:int = Form(),
    product_id:int = Form(),
    session: Session = Depends(get_session)) :
    print('''
    ========================================
    /cart : 장바구니 담기 실행
    ========================================
    ''')

    user_id = request.session.get('user_id')

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    if cart_quantity < 1 :
        return RedirectResponse(
            url=f'/product/detail/{product_id}',
            status_code=303
        )

    print('cart_quantity : ', cart_quantity)
    print('user_id : ', user_id)
    print('product_id : ', product_id)

    sql_cart_get = text('''
        select * from cart
        where user_id = :user_id and product_id = :product_id
    ''')

    result_cart_get = session.execute(sql_cart_get, {
        'user_id' : user_id,
        'product_id' : product_id
    })

    result_cart = result_cart_get.mappings().fetchone()
    print('result_cart : ', result_cart)

    if result_cart == None :
        sql_cart_add = text('''
            insert into cart(user_id, product_id, product_quantity)
            values(:user_id, :product_id, :product_quantity)
        ''')

        session.execute(sql_cart_add, {
            'user_id' : user_id,
            'product_id' : product_id,
            'product_quantity' : cart_quantity
        })
        session.commit()
    else :
        sql_cart_update = text('''
            update cart
            set product_quantity = product_quantity + :product_quantity
            where user_id = :user_id and product_id = :product_id
        ''')

        session.execute(sql_cart_update, {
            'product_quantity' : cart_quantity,
            'user_id' : user_id,
            'product_id' : product_id
        })
        session.commit()

    return RedirectResponse(
        url='/cart',
        status_code=303
    )

@app.post('/cart/delete')
def cartDelete(
    request:Request, 
    cart_id: int = Form(), 
    session: Session = Depends(get_session)):
    print('''
    ========================================
    /cart/delete : 장바구니 상품 삭제 실행
    ========================================
    ''')
    print('cart_id : ', cart_id)

    user_id = request.session.get('user_id')
    print('user_id : ', user_id)

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    sql_delete = text('''
        delete from cart
        where cart_id = :cart_id and user_id = :user_id
    ''')

    session.execute(sql_delete, {
        'cart_id' : cart_id,
        'user_id' : user_id
    })
    session.commit()

    return RedirectResponse(
        url='/cart',
        status_code=303
    )

@app.post('/cart/update')
def cartUpdate(
    request:Request, 
    cart_id:int = Form(), 
    product_quantity: int = Form(),
    session: Session = Depends(get_session)):
    print('''
    ========================================
    /cart/update : 장바구니 수량 변경 실행
    ========================================
    ''')

    user_id = request.session.get('user_id')

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    if product_quantity < 1 or product_quantity > 10:
        return RedirectResponse(
            url='/cart',
            status_code=303
        )

    sql_update = text('''
        update cart
        set product_quantity = :product_quantity
        where cart_id = :cart_id and user_id = :user_id 
    ''')

    session.execute(sql_update, {
        'cart_id' : cart_id,
        'user_id' : user_id,
        'product_quantity' : product_quantity
    })
    session.commit()

    return RedirectResponse(
        url='/cart',
        status_code=303
    )

@app.post('/cart/deleteSelect')
def cartDeleteSelect(
    request: Request,
    deleteSelectList: list[int],
    session: Session = Depends(get_session)):

    if len(deleteSelectList) == 0:
        return {
            'result': '삭제할 상품을 선택해 주세요.'
        }

    user_id = request.session.get('user_id')

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    deleteList = ''

    for deleteIndex in deleteSelectList :
        deleteList += str(deleteIndex) + ','

    deleteList = deleteList[:-1]
    print(deleteList)

    sql_deleteSelect = text(f'''
        select count(*) as deleteCount from cart
        where user_id = :user_id
        and cart_id in ({deleteList})
    ''')

    result_deleteSelect= session.execute(sql_deleteSelect, {
        'user_id' : user_id
    })

    deleteSelect = result_deleteSelect.mappings().fetchone()
    print('deleteSelect 결과물 : ', deleteSelect)

    deleteCount = deleteSelect['deleteCount']

    sql_delete = text(f'''
        delete from cart
        where user_id = :user_id
        and cart_id in ({deleteList})
    ''')

    session.execute(sql_delete, {
        'user_id' : user_id
    })
    session.commit()

    return {
        'result' : f'총 {deleteCount}건이 삭제되었습니다.'
    }

####################################
#          관리자 페이지 관련 구역       
####################################
@app.get('/admin')
def adminDashboard(request: Request) :
    print('''
    ========================================
    /admin : 관리자페이지 실행
    ========================================
    ''')

    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-dashboard.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

@app.get('/error-404')
def adminError(request: Request):
    print('''
    ========================================
    /error-404 : 관리자페이지 접근 불가 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'error-404.html')

@app.get('/admin/inquiries')
def adminInquiries(request: Request) :
    print('''
    ========================================
    /admin/inquiries : 관리자페이지 문의 관리 실행
    ========================================
    ''')
    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-inquiries.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

@app.get('/admin/orders')
def adminOrders(request: Request) :
    print('''
    ========================================
    /admin/orders : 관리자페이지 주문 관리 실행
    ========================================
    ''')
    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-orders.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

@app.get('/admin/products')
def adminProducts(request: Request) :
    print('''
    ========================================
    /admin/products : 관리자페이지 상품 관리 실행
    ========================================
    ''')
    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-products.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

@app.get('/admin/reservations')
def adminReservations(request: Request) :
    print('''
    ========================================
    /admin/reservations : 관리자페이지 예약 관리 실행
    ========================================
    ''')
    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-reservations.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

@app.get('/admin/users')
def adminUsers(request: Request) :
    print('''
    ========================================
    /admin/users : 관리자페이지 회원 관리 실행
    ========================================
    ''')
    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-users.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )    

####################################
#          AI 건강진단 관련 구역       
####################################
@app.get('/ai-health')
def aiHealth(request: Request):

    print('''
    ========================================
    /ai-health : AI 건강 체크 실행
    ========================================
    ''')

    user_id = request.session.get('user_id')

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

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
    print('''
    ========================================
    /ai-health : AI 건강 체크 결과 실행
    ========================================
    ''')

    user_id = request.session.get('user_id')

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    # 입력값 검증
    if health_weight < 20 or health_weight > 300:
        return RedirectResponse(
            url='/ai-health',
            status_code=303
        )

    if health_age < 1 or health_age > 120:
        return RedirectResponse(
            url='/ai-health',
            status_code=303
        )

    if health_gender not in ['남성', '여성', '기타']:
        return RedirectResponse(
            url='/ai-health',
            status_code=303
        )

    if health_sleep < 0 or health_sleep > 24:
        return RedirectResponse(
            url='/ai-health',
            status_code=303
        )

    if health_activity < 0 or health_activity > 14:
        return RedirectResponse(
            url='/ai-health',
            status_code=303
        )

    # 건강 키워드 결정
    if health_sleep < 6:
        health_keyword = 'sleep'

    elif health_age >= 60:
        health_keyword = 'health_device'

    elif health_activity < 2:
        health_keyword = 'fitness'

    else:
        health_keyword = 'nutrition'

    print('건강 키워드:', health_keyword)

    # 키워드에 해당하는 AI 피드백과 의원 검색어 조회
    sql_health_keyword = text('''
        select
            health_keyword_id,
            health_keyword,
            health_answer,
            clinic_search_keyword
        from ai_health_keyword
        where health_keyword = :health_keyword
    ''')

    result_health_keyword = session.execute(
        sql_health_keyword,
        {
            'health_keyword': health_keyword
        }
    )

    health_keyword_result = (
        result_health_keyword.mappings().fetchone()
    )

    if health_keyword_result == None:
        return RedirectResponse(
            url='/ai-health',
            status_code=303
        )

    health_keyword_id = (
        health_keyword_result['health_keyword_id']
    )

    health_result = (
        health_keyword_result['health_answer']
    )

    clinic_search_keyword = (
        health_keyword_result['clinic_search_keyword']
    )

    # 건강 체크 입력값과 결과 저장
    sql_health_insert = text('''
        insert into ai_health
        (
            health_weight,
            health_age,
            health_gender,
            health_sleep,
            health_activity,
            health_result,
            health_keyword_id,
            user_id
        )
        values
        (
            :health_weight,
            :health_age,
            :health_gender,
            :health_sleep,
            :health_activity,
            :health_result,
            :health_keyword_id,
            :user_id
        )
    ''')

    result_health_insert = session.execute(
        sql_health_insert,
        {
            'health_weight': health_weight,
            'health_age': health_age,
            'health_gender': health_gender,
            'health_sleep': health_sleep,
            'health_activity': health_activity,
            'health_result': health_result,
            'health_keyword_id': health_keyword_id,
            'user_id': user_id
        }
    )

    health_id = result_health_insert.lastrowid

    # 키워드에 연결된 판매 중인 상품 중 3개 조회
    sql_recommended_product = text('''
        select
            pr.product_id,
            pr.product_name,
            pr.product_image,
            pr.product_price,
            pr.product_sale_stock,
            pr.product_active
        from product_health_keyword as phk
        join product as pr
            on phk.product_id = pr.product_id
        where phk.health_keyword_id = :health_keyword_id
        and pr.product_active = 1
        order by rand()
        limit 3
    ''')

    result_recommended_product = session.execute(
        sql_recommended_product,
        {
            'health_keyword_id': health_keyword_id
        }
    )

    recommended_product_list = (
        result_recommended_product.mappings().fetchall()
    )

    # 추천 결과 저장
    sql_recommendation_insert = text('''
        insert into ai_health_recommendation
        (
            health_id,
            product_id,
            recommendation_rank
        )
        values
        (
            :health_id,
            :product_id,
            :recommendation_rank
        )
    ''')

    recommendation_rank = 1

    for product in recommended_product_list:

        session.execute(
            sql_recommendation_insert,
            {
                'health_id': health_id,
                'product_id': product['product_id'],
                'recommendation_rank': recommendation_rank
            }
        )

        recommendation_rank += 1

    session.commit()

    return templates.TemplateResponse(
        request,
        'ai-health.html',
        {
            'health_result': health_result,
            'recommended_product_list':
                recommended_product_list,
            'clinic_search_keyword':
                clinic_search_keyword
        }
    )

####################################
#          상품 주문 관련 구역       
####################################
@app.get('/checkout')
def checkout(request: Request, session: Session = Depends(get_session)) :
    print('''
    ========================================
    /checkout : 주문서 작성 실행
    ========================================
    ''')
    user_id = request.session.get('user_id')
    checkout_type = request.session.get('checkout_type')
    product_id = request.session.get('checkout_product_id')
    buy_quantity = request.session.get('checkout_quantity')
    cartBuyList = request.session.get('checkout_cart_ids')

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )
    if checkout_type == 'direct' :
        if product_id == None or buy_quantity == None:
            return RedirectResponse(
                url='/products',
                status_code=303
            )
    elif checkout_type == 'reservation' :
        if product_id == None or buy_quantity == None:
            return RedirectResponse(
                url='/mypage/reservations',
                status_code=303
            )
    elif checkout_type == 'cart':
        cartBuyList = request.session.get('checkout_cart_ids')

        if cartBuyList == None or len(cartBuyList) == 0:
            return RedirectResponse(
                url='/cart',
                status_code=303
            ) 
    else :
        return RedirectResponse(
            url='/products',
            status_code=303
        )

    print(user_id)
    print(product_id)
    print(buy_quantity)
    if checkout_type == 'direct' or checkout_type == 'reservation' :
        sql_checkout = text('''
            select * from product
            where product_id = :product_id
        ''')

        result_checkout = session.execute(sql_checkout, {
            'product_id': product_id
        })

        checkout_product = result_checkout.mappings().fetchone()

        if checkout_product == None:
            return RedirectResponse(
                url='/products',
                status_code=303
            )
    elif checkout_type == 'cart' :

        if cartBuyList == None or len(cartBuyList) == 0:
            return RedirectResponse(
                url='/cart',
                status_code=303
            )

        cartList = ''
        for cartIndex in cartBuyList :
            cartList += str(cartIndex) + ','

        cartList = cartList[:-1]

        sql_checkout = text(f'''
            select
                ca.cart_id,
                ca.product_quantity,
                pr.product_id,
                pr.product_name,
                pr.product_image,
                pr.product_price,
                pr.product_sale_stock,
                pr.product_active
            from cart as ca
            join product as pr
                on ca.product_id = pr.product_id
            where ca.user_id = :user_id
            and ca.cart_id in ({cartList})
        ''')

        result_checkout = session.execute(sql_checkout, {
            'user_id': user_id
        })

        checkout_product = result_checkout.mappings().fetchall()

        if len(checkout_product) != len(cartBuyList):
            return RedirectResponse(
                url='/cart',
                status_code=303
            )

    print(checkout_product)

    sql_checkout_user = text('''
        select * from users
        where user_id = :user_id
    ''')

    result_checkout_user = session.execute(sql_checkout_user, {
        'user_id' : user_id
    })

    checkout_user = result_checkout_user.mappings().fetchone()

    if checkout_user == None:
        request.session.clear()

        return RedirectResponse(
            url='/login',
            status_code=303
        )

    if checkout_type =='cart' :
        checkout_total_price = 0

        for product in checkout_product :
            checkout_total_price += (product['product_price'] * product['product_quantity'])
    else :
        checkout_total_price = (checkout_product['product_price'] * buy_quantity)

    return templates.TemplateResponse(request, 'checkout.html', {
        'checkout_type' : checkout_type,
        'checkout_product': checkout_product,
        'buy_quantity': buy_quantity,
        'checkout_total_price': checkout_total_price,
        'checkout_user' : checkout_user
    })

@app.post('/checkout/direct')
def checkoutBuy (request:Request, buy_quantity: int = Form(), product_id:int = Form(), session: Session = Depends(get_session)) :
    print('''
    ========================================
    /checkout/direct : 상품 상세 바로구매 실행
    ========================================
    ''')
    print(buy_quantity)
    print(product_id)
    user_id = request.session.get('user_id')
    print(user_id)

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    if buy_quantity < 1:
        return RedirectResponse(
            url=f'/product/detail/{product_id}',
            status_code=303
        )

    sql_checkout = text('''
        select * from product
        where product_id = :product_id
    ''')

    result_checkout = session.execute(sql_checkout, {
        'product_id' : product_id
    })

    product = result_checkout.mappings().fetchone()

    if product == None:
        return RedirectResponse(
            url='/products',
            status_code=303
        )

    if product['product_active'] != 1:
        return RedirectResponse(
            url=f'/product/detail/{product_id}',
            status_code=303
        )

    if buy_quantity > product['product_sale_stock']:
        return RedirectResponse(
            url=f'/product/detail/{product_id}',
            status_code=303
        )

    request.session['checkout_product_id'] = product_id
    request.session['checkout_quantity'] = buy_quantity
    request.session['checkout_type'] = 'direct'

    return RedirectResponse(
        url='/checkout',
        status_code=303
    )   

@app.post('/checkout/reservation')
def checkOutReservation(
    request:Request, 
    product_id:int = Form(), 
    reservation_quantity:int = Form(), 
    reservation_id:int = Form(),
    session: Session = Depends(get_session)):
    print('''
    ========================================
    /checkout/reservaton : 예약 관리 바로구매 실행
    ========================================
    ''')

    user_id = request.session.get('user_id')

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )
    sql_reservation_check = text('''
        select *
        from reservation
        where reservation_id = :reservation_id
        and user_id = :user_id
        and product_id = :product_id
        and reservation_quantity = :reservation_quantity
        and reservation_status_id = 2
    ''')

    result_reservation_check = session.execute(
        sql_reservation_check,
        {
            'reservation_id': reservation_id,
            'user_id': user_id,
            'product_id': product_id,
            'reservation_quantity': reservation_quantity
        }
    )

    reservation_check = (
        result_reservation_check.mappings().fetchone()
    )

    if reservation_check == None:
        return RedirectResponse(
            url='/mypage/reservations',
            status_code=303
        )

    if reservation_quantity < 1:
        return RedirectResponse(
            url='/mypage/reservations',
            status_code=303
        )

    sql_checkout = text('''
        select * from product
        where product_id = :product_id
    ''')

    result_checkout = session.execute(sql_checkout, {
        'product_id' : product_id
    })

    product = result_checkout.mappings().fetchone()

    if product == None:
        return RedirectResponse(
            url='/mypage/reservations',
            status_code=303
        )

    if product['product_active'] != 1:
        return RedirectResponse(
            url='/mypage/reservations',
            status_code=303
        )

    if reservation_quantity > product['product_reservation_stock']:
        return RedirectResponse(
            url='/mypage/reservations',
            status_code=303
        )

    request.session['checkout_product_id'] = product_id
    request.session['checkout_quantity'] = reservation_quantity
    request.session['checkout_type'] = 'reservation'
    request.session['checkout_reservation_id'] = reservation_id

    return RedirectResponse(
        url='/checkout',
        status_code=303
    )   

@app.post('/checkout/cart')
def cartDeleteSelect(
    request: Request,
    cartBuyList: list[int],
    session: Session = Depends(get_session)):

    if len(cartBuyList) == 0:
        return {
            'result': '주문하실 상품을 선택해 주세요.'
        }

    user_id = request.session.get('user_id')

    if user_id == None:
        return {
            'result': 'login'
        }

    cartList = ''

    for cartIndex in cartBuyList :
        cartList += str(cartIndex) + ','

    cartList = cartList[:-1]
    print(cartList)

    sql_cartSelect = text(f'''
        select count(*) as buyCount from cart
        where user_id = :user_id
        and cart_id in ({cartList})
    ''')

    result_cartSelect= session.execute(sql_cartSelect, {
        'user_id' : user_id
    })

    cartSelect = result_cartSelect.mappings().fetchone()
    print('cartSelect 결과물 : ', cartSelect)

    if cartSelect['buyCount'] != len(cartBuyList):
        return {
            'result': 'failed',
            'message': '선택한 장바구니 정보를 확인할 수 없습니다.'
        }

    request.session['checkout_cart_ids'] = cartBuyList
    request.session['checkout_type'] = 'cart'

    return {
        'result' : 'success'
    }

@app.post('/checkout/card')
def checkOutCard(
    request:Request,
    order_name:str = Form(),
    order_phone:str = Form(),
    order_addr:str = Form(),
    order_addr_detail:str = Form(),
    payment_method:str = Form(),
    session: Session = Depends(get_session)):
    print('''
    ========================================
    /checkout/card : 체크아웃 카드결제 실행
    ========================================
    ''')
    product_id = request.session.get('checkout_product_id')
    buy_quantity = request.session.get('checkout_quantity')
    checkout_type = request.session.get('checkout_type')
    reservation_id = request.session.get('checkout_reservation_id')
    user_id = request.session.get('user_id')

    print('구매 시 PRID : ', product_id)
    print('구매 시 수량 : ', buy_quantity)
    print('구매 시 경로 : ', checkout_type)

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    if checkout_type == 'direct' or checkout_type == 'reservation':
        if product_id == None or buy_quantity == None:
            return RedirectResponse(
                url='/products',
                status_code=303
            )

    elif checkout_type == 'cart':
        cartBuyList = request.session.get('checkout_cart_ids')

        if cartBuyList == None or len(cartBuyList) == 0:
            return RedirectResponse(
                url='/cart',
                status_code=303
            )

    else:
        return RedirectResponse(
            url='/products',
            status_code=303
        )


    if checkout_type == 'direct' or checkout_type == 'reservation':

        sql_checkout_stock = text('''
            select * from product
            where product_id = :product_id
        ''')

        result_checkout_stock = session.execute(sql_checkout_stock, {
            'product_id': product_id
        })

        checkout_stock = result_checkout_stock.mappings().fetchone()

        if checkout_stock == None:
            return RedirectResponse(
                url='/products',
                status_code=303
            )

        if checkout_stock['product_active'] != 1:
            return RedirectResponse(
                url='/products',
                status_code=303
            )

        if buy_quantity < 1:
            return RedirectResponse(
                url=f'/product/detail/{product_id}',
                status_code=303
            )

    # 장바구니 상품 조회
    elif checkout_type == 'cart':

        cartList = ''

        for cartIndex in cartBuyList:
            cartList += str(cartIndex) + ','

        cartList = cartList[:-1]

        sql_checkout_cart = text(f'''
            select
                ca.cart_id,
                ca.product_quantity,
                pr.product_id,
                pr.product_price,
                pr.product_sale_stock,
                pr.product_active
            from cart as ca
            join product as pr
                on ca.product_id = pr.product_id
            where ca.user_id = :user_id
            and ca.cart_id in ({cartList})
        ''')

        result_checkout_cart = session.execute(sql_checkout_cart, {
            'user_id': user_id
        })

        checkout_cart_list = (
            result_checkout_cart.mappings().fetchall()
        )

        # 선택한 장바구니 개수와 조회된 개수가 다른 경우
        if len(checkout_cart_list) != len(cartBuyList):
            return RedirectResponse(
                url='/cart',
                status_code=303
            )

        # 상품별 판매 상태와 재고 검사
    
        for cartProduct in checkout_cart_list:

            if cartProduct['product_active'] != 1:
                return RedirectResponse(
                    url='/cart',
                    status_code=303
                )

            if cartProduct['product_quantity'] < 1:
                return RedirectResponse(
                    url='/cart',
                    status_code=303
                )

            if (
                cartProduct['product_sale_stock']
                < cartProduct['product_quantity']
            ):
                return RedirectResponse(
                    url='/cart?checkout=stock_failed',
                    status_code=303
                )

    if checkout_type == 'direct':
        if checkout_stock['product_sale_stock'] < buy_quantity:
            return RedirectResponse(
                url=f'/product/detail/{product_id}',
                status_code=303
            )

    elif checkout_type == 'reservation':
        if checkout_stock['product_reservation_stock'] < buy_quantity:
            return RedirectResponse(
                url='/mypage/reservations',
                status_code=303
            )

    now = datetime.now()
    checkoutDate = now.strftime('%Y-%m-%d %H:%M:%S')

    if checkout_type == 'cart':

        checkout_total_price = 0

        for cartProduct in checkout_cart_list:
            checkout_total_price += (
                cartProduct['product_price']
                * cartProduct['product_quantity']
            )

    else:
        checkout_total_price = (
            checkout_stock['product_price']
            * buy_quantity
        )

    sql_checkout_sheet = text('''
        insert into order_sheet (order_sheet_date, order_total_price)
        values (:checkoutDate, :checkout_total_price)
    ''')

    result_checkout_sheet = session.execute(sql_checkout_sheet, {
        'checkoutDate' : checkoutDate,
        'checkout_total_price' : checkout_total_price
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
                'order_addr': order_addr + ' ' + order_addr_detail,
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
            'order_addr': order_addr + ' ' + order_addr_detail,
            'order_phone': order_phone,
            'product_id': product_id,
            'order_quantity': buy_quantity,
            'order_sheet_id': checkout_sheet_id,
            'order_price': checkout_stock['product_price']
        })

    sql_payment = text('''
        insert into payment
        (payment_method, payment_failure_reason, payment_status_id, order_sheet_id)
        values (:payment_method, null, 2, :order_sheet_id)
    ''')

    session.execute(sql_payment, {
        'payment_method' : payment_method,
        'order_sheet_id' : checkout_sheet_id
    })

    # 바로 구매 판매재고 차감
    if checkout_type == 'direct':

        sql_stock_update = text('''
            update product
            set product_sale_stock =
                product_sale_stock - :order_quantity
            where product_id = :product_id
            and product_sale_stock >= :order_quantity
            and product_active = 1
        ''')

        result_stock_update = session.execute(sql_stock_update, {
            'order_quantity': buy_quantity,
            'product_id': product_id
        })

        if result_stock_update.rowcount == 0:
            session.rollback()

            return RedirectResponse(
                url=f'/product/detail/{product_id}',
                status_code=303
            )


    # 예약 구매 예약재고 차감
    elif checkout_type == 'reservation':

        sql_stock_update = text('''
            update product
            set product_reservation_stock =
                product_reservation_stock - :order_quantity
            where product_id = :product_id
            and product_reservation_stock >= :order_quantity
            and product_active = 1
        ''')

        result_stock_update = session.execute(sql_stock_update, {
            'order_quantity': buy_quantity,
            'product_id': product_id
        })

        if result_stock_update.rowcount == 0:
            session.rollback()

            return RedirectResponse(
                url='/mypage/reservations',
                status_code=303
            )

    # 장바구니 상품별 판매재고 차감
    elif checkout_type == 'cart':

        sql_stock_update = text('''
            update product
            set product_sale_stock =
                product_sale_stock - :order_quantity
            where product_id = :product_id
            and product_sale_stock >= :order_quantity
            and product_active = 1
        ''')

        for cartProduct in checkout_cart_list:

            result_stock_update = session.execute(sql_stock_update, {
                'order_quantity': cartProduct['product_quantity'],
                'product_id': cartProduct['product_id']
            })

            if result_stock_update.rowcount == 0:
                session.rollback()

                return RedirectResponse(
                    url='/cart',
                    status_code=303
                )

    sql_delivery = text('''
        insert into delivery (delivery_receiver, delivery_addr, delivery_phone, delivery_status_id, order_sheet_id)
        values (:delivery_receiver, :delivery_addr, :delivery_phone, 1, :order_sheet_id)
    ''')

    session.execute(sql_delivery,{
        'delivery_receiver' : order_name,
        'delivery_addr' : order_addr + ' ' + order_addr_detail,
        'delivery_phone' : order_phone,
        'order_sheet_id' : checkout_sheet_id
    })

    if checkout_type == 'reservation':
        if reservation_id == None:
            session.rollback()

            return RedirectResponse(
                url='/mypage/reservations',
                status_code=303
            )

        sql_reservation_delete = text('''
            delete from reservation
            where reservation_id = :reservation_id
            and user_id = :user_id
            and product_id = :product_id
            and reservation_status_id = 2
        ''')

        result_reservation_delete = session.execute(
            sql_reservation_delete,
            {
                'reservation_id': reservation_id,
                'user_id': user_id,
                'product_id': product_id
            }
        )

        if result_reservation_delete.rowcount == 0:
            session.rollback()

            return RedirectResponse(
                url='/mypage/reservations',
                status_code=303
            )
    if checkout_type == 'cart':

        sql_cart_delete = text(f'''
            delete from cart
            where user_id = :user_id
            and cart_id in ({cartList})
        ''')

        result_cart_delete = session.execute(sql_cart_delete, {
            'user_id': user_id
        })

        if result_cart_delete.rowcount != len(cartBuyList):
            session.rollback()

            return RedirectResponse(
                url='/cart',
                status_code=303
            )
        
    session.commit()

    request.session.pop('checkout_product_id', None)
    request.session.pop('checkout_quantity', None)
    request.session.pop('checkout_type', None)
    request.session.pop('checkout_reservation_id', None)
    request.session.pop('checkout_cart_ids', None)

    return RedirectResponse(
        url=f'/payment/result?order_sheet_id={checkout_sheet_id}',
        status_code=303
    )

####################################
#          상품 결제 관련 구역       
####################################
@app.get('/payment/result')
def paymentResult(
    request: Request,
    order_sheet_id: int,
    session: Session = Depends(get_session)
):
    user_id = request.session.get('user_id')

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    sql_order = text('''
        select
            os.order_sheet_id,
            os.order_sheet_date,
            os.order_total_price,
            od.order_name
        from order_sheet as os
        join orders as od
            on os.order_sheet_id = od.order_sheet_id
        where os.order_sheet_id = :order_sheet_id
          and od.user_id = :user_id
        limit 1
    ''')

    result_order = session.execute(sql_order, {
        'order_sheet_id': order_sheet_id,
        'user_id': user_id
    })

    payment_result = result_order.mappings().fetchone()

    if payment_result == None:
        return RedirectResponse(
            url='/',
            status_code=303
        )

    print(payment_result)

    return templates.TemplateResponse(request, 'payment-result.html',{
            'payment_result': payment_result
        }
    )

####################################
#          커뮤니티 관련 구역       
####################################
@app.get('/notice')
def commNotice(
    request: Request,
    keyword: str = '',
    page: int = 1,
    session: Session = Depends(get_session)
):
    print('''
    ========================================
    /notice : 커뮤니티 공지사항 실행
    ========================================
    ''')

    keyword = keyword.strip()

    if page < 1:
        page = 1

    page_size = 10
    page_start = (page - 1) * page_size

    sql_notice = text('''
        select
            notice_id,
            notice_title,
            notice_detail,
            notice_date,
            user_id
        from notice
        where (
            :keyword = ''
            or notice_title like :search_keyword
            or notice_detail like :search_keyword
        )
        order by notice_id desc
        limit :page_start, :page_size
    ''')

    result_notice = session.execute(
        sql_notice,
        {
            'keyword': keyword,
            'search_keyword': '%' + keyword + '%',
            'page_start': page_start,
            'page_size': page_size
        }
    )

    notice_list = (
        result_notice
        .mappings()
        .fetchall()
    )

    sql_notice_count = text('''
        select count(*) as notice_count
        from notice
        where (
            :keyword = ''
            or notice_title like :search_keyword
            or notice_detail like :search_keyword
        )
    ''')

    result_count = session.execute(
        sql_notice_count,
        {
            'keyword': keyword,
            'search_keyword': '%' + keyword + '%'
        }
    )

    notice_count = (
        result_count
        .mappings()
        .fetchone()['notice_count']
    )

    total_page = int(notice_count / page_size)

    if notice_count % page_size != 0:
        total_page += 1

    return templates.TemplateResponse(
        request,
        'notice.html',
        {
            'notice_list': notice_list,
            'keyword': keyword,
            'page': page,
            'total_page': total_page
        }
    )

@app.get('/notice/write')
def noticeWrite(request: Request):
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        'notice-editor.html',
        {
            'editor_mode': 'write',
            'notice': None
        }
    )


@app.post('/notice/write')
def noticeWriteData(
    request: Request,
    notice_title: str = Form(),
    notice_detail: str = Form(),
    session: Session = Depends(get_session)
):
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

    notice_title = notice_title.strip()
    notice_detail = notice_detail.strip()

    if notice_title == '' or notice_detail == '':
        return RedirectResponse(
            url='/notice/write',
            status_code=303
        )

    notice_date = datetime.now().strftime('%Y-%m-%d')

    sql_notice_write = text('''
        insert into notice (
            notice_title,
            notice_detail,
            notice_date,
            user_id
        )
        values (
            :notice_title,
            :notice_detail,
            :notice_date,
            :user_id
        )
    ''')

    session.execute(
        sql_notice_write,
        {
            'notice_title': notice_title,
            'notice_detail': notice_detail,
            'notice_date': notice_date,
            'user_id': request.session.get('user_id')
        }
    )

    session.commit()

    return RedirectResponse(
        url='/notice',
        status_code=303
    )

@app.get('/notice/edit/{notice_id}')
def noticeEdit(
    request: Request,
    notice_id: int,
    session: Session = Depends(get_session)
):
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

    sql_notice = text('''
        select *
        from notice
        where notice_id = :notice_id
    ''')

    result_notice = session.execute(
        sql_notice,
        {
            'notice_id': notice_id
        }
    )

    notice = (
        result_notice
        .mappings()
        .fetchone()
    )

    if notice is None:
        return RedirectResponse(
            url='/notice',
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        'notice-editor.html',
        {
            'editor_mode': 'edit',
            'notice': notice
        }
    )


@app.post('/notice/edit/{notice_id}')
def noticeEditData(
    request: Request,
    notice_id: int,
    notice_title: str = Form(),
    notice_detail: str = Form(),
    session: Session = Depends(get_session)
):
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

    notice_title = notice_title.strip()
    notice_detail = notice_detail.strip()

    if notice_title == '' or notice_detail == '':
        return RedirectResponse(
            url=f'/notice/edit/{notice_id}',
            status_code=303
        )

    sql_notice_update = text('''
        update notice
        set
            notice_title = :notice_title,
            notice_detail = :notice_detail
        where notice_id = :notice_id
    ''')

    session.execute(
        sql_notice_update,
        {
            'notice_title': notice_title,
            'notice_detail': notice_detail,
            'notice_id': notice_id
        }
    )

    session.commit()

    return RedirectResponse(
        url='/notice',
        status_code=303
    )

@app.post('/notice/delete')
def noticeDelete(
    request: Request,
    notice_id: int = Form(),
    session: Session = Depends(get_session)
):
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

    sql_notice_delete = text('''
        delete from notice
        where notice_id = :notice_id
    ''')

    session.execute(
        sql_notice_delete,
        {
            'notice_id': notice_id
        }
    )

    session.commit()

    return RedirectResponse(
        url='/notice',
        status_code=303
    )

@app.get('/faq')
def commFaq(
    request: Request,
    keyword: str = '',
    page: int = 1,
    session: Session = Depends(get_session)
):
    print('''
========================================
/faq : 커뮤니티 자주 묻는 질문 실행
========================================
''')

    keyword = keyword.strip()

    if page < 1:
        page = 1

    page_size = 10
    page_start = (page - 1) * page_size

    sql_faq = text('''
        select
            faq_id,
            faq_title,
            faq_detail,
            faq_date,
            user_id
        from faq
        where (
            :keyword = ''
            or faq_title like :search_keyword
            or faq_detail like :search_keyword
        )
        order by faq_id desc
        limit :page_start, :page_size
    ''')

    result_faq = session.execute(
        sql_faq,
        {
            'keyword': keyword,
            'search_keyword': '%' + keyword + '%',
            'page_start': page_start,
            'page_size': page_size
        }
    )

    faq_list = (
        result_faq
        .mappings()
        .fetchall()
    )

    sql_faq_count = text('''
        select count(*) as faq_count
        from faq
        where (
            :keyword = ''
            or faq_title like :search_keyword
            or faq_detail like :search_keyword
        )
    ''')

    result_count = session.execute(
        sql_faq_count,
        {
            'keyword': keyword,
            'search_keyword': '%' + keyword + '%'
        }
    )

    faq_count = (
        result_count
        .mappings()
        .fetchone()['faq_count']
    )

    total_page = int(faq_count / page_size)

    if faq_count % page_size != 0:
        total_page += 1

    return templates.TemplateResponse(
        request,
        'faq.html',
        {
            'faq_list': faq_list,
            'keyword': keyword,
            'page': page,
            'total_page': total_page
        }
    )
@app.get('/faq/write')
def faqWrite(request: Request):
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        'faq-editor.html',
        {
            'editor_mode': 'write',
            'faq': None
        }
    )

@app.post('/faq/write')
def faqWriteData(
    request: Request,
    faq_title: str = Form(),
    faq_detail: str = Form(),
    session: Session = Depends(get_session)
):
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

    faq_title = faq_title.strip()
    faq_detail = faq_detail.strip()

    if faq_title == '' or faq_detail == '':
        return RedirectResponse(
            url='/faq/write',
            status_code=303
        )

    faq_date = datetime.now().strftime('%Y-%m-%d')

    sql_faq_write = text('''
        insert into faq (
            faq_title,
            faq_detail,
            faq_date,
            user_id
        )
        values (
            :faq_title,
            :faq_detail,
            :faq_date,
            :user_id
        )
    ''')

    session.execute(
        sql_faq_write,
        {
            'faq_title': faq_title,
            'faq_detail': faq_detail,
            'faq_date': faq_date,
            'user_id': request.session.get('user_id')
        }
    )

    session.commit()

    return RedirectResponse(
        url='/faq',
        status_code=303
    )

@app.get('/faq/edit/{faq_id}')
def faqEdit(
    request: Request,
    faq_id: int,
    session: Session = Depends(get_session)
):
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

    sql_faq = text('''
        select *
        from faq
        where faq_id = :faq_id
    ''')

    result_faq = session.execute(
        sql_faq,
        {
            'faq_id': faq_id
        }
    )

    faq = (
        result_faq
        .mappings()
        .fetchone()
    )

    if faq is None:
        return RedirectResponse(
            url='/faq',
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        'faq-editor.html',
        {
            'editor_mode': 'edit',
            'faq': faq
        }
    )

@app.post('/faq/edit/{faq_id}')
def faqEditData(
    request: Request,
    faq_id: int,
    faq_title: str = Form(),
    faq_detail: str = Form(),
    session: Session = Depends(get_session)
):
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

    faq_title = faq_title.strip()
    faq_detail = faq_detail.strip()

    if faq_title == '' or faq_detail == '':
        return RedirectResponse(
            url=f'/faq/edit/{faq_id}',
            status_code=303
        )

    sql_faq_update = text('''
        update faq
        set
            faq_title = :faq_title,
            faq_detail = :faq_detail
        where faq_id = :faq_id
    ''')

    session.execute(
        sql_faq_update,
        {
            'faq_title': faq_title,
            'faq_detail': faq_detail,
            'faq_id': faq_id
        }
    )

    session.commit()

    return RedirectResponse(
        url='/faq',
        status_code=303
    )

@app.post('/faq/delete')
def faqDelete(
    request: Request,
    faq_id: int = Form(),
    session: Session = Depends(get_session)
):
    if request.session.get('user_id') != 'admin':
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

    sql_faq_delete = text('''
        delete from faq
        where faq_id = :faq_id
    ''')

    session.execute(
        sql_faq_delete,
        {
            'faq_id': faq_id
        }
    )

    session.commit()

    return RedirectResponse(
        url='/faq',
        status_code=303
    )

@app.get('/inquiry/write')
def commInquiryWrite(request: Request):
    print('''
========================================
/inquiry/write : 커뮤니티 일대일 문의 실행
========================================
''')

    user_id = request.session.get('user_id')

    if user_id is None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        'inquiry-write.html'
    )

@app.post('/inquiry/write')
def commInquiryWriteData(
    request: Request,
    inquiry_type: str = Form(),
    inquiry_title: str = Form(),
    inquiry_detail: str = Form(),
    session: Session = Depends(get_session)
):
    print('''
========================================
/inquiry/write : 일대일 문의 등록
========================================
''')

    user_id = request.session.get('user_id')

    if user_id is None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    inquiry_type = inquiry_type.strip()
    inquiry_title = inquiry_title.strip()
    inquiry_detail = inquiry_detail.strip()

    inquiry_type_list = [
        '상품문의',
        '배송문의',
        '예약문의',
        '기타문의'
    ]

    if inquiry_type not in inquiry_type_list:
        return RedirectResponse(
            url='/inquiry/write',
            status_code=303
        )

    if (
        inquiry_title == ''
        or inquiry_detail == ''
    ):
        return RedirectResponse(
            url='/inquiry/write',
            status_code=303
        )

    if (
        len(inquiry_title) > 200
        or len(inquiry_detail) > 3000
    ):
        return RedirectResponse(
            url='/inquiry/write',
            status_code=303
        )

    inquiry_date = (
        datetime.now()
        .strftime('%Y-%m-%d')
    )

    sql_inquiry_write = text('''
        insert into inquiry (
            inquiry_title,
            inquiry_detail,
            inquiry_attachment,
            inquiry_date,
            inquiry_answer,
            inquiry_answer_date,
            user_id,
            inquiry_status_id,
            inquiry_type
        )
        values (
            :inquiry_title,
            :inquiry_detail,
            null,
            :inquiry_date,
            null,
            null,
            :user_id,
            1,
            :inquiry_type
        )
    ''')

    session.execute(
        sql_inquiry_write,
        {
            'inquiry_title': inquiry_title,
            'inquiry_detail': inquiry_detail,
            'inquiry_date': inquiry_date,
            'user_id': user_id,
            'inquiry_type': inquiry_type
        }
    )

    session.commit()

    return RedirectResponse(
        url='/mypage/inquiries?write_result=success',
        status_code=303
    )

####################################
#          마이페이지 관련 구역       
####################################
@app.get('/mypage')
def mypage(request: Request) :
    print('''
    ========================================
    /mypage : 마이페이지 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'mypage-dashboard.html')

@app.get('/mypage/inquiries')
def mypageInquiries(
    request: Request,
    page: int = 1,
    session: Session = Depends(get_session)
):
    print('''
========================================
/mypage/inquiries : 마이페이지 일대일 문의 실행
========================================
''')

    user_id = request.session.get('user_id')

    if user_id is None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    if page < 1:
        page = 1

    page_size = 10
    page_start = (page - 1) * page_size

    sql_inquiry = text('''
        select
            iq.inquiry_id,
            iq.inquiry_type,
            iq.inquiry_title,
            iq.inquiry_detail,
            iq.inquiry_attachment,
            iq.inquiry_date,
            iq.inquiry_answer,
            iq.inquiry_answer_date,
            iq.inquiry_status_id,
            ist.inquiry_status_name
        from inquiry as iq
        join inquiry_status as ist
            on iq.inquiry_status_id =
               ist.inquiry_status_id
        where iq.user_id = :user_id
        order by iq.inquiry_id desc
        limit :page_start, :page_size
    ''')

    result_inquiry = session.execute(
        sql_inquiry,
        {
            'user_id': user_id,
            'page_start': page_start,
            'page_size': page_size
        }
    )

    inquiry_list = (
        result_inquiry
        .mappings()
        .fetchall()
    )

    sql_inquiry_count = text('''
        select count(*) as inquiry_count
        from inquiry
        where user_id = :user_id
    ''')

    result_count = session.execute(
        sql_inquiry_count,
        {
            'user_id': user_id
        }
    )

    inquiry_count = (
        result_count
        .mappings()
        .fetchone()['inquiry_count']
    )

    total_page = int(inquiry_count / page_size)

    if inquiry_count % page_size != 0:
        total_page += 1

    return templates.TemplateResponse(
        request,
        'mypage-inquiries.html',
        {
            'inquiry_list': inquiry_list,
            'page': page,
            'total_page': total_page
        }
    )

@app.post('/mypage/inquiry/delete')
def mypageInquiryDelete(
    request: Request,
    inquiry_id: int = Form(),
    session: Session = Depends(get_session)
):
    print('''
========================================
/mypage/inquiry/delete : 내 문의 삭제
========================================
''')

    user_id = request.session.get('user_id')

    if user_id is None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    sql_inquiry_delete = text('''
        delete from inquiry
        where inquiry_id = :inquiry_id
          and user_id = :user_id
    ''')

    session.execute(
        sql_inquiry_delete,
        {
            'inquiry_id': inquiry_id,
            'user_id': user_id
        }
    )

    session.commit()

    return RedirectResponse(
        url='/mypage/inquiries?delete_result=success',
        status_code=303
    )

@app.get('/mypage/orders')
def mypageOrders(request: Request) :
    print('''
    ========================================
    /mypage/orders : 마이페이지 주문 관리 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'mypage-orders.html')

@app.get('/mypage/profile')
def mypageProfile(
    request: Request,
    session: Session = Depends(get_session)
):
    print('''
========================================
/mypage/profile : 마이페이지 회원 정보 실행
========================================
''')

    user_id = request.session.get('user_id')

    if user_id is None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    sql_profile = text('''
        select
            user_id,
            user_name,
            user_email,
            user_phone,
            user_addr,
            user_addr_detail
        from users
        where user_id = :user_id
    ''')

    result_profile = session.execute(
        sql_profile,
        {
            'user_id': user_id
        }
    )

    user_profile = (
        result_profile
        .mappings()
        .fetchone()
    )

    if user_profile is None:
        request.session.clear()

        return RedirectResponse(
            url='/login',
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        'mypage-profile.html',
        {
            'user_profile': user_profile
        }
    )

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
    print('''
========================================
/mypage/profile : 마이페이지 회원 정보 수정
========================================
''')

    user_id = request.session.get('user_id')

    if user_id is None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    user_name = user_name.strip()
    user_addr = user_addr.strip()
    user_addr_detail = user_addr_detail.strip()
    user_email = user_email.strip()

    # 010-1234-5678 → 01012345678
    user_phone = (
        user_phone
        .strip()
        .replace('-', '')
    )

    if (
        user_name == ''
        or user_addr == ''
        or user_addr_detail == ''
        or user_email == ''
    ):
        return RedirectResponse(
            url='/mypage/profile',
            status_code=303
        )

    if (
        not user_phone.isdigit()
        or len(user_phone) != 11
        or not user_phone.startswith('010')
    ):
        return RedirectResponse(
            url='/mypage/profile',
            status_code=303
        )

    sql_profile_update = text('''
        update users
        set
            user_name = :user_name,
            user_addr = :user_addr,
            user_addr_detail = :user_addr_detail,
            user_email = :user_email,
            user_phone = :user_phone
        where user_id = :user_id
    ''')

    session.execute(
        sql_profile_update,
        {
            'user_name': user_name,
            'user_addr': user_addr,
            'user_addr_detail': user_addr_detail,
            'user_email': user_email,
            'user_phone': user_phone,
            'user_id': user_id
        }
    )

    session.commit()

    # 헤더에 표시되는 이름도 변경
    request.session['user_name'] = user_name

    return RedirectResponse(
        url='/mypage/profile',
        status_code=303
    )

@app.post('/mypage/profile/password')
def mypagePasswordUpdate(
    request: Request,
    current_password: str = Form(),
    new_password: str = Form(),
    new_password_confirm: str = Form(),
    session: Session = Depends(get_session)
):
    user_id = request.session.get('user_id')

    if user_id is None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    if (
        current_password == ''
        or new_password == ''
        or new_password != new_password_confirm
    ):
        return RedirectResponse(
            url='/mypage/profile',
            status_code=303
        )

    sql_password_check = text('''
        select user_password
        from users
        where user_id = :user_id
    ''')

    result_password = session.execute(
        sql_password_check,
        {
            'user_id': user_id
        }
    )

    password_data = (
        result_password
        .mappings()
        .fetchone()
    )

    if (
        password_data is None
        or password_data['user_password']
            != current_password
    ):
        return RedirectResponse(
            url='/mypage/profile?password_result=wrong',
            status_code=303
        )

    sql_password_update = text('''
        update users
        set user_password = :new_password
        where user_id = :user_id
    ''')

    session.execute(
        sql_password_update,
        {
            'new_password': new_password,
            'user_id': user_id
        }
    )

    session.commit()

    return RedirectResponse(
        url='/mypage/profile?password_result=success',
        status_code=303
    )

@app.get('/mypage/reservations')
def mypageReservations(request: Request, session: Session = Depends(get_session)) :
    print('''
    ========================================
    /mypage/reservations : 마이페이지 예약 관리 실행
    ========================================
    ''')

    user_id = request.session.get('user_id')

    sql_mypage_reservation = text('''
        select * 
        from reservation as res
        join product as pr
            on res.product_id = pr.product_id
        join users as us
            on res.user_id = us.user_id
        join reservation_status as stat 
            on res.reservation_status_id  = stat.reservation_status_id
        where res.user_id = :user_id
        order by res.product_id, res.reservation_date, res.reservation_id;        
    ''')

    result_mypage_reservation = session.execute(sql_mypage_reservation, {
        'user_id' : user_id
    })

    reservationList = result_mypage_reservation.mappings().fetchall()

    # print(' reservationList : ' , reservationList)

    return templates.TemplateResponse(request, 'mypage-reservations.html', {
        'reservationList' : reservationList
    })

@app.post('/mypage/reservation/cancel')
def mypageReservationCancle(
    request: Request,
    reservation_id: int = Form(), 
    session: Session = Depends(get_session)) :
    print('''
    ========================================
    /mypage/reservation/cancel : 마이페이지 예약 취소 실행
    ========================================
    ''')

    user_id = request.session.get('user_id')

    print('reservation_id 확인용 : ', reservation_id)
    print('user_id 확인용 : ', user_id)

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    sql_reservation_delete = text('''
        delete from reservation
        where user_id = :user_id and reservation_id = :reservation_id
    ''')

    session.execute(sql_reservation_delete, {
        'user_id' : user_id,
        'reservation_id' : reservation_id
    })
    session.commit()

    return RedirectResponse(
        url='/mypage/reservations',
        status_code=303
    )  

@app.post('/mypage/reservation/turn')
def mypageReservationTurn(
    request: Request,
    reservation_id:int,
    session: Session = Depends(get_session)):
    print('''
    ========================================
    /mypage/reservation/turn : 마이페이지 우선순위 확인 실행
    ========================================
    ''')
    user_id = request.session.get('user_id')
    print(reservation_id)
    print(user_id)

    sql_reservation = text('''
        select reservation_id, product_id
        from reservation
        where reservation_id = :reservation_id
          and user_id = :user_id
    ''')

    reservation_result = session.execute(sql_reservation, {
        'reservation_id': reservation_id,
        'user_id': user_id
    })

    reservation = reservation_result.mappings().fetchone()

    if reservation == None:
        return {
            'result': '예약정보를 찾을 수 없습니다.'
        }

    sql_reservation_turn = text('''
        select count(*) as reservation_turn from reservation 
        where product_id = :product_id 
        and reservation_status_id = 3
        and reservation_id <= :reservation_id
    ''')

    result_reservation_turn = session.execute(sql_reservation_turn, {
        'user_id' : user_id,
        'product_id': reservation['product_id'],
        'reservation_id': reservation['reservation_id']
    })

    reservation_turn = result_reservation_turn.mappings().fetchone()

    return {
        'result' : '성공',
        'reservation_count' : reservation_turn['reservation_turn']
    }

# 사용 없는 코드 정리본
"""
사용 없는 코드 정리

# 사용없음 정리
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

#     return {
#         'product_list' : product_list,

#     }

# @app.get('/products/page/{page}')
# def productsPage(request: Request, page: int, session: Session = Depends(get_session)):
#     print('page : ', page)

#     sql = text('''
#         select * from product
#         limit :page_view, 8
#     ''')

#     result = session.execute(sql, {
#         'page_view' : (page * 8) - 8
#     })
#     product_page_list = result.mappings().fetchall()
#     print(product_page_list)

#     sql_all = text('''
#         select * from product        
#     ''')
#     result_all = session.execute(sql_all)
#     product_list = result_all.mappings().fetchall()

#     product_count = len(product_list)

#     total_page = int(product_count / 8)

#     if product_count % 8 != 0 :
#         total_page += 1

#     return templates.TemplateResponse(request, 'products.html', {
#         'product_list' : product_page_list,
#         'product_count' : product_count,
#         'total_page' : total_page,
#         'page' : page,
#         'category_id' : 0,
#         'keyword' : ''
#     })

# @app.get('/product/category/{category_id}')
# def productsCategory(request: Request, category_id:int, session: Session = Depends(get_session)):
#     sql = text('''
#         select * from product
#         where category_id = :category_id
#         order by product_view_count desc
#     ''')

#     result = session.execute(sql, {
#         'category_id' : category_id
#     })
#     product_category_list = result.mappings().fetchall()
#     # print('product_category_list', product_category_list)

#     return templates.TemplateResponse(request, 'products.html', {
#         'product_list' : product_category_list,
#         'product_count' : len(product_category_list),
#         'category_id' : category_id
#     })

# @app.get('/product/search')
# def productSearch(request: Request, keyword: str, session: Session = Depends(get_session)):
#     # print('keyword', keyword)

#     sql_search = text('''
#         select * from product
#         where product_name like :keyword
#         order by product_view_count desc
#     ''')
    
#     result = session.execute(sql_search, {
#         'keyword' : '%' + keyword + '%'
#     }) 
#     product_search_list = result.mappings().fetchall()

#     return templates.TemplateResponse(request, 'products.html', {
#         'product_list' : product_search_list,
#         'product_count' : len(product_search_list),
#         'category_id' : 0,
#         'keyword' : keyword
#     })

# @app.get('/product/detail/{product_id}')
# def productsDetail(request: Request, product_id:int, reservation: str = None, session: Session = Depends(get_session)) :
# print(request.session.get('user_name')[0])
# print(len(request.session.get('user_name')[1:]))

# aster = ''
# for i in range(len(request.session.get('user_name')[1:])) :
#     # print('*')
#     aster += '*' 
#     user_name = request.session.get('user_name')[0]
#     aster_name = user_name + aster
#     print(aster_name)

# for i in range(len(request.session.get('user_id')[3:])-1) :
#     aster += '*'
#     user_id = request.session.get('user_id')[:2]
#     print(user_id)
#     aster_id = user_id + aster
#     print(aster_id)

# @app.post('/product/reservation')
# def productReservation (
    # print('reservation_quantity : ', reservation_quantity)
    # nowAfter = now + timedelta(days=1)
    # reservationExpiration = nowAfter.strftime('%Y-%m-%d %H:%M:%S')

    # print('현재시간 : ', reservationDate)
    # print('24시간뒤 : ', reservationExpiration)
    # sql_stock_chk = text('''
    #     select * from product
    #     where product_id = :product_id
    # ''')
    # result_stock = session.execute(sql_stock_chk, {
    #     'product_id' : product_id
    # })
    # result_stock_list = result_stock.mappings().fetchone()
    # print('result_stock_list : ', result_stock_list)

    # if reservation_quantity > result_stock_list['product_reservation_stock'] :
    #     return RedirectResponse(
    #         url=f'/product/detail/{product_id}?reservation=failed',
    #         status_code=303
    #     )
    # session.execute(sql_reservation, {
    #     'reservation_expiration' : reservationExpiration 
    # })
    # sql_sale_stock_minus = text('''
    #     update product
    #     set product_reservation_stock = product_reservation_stock - :reservation_quantity
    #     where product_id = :product_id
    # ''')

    # session.execute(sql_sale_stock_minus, {
    #     'reservation_quantity' : reservation_quantity,
    #     'product_id' : product_id
    # })
    # session.commit()

# @app.post('/cart/deleteSelect')
# def cartDeleteSelect(
#     request: Request,
#     deleteSelectList: list[str],
#     session: Session = Depends(get_session)):

#     user_id = request.session.get('user_id')

#     print(deleteSelectList)
#     print(tuple(deleteSelectList))
#     test = "''".join(deleteSelectList)
#     test2 = str(tuple(deleteSelectList))
#     print('tuplelen' ,len(tuple(deleteSelectList)))
#     print(test)
#     print(test2.replace(',', ''))

    # test3 = ''
    # test3_front = ''

    # # for deleteSelect in deleteSelectList :
    # #     print(deleteSelect)
    # #     print(len(deleteSelectList))
    # #     print(deleteSelectList.index(deleteSelect))

    # #     if deleteSelectList.index(deleteSelect) == len(deleteSelectList) -1 :
    # #         test3_front += f'({deleteSelect})'
    # #     else :
    # #         test3 = f'{test3_front} {deleteSelect}' 

    # #     # if len(deleteSelectList) == 1 :
    # #     #     test3 += f'{deleteSelect}'
    # #     # else :
    # #     #     test3 += f'{deleteSelect},'
            
    # print('test3_front : ', test3_front)
    # print('test3 : ', test3)

    # sql_test = text('''
    #     select * from cart
    #     where user_id = :user_id
    #     in 
    # '''+test2)

    # test_result = session.execute(sql_test, {
    #     'user_id' : user_id
    # })

    # result = test_result.mappings().fetchall()

    # print(result)

    # print(deleteSelectList)
    # print(tuple(deleteSelectList))
    # test = "''".join(deleteSelectList)
    # test2 = str(tuple(deleteSelectList))
    # print('tuplelen' ,len(tuple(deleteSelectList)))
    # print(test)
    # print(test2.replace(',', ''))
    # delete_list = ''
    # if len(tuple(deleteSelectList)) == 1 :
    #     delete_list = str(tuple(deleteSelectList)).replace(',', '')
    # else :
    #     delete_list = str(tuple(deleteSelectList))

    # print(delete_list)

    # sql_test = text('''
    #     select * from cart
    #     where user_id = :user_id
    #     in 
    # '''+delete_list)

    # test_result = session.execute(sql_test, {
    #     'user_id' : user_id
    # })

    # result = test_result.mappings().fetchall()

    # print('내가결과에요 : ', result)

# @app.post('/checkout/card')
# def checkOutCard(
#     request:Request,
#     order_name:str = Form(),
#     order_phone:str = Form(),
#     order_addr:str = Form(),
#     order_addr_detail:str = Form(),
#     payment_method:str = Form(),
#     session: Session = Depends(get_session)):
#     if checkout_type == 'cart':
#         cartList = ''

#         for cartIndex in cartBuyList:
#             cartList += str(cartIndex) + ','

#         cartList = cartList[:-1]

#         sql_checkout_cart = text(f'''
#             select
#                 ca.cart_id,
#                 ca.product_quantity,
#                 pr.product_id,
#                 pr.product_price,
#                 pr.product_sale_stock,
#                 pr.product_active
#             from cart as ca
#             join product as pr
#                 on ca.product_id = pr.product_id
#             where ca.user_id = :user_id
#             and ca.cart_id in ({cartList})
#         ''')

#         result_checkout_cart = session.execute(sql_checkout_cart, {
#             'user_id': user_id
#         })

#         checkout_cart_list = result_checkout_cart.mappings().fetchall()

#         if len(checkout_cart_list) != len(cartBuyList):
#             return RedirectResponse(
#                 url='/cart',
#                 status_code=303
#             )

#     if checkout_type == 'direct' or checkout_type == 'reservation':
#         sql_checkout_stock = text('''
#             select * from product
#             where product_id = :product_id
#         ''')

#         result_checkout_stock = session.execute(sql_checkout_stock, {
#             'product_id': product_id
#         })

#         checkout_stock = result_checkout_stock.mappings().fetchone()

#         if checkout_stock == None:
#             return RedirectResponse(
#                 url='/products',
#                 status_code=303
#             )

#         if checkout_stock['product_active'] != 1:
#             return RedirectResponse(
#                 url='/products',
#                 status_code=303
#             )

#         if buy_quantity < 1:
#             return RedirectResponse(
#                 url=f'/product/detail/{product_id}',
#                 status_code=303
#             )
    
#     result_checkout_stock = session.execute(sql_checkout_stock, {
#         'product_id' : product_id
#     })

#     checkout_stock = result_checkout_stock.mappings().fetchone()
#     print(checkout_stock)

#     # 검증구간

    
#     if checkout_stock == None:
#         return RedirectResponse(
#             url='/products',
#             status_code=303
#         )
    
#     if checkout_stock['product_active'] != 1 :
#         return RedirectResponse(
#                 url='/products',
#                 status_code=303
#             )

#     if buy_quantity < 1 :
#         return RedirectResponse(
#             url=f'/product/detail/{product_id}',
#             status_code=303
#         )
# 바로 구매 또는 예약 구매 상품 조회
"""

if __name__ == '__main__' :
    import uvicorn
    uvicorn.run('api:app', port=8000, reload=True, host="0.0.0.0")