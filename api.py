from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy import text, URL

from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import random


app = FastAPI()
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

    # print(product_list[0]['product_price'], type(product_list[0]['product_price']))

    return templates.TemplateResponse(request, 'product-detail.html', {
        'product_list' : product_list
    })

@app.get('/cart')
def cart(request: Request) :
    return templates.TemplateResponse(request, 'cart.html')

# 레이아웃 페이지 이동용_관리자페이지
@app.get('/admin')
def admin(request: Request) :
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

# 레이아웃 페이지 이동용_로그인/회원가입
@app.get('/login')
def login(request: Request) :
    return templates.TemplateResponse(request, 'login.html')

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