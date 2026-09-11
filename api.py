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

# 레이아웃 페이지 이동용_관리자페이지
@app.get('/admin')
def admin(request: Request) :
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

# 레이아웃 페이지 이동용_AI건강체크
@app.get('/ai-health')
def adminAihealth(request: Request) :
    print('''
    ========================================
    /ai-health : AI 건강 체크 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'ai-health.html')

# 레이아웃 페이지 이동용_주문서작성
@app.get('/checkout')
def checkout(request: Request, session: Session = Depends(get_session)) :
    print('''
    ========================================
    /checkout : 주문서 작성 실행
    ========================================
    ''')
    user_id = request.session.get('user_id')
    product_id = request.session.get('checkout_product_id')
    buy_quantity = request.session.get('checkout_quantity')

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    if product_id == None or buy_quantity == None:
        return RedirectResponse(
            url='/products',
            status_code=303
        )

    print(user_id)
    print(product_id)
    print(buy_quantity)

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

    checkout_total_price = (
        checkout_product['product_price'] * buy_quantity
    )

    return templates.TemplateResponse(request, 'checkout.html', {
        'checkout_product': checkout_product,
        'buy_quantity': buy_quantity,
        'checkout_total_price': checkout_total_price,
        'checkout_user' : checkout_user
    })

@app.post('/checkout')
def checkoutBuy (request:Request, buy_quantity: int = Form(), product_id:int = Form(), session: Session = Depends(get_session)) :
    print('''
    ========================================
    /checkout : 상품 상세 바로구매 실행
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
    user_id = request.session.get('user_id')

    print('구매 시 PRID : ', product_id)
    print('구매 시 수량 : ', buy_quantity)
    print('구매 시 경로 : ', checkout_type)

    if user_id == None:
        return RedirectResponse(
            url='/login',
            status_code=303
        )

    if product_id == None or buy_quantity == None:
        return RedirectResponse(
            url='/products',
            status_code=303
        )

    sql_checkout_stock = text('''
        select * from product
        where product_id = :product_id
    ''')

    result_checkout_stock = session.execute(sql_checkout_stock, {
        'product_id' : product_id
    })

    checkout_stock = result_checkout_stock.mappings().fetchone()
    print(checkout_stock)

    # 검증구간

    
    if checkout_stock == None:
        return RedirectResponse(
            url='/products',
            status_code=303
        )
    
    if checkout_stock['product_active'] != 1 :
        return RedirectResponse(
                url='/products',
                status_code=303
            )

    if buy_quantity < 1 :
        return RedirectResponse(
            url=f'/product/detail/{product_id}',
            status_code=303
        )

    if checkout_stock['product_sale_stock'] < buy_quantity :
        return RedirectResponse(
            url=f'/product/detail/{product_id}',
            status_code=303
        )

    now = datetime.now()
    checkoutDate = now.strftime('%Y-%m-%d %H:%M:%S')

    checkout_total_price = checkout_stock['product_price'] * buy_quantity

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

    session.execute(sql_orders, {
        'user_id' : user_id, 
        'order_status_id' : 1, 
        'order_name' : order_name, 
        'order_addr' : order_addr + ' ' + order_addr_detail, 
        'order_phone' : order_phone, 
        'product_id' : product_id, 
        'order_quantity' : buy_quantity, 
        'order_sheet_id' : checkout_sheet_id, 
        'order_price' : checkout_stock['product_price']
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

    sql_stock_update = text('''
        update product
        set product_sale_stock = product_sale_stock - :order_quantity
        where product_id = :product_id and product_sale_stock >= :order_quantity and product_active = 1
    ''')

    result_stock_update = session.execute(sql_stock_update, {
        'order_quantity' : buy_quantity,
        'product_id' : product_id
    })

    if result_stock_update.rowcount == 0:
        session.rollback()

        return RedirectResponse(
            url=f'/product/detail/{product_id}',
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

    session.commit()

    request.session.pop('checkout_product_id', None)
    request.session.pop('checkout_quantity', None)
    request.session.pop('checkout_type', None)

    return RedirectResponse(
        url=f'/payment/result?order_sheet_id={checkout_sheet_id}',
        status_code=303
    )

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

# 레이아웃 페이지 이동용_커뮤니티
@app.get('/notice')
def commNotice(request: Request) :
    print('''
    ========================================
    /notice : 커뮤니티 공지사항 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'notice.html')

@app.get('/faq')
def commFaq(request: Request) :
    print('''
    ========================================
    /faq : 커뮤니티 자주 묻는 질문 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'faq.html')

@app.get('/inquiry-write')
def commInquirywrite(request: Request) :
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
    return templates.TemplateResponse(request, 'signup.html')

@app.get('/terms')
def terms(request: Request) :
    print('''
    ========================================
    /terms : 이용약관 페이지 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'terms.html')

# 레이아웃 페이지 이동용_마이페이지
@app.get('/mypage')
def mypage(request: Request) :
    print('''
    ========================================
    /mypage : 마이페이지 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'mypage-dashboard.html')

@app.get('/mypage/inquiries')
def mypageInquiries(request: Request) :
    print('''
    ========================================
    /mypage/inquiries : 마이페이지 일대일 문의 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'mypage-inquiries.html')

@app.get('/mypage/orders')
def mypageOrders(request: Request) :
    print('''
    ========================================
    /mypage/orders : 마이페이지 주문 관리 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'mypage-orders.html')

@app.get('/mypage/profile')
def mypageProfile(request: Request) :
    print('''
    ========================================
    /mypage/profile : 마이페이지 회원 정보 실행
    ========================================
    ''')
    return templates.TemplateResponse(request, 'mypage-profile.html')

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

    print(' reservationList : ' , reservationList)

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


if __name__ == '__main__' :
    import uvicorn
    uvicorn.run('api:app', port=8000, reload=True, host="0.0.0.0")