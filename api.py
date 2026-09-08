from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy import text, URL

from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from starlette.middleware.sessions import SessionMiddleware

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
        session.commit() 

# 원 단위 세 자리씩 끊어서 ',' 찍어주는 함수
def price(value) :
    return f'{int(value):,}'
templates.env.filters['price'] = price

# print(random.randint(1,10))

@app.get('/chat')
def chatBot(request: Request, answer:str, session: Session = Depends(get_session)) :
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
    print('/ 메인페이지')

    print(request.session.get('isLogin'))
    print(request.session.get('id'))

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
def productsDetail(request: Request, product_id:int, session: Session = Depends(get_session)) :

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

    # print(product_list[0]['product_price'], type(product_list[0]['product_price']))

    return templates.TemplateResponse(request, 'product-detail.html', {
        'product_list' : product_list,
        'review_list' : review_list,
        'rating_avg' : rating_avg,
        'review_count' : rating['review_count']
    })

@app.post('/product/review')
def productReview (
    product_id:int = Form(), 
    review_score:int = Form(), 
    review_content:str = Form(),
    user_id:str = Form(),
    session: Session = Depends(get_session)):

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

    return RedirectResponse(
        url=f'/product/detail/{product_id}',
        status_code=303
    )



@app.get('/cart')
def cart(request: Request) :
    return templates.TemplateResponse(request, 'cart.html')

# 레이아웃 페이지 이동용_관리자페이지
@app.get('/admin')
def admin(request: Request) :

    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-dashboard.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

@app.get('/error-404')
def error(request: Request):
    return templates.TemplateResponse(request, 'error-404.html')


@app.get('/admin/inquiries')
def adminInquiries(request: Request) :

    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-inquiries.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

@app.get('/admin/orders')
def adminOrders(request: Request) :
    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-orders.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

@app.get('/admin/products')
def adminProducts(request: Request) :
    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-products.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

@app.get('/admin/reservations')
def adminReservations(request: Request) :
    if request.session.get('user_id') == 'admin' :
        return templates.TemplateResponse(request, 'admin-reservations.html')
    else :
        return RedirectResponse(
            url='/error-404',
            status_code=303
        )

@app.get('/admin/users')
def adminUsers(request: Request) :
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
    return templates.TemplateResponse(request, 'ai-health.html')

# 레이아웃 페이지 이동용_주문서작성
@app.get('/checkout')
def checkout(request: Request) :
    return templates.TemplateResponse(request, 'checkout.html')

# 레이아웃 페이지 이동용_커뮤니티
@app.get('/notice')
def commNotice(request: Request) :
    return templates.TemplateResponse(request, 'notice.html')

@app.get('/faq')
def commFaq(request: Request) :
    return templates.TemplateResponse(request, 'faq.html')

@app.get('/inquiry-write')
def commInquirywrite(request: Request) :
    return templates.TemplateResponse(request, 'inquiry-write.html')

@app.get('/login')
def login_loading(request: Request):
    return templates.TemplateResponse(request, 'login.html')

# 레이아웃 페이지 이동용_로그인/회원가입
@app.post('/login')
def login(request: Request, user_id:str = Form(), user_password:str = Form(), session: Session = Depends(get_session)) :

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

            return RedirectResponse(
                url='/',
                status_code=303
            )

    return templates.TemplateResponse(request, 'login.html', {
        'login_error': '아이디 또는 비밀번호가 일치하지 않습니다.'
    })

    # print('@@@@@@@@@@@@@@@@@@@@@@@')
    # print('user_id', user_id)
    # print('user_password', user_password)
    # return templates.TemplateResponse(request, 'login.html')

@app.get('/logout')
def logout(request:Request):
    request.session.clear()

    return RedirectResponse(
        url='/',
        status_code=303
    )

@app.get('/signup')
def signup(request: Request) :
    return templates.TemplateResponse(request, 'signup.html')

@app.get('/terms')
def terms(request: Request) :
    return templates.TemplateResponse(request, 'terms.html')

# 레이아웃 페이지 이동용_마이페이지
@app.get('/mypage')
def mypage(request: Request) :
    return templates.TemplateResponse(request, 'mypage-dashboard.html')

@app.get('/mypage/inquiries')
def mypageInquiries(request: Request) :
    return templates.TemplateResponse(request, 'mypage-inquiries.html')

@app.get('/mypage/orders')
def mypageOrders(request: Request) :
    return templates.TemplateResponse(request, 'mypage-orders.html')

@app.get('/mypage/profile')
def mypageProfile(request: Request) :
    return templates.TemplateResponse(request, 'mypage-profile.html')

@app.get('/mypage/reservations')
def mypageReservations(request: Request) :
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

if __name__ == '__main__' :
    import uvicorn
    uvicorn.run('api:app', port=8000, reload=True, host="0.0.0.0")