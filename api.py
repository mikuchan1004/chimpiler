<<<<<<< HEAD
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
=======
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

>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username="chimpiler_team",
    password="chimpiler!@#",
    host="192.168.0.65",
    port=3306,
    database="chimpiler",
)
<<<<<<< HEAD

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

@app.get('/')
def main_loading(request: Request, session: Session = Depends(get_session)):

    user_name = None

    user_id = request.cookies.get('user_id')

    if user_id:
        user = session.get(Users, user_id)

        if user:
            user_name = user.user_name

    return templates.TemplateResponse(
        request,
        'main.html',
        context={
            'user_name': user_name
        }
    )


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
            # response=templates.TemplateResponse( 
            #             request=alist,
            #             # name='main.html',
            #             name='templates/layout.html',
            #             context={
            #                 'user_name':users['user_name']
            #             }

            #             )
            response = RedirectResponse("/", status_code=303)

            response.set_cookie(
                key='log_chk',
                value='chk',
                max_age=60 * 60,
                path='/'
            )

            response.set_cookie(
                key='user_id',
                value=user_id,
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
=======
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session :
        yield session
        session.commit() 

def price(value) :
    return f'{int(value):,}'
templates.env.filters['price'] = price
# print(random.randint(1,10))

@app.get('/chat')
def chatBot(answer:str, session: Session = Depends(get_session)) :
    print('''
    ========================================
    /chat : 챗봇 실행
    ========================================
    ''')
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
def randomProduct(session: Session = Depends(get_session)):
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
    product_id:int = Form(), 
    review_score:int = Form(), 
    review_content:str = Form(),
    user_id:str = Form(),
    session: Session = Depends(get_session)):
    print('''
    ========================================
    /product/review : 리뷰 작성 실행
    ========================================
    ''')
    print(product_id)
    print(review_score)
    print(review_content)
    print(user_id)

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

@app.get('/cart')
def cart(
    request: Request,
    user_id: str,
    session: Session = Depends(get_session)) :
    print('''
    ========================================
    /cart : 장바구니 실행
    ========================================
    ''')

    print('장바구니에 담긴 ID : ',user_id)

    sql_cart = text('''
        select *, 
        ca.product_quantity as cart_quantity, 
        sum(ca.product_quantity) * pr.product_price as cart_price 
        from cart as ca
        join users as us on (ca.user_id = us.user_id)
        join product as pr on (ca.product_id = pr.product_id)
        where ca.user_id = :user_id
        group by pr.product_name
    ''')

    result_cart = session.execute(sql_cart, {
        'user_id' : user_id
    })
    cart_list = result_cart.mappings().fetchall()

    return templates.TemplateResponse(request, 'cart.html', {
        'cart_list' : cart_list
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
        url=f'/cart?user_id={user_id}',
        status_code=303
    )
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2

# 레이아웃 페이지 이동용_관리자페이지
@app.get('/admin')
def admin(request: Request) :
<<<<<<< HEAD
    return templates.TemplateResponse(request, 'admin-dashboard.html')

@app.get('/admin/inquiries')
def adminInquiries(request: Request) :
    return templates.TemplateResponse(request, 'admin-inquiries.html')

@app.get('/admin/orders')
def adminOrders(request: Request) :
    return templates.TemplateResponse(request, 'admin-orders.html')

@app.get('/admin/products')
def adminProducts(request: Request) :
    return templates.TemplateResponse(request, 'admin-products.html')

@app.get('/admin/reservations')
def adminReservations(request: Request) :
    return templates.TemplateResponse(request, 'admin-reservations.html')

@app.get('/admin/users')
def adminUsers(request: Request) :
    return templates.TemplateResponse(request, 'admin-users.html')
=======
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
def error(request: Request):
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
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2

# 레이아웃 페이지 이동용_AI건강체크
@app.get('/ai-health')
def adminAihealth(request: Request) :
<<<<<<< HEAD
=======
    print('''
    ========================================
    /ai-health : AI 건강 체크 실행
    ========================================
    ''')
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
    return templates.TemplateResponse(request, 'ai-health.html')

# 레이아웃 페이지 이동용_주문서작성
@app.get('/checkout')
def checkout(request: Request) :
<<<<<<< HEAD
=======
    print('''
    ========================================
    /checkout : 주문서 작성 실행
    ========================================
    ''')
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
    return templates.TemplateResponse(request, 'checkout.html')

# 레이아웃 페이지 이동용_커뮤니티
@app.get('/notice')
def commNotice(request: Request) :
<<<<<<< HEAD
=======
    print('''
    ========================================
    /notice : 커뮤니티 공지사항 실행
    ========================================
    ''')
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
    return templates.TemplateResponse(request, 'notice.html')

@app.get('/faq')
def commFaq(request: Request) :
<<<<<<< HEAD
=======
    print('''
    ========================================
    /faq : 커뮤니티 자주 묻는 질문 실행
    ========================================
    ''')
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
    return templates.TemplateResponse(request, 'faq.html')

@app.get('/inquiry-write')
def commInquirywrite(request: Request) :
<<<<<<< HEAD
    return templates.TemplateResponse(request, 'inquiry-write.html')

# 레이아웃 페이지 이동용_로그인/회원가입
@app.get('/login')
def login(request: Request) :
    return templates.TemplateResponse(request, 'login.html')

@app.get('/signup')
def signup(request: Request) :
=======
    print('''
    ========================================
    /inquiry-write : 커뮤니티 일대일 문의 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'inquiry-write.html')

@app.get('/login')
def login_loading(request: Request):
    print('''
    ========================================
    /login : 로그인 페이지 로딩
    ========================================
    ''')
    return templates.TemplateResponse(request, 'login.html')

# 레이아웃 페이지 이동용_로그인/회원가입
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
def signup(request: Request) :
    print('''
    ========================================
    /signup : 회원가입 페이지 실행
    ========================================
    ''')
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
    return templates.TemplateResponse(request, 'signup.html')

@app.get('/terms')
def terms(request: Request) :
<<<<<<< HEAD
=======
    print('''
    ========================================
    /terms : 이용약관 페이지 실행
    ========================================
    ''')
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
    return templates.TemplateResponse(request, 'terms.html')

# 레이아웃 페이지 이동용_마이페이지
@app.get('/mypage')
def mypage(request: Request) :
<<<<<<< HEAD
=======
    print('''
    ========================================
    /mypage : 마이페이지 실행
    ========================================
    ''')
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
    return templates.TemplateResponse(request, 'mypage-dashboard.html')

@app.get('/mypage/inquiries')
def mypageInquiries(request: Request) :
<<<<<<< HEAD
=======
    print('''
    ========================================
    /mypage/inquiries : 마이페이지 일대일 문의 실행
    ========================================
    ''')
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
    return templates.TemplateResponse(request, 'mypage-inquiries.html')

@app.get('/mypage/orders')
def mypageOrders(request: Request) :
<<<<<<< HEAD
=======
    print('''
    ========================================
    /mypage/orders : 마이페이지 주문 관리 실행
    ========================================
    ''')
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
    return templates.TemplateResponse(request, 'mypage-orders.html')

@app.get('/mypage/profile')
def mypageProfile(request: Request) :
<<<<<<< HEAD
=======
    print('''
    ========================================
    /mypage/profile : 마이페이지 회원 정보 실행
    ========================================
    ''')
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
    return templates.TemplateResponse(request, 'mypage-profile.html')

@app.get('/mypage/reservations')
def mypageReservations(request: Request) :
<<<<<<< HEAD
    return templates.TemplateResponse(request, 'mypage-reservations.html')

@app.get('/products')
def adminProducts(request: Request) :
    return templates.TemplateResponse(request, 'products.html')




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
=======
    print('''
    ========================================
    /mypage/reservations : 마이페이지 예약 관리 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'mypage-reservations.html')


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

if __name__ == '__main__' :
    import uvicorn
    uvicorn.run('api:app', port=8000, reload=True, host="0.0.0.0")
>>>>>>> d9c1eea7a34c16c02350c107aac4abd0fa7ec1f2
