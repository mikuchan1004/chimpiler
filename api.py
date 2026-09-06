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
    return f'{ int(value) :,}'
templates.env.filters['price'] = price

# print(random.randint(1,10))

@app.get('/')
def login(request: Request, session: Session = Depends(get_session)) :
    print('/ 메인페이지')

    # 전체 상품 로드구간
    sql = text('''
        select * from product
    ''')

    result = session.execute(sql) 
    product_list_main = result.mappings().fetchall()
    print(product_list_main)

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
    print('product_view_main', product_view_main)

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
def random_product(session: Session = Depends(get_session)):

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

@app.get('/view_product')
def view_product():
    pass

@app.get('/products')
def login(request: Request, session: Session = Depends(get_session)) :

    sql = text('''
        select * from product
        order by product_view_count desc
    ''')

    result = session.execute(sql) 
    product_list = result.mappings().fetchall()

    sql_count = text('''
        select count(*) from product
    ''')

    result_count = session.execute(sql_count) 
    product_count = result_count.mappings().fetchall()

    # print(product_count[0]['count(*)'])

    return templates.TemplateResponse(request, 'products.html', {
        'product_list' : product_list,
        'product_count' : product_count[0]['count(*)']
    })

@app.get('/products/align')
def productsAlign(value: str, session: Session = Depends(get_session)):
    if value == 'align_view' :
        sql = text('''
            select * from product
            order by product_view_count desc
        ''')

    elif value == 'align_price_low' :
        sql = text('''
            select * from product
            order by product_price
        ''')

    elif value == 'align_price_high' :
        sql = text('''
            select * from product
            order by product_price desc
        ''')

    elif value == 'align_name' :
        sql = text('''
            select * from product
            order by product_name
        ''')

    result = session.execute(sql) 
    product_list = result.mappings().fetchall()

    return {
        'product_list' : product_list,
    }


@app.get('/product/detail/{product_id}')
def login(request: Request, product_id:int, session: Session = Depends(get_session)) :

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
def login(request: Request) :
    return templates.TemplateResponse(request, 'cart.html')

# 레이아웃 페이지 이동용_관리자페이지
@app.get('/admin')
def login(request: Request) :
    return templates.TemplateResponse(request, 'admin-dashboard.html')

@app.get('/admin/inquiries')
def login(request: Request) :
    return templates.TemplateResponse(request, 'admin-inquiries.html')

@app.get('/admin/orders')
def login(request: Request) :
    return templates.TemplateResponse(request, 'admin-orders.html')

@app.get('/admin/products')
def login(request: Request) :
    return templates.TemplateResponse(request, 'admin-products.html')

@app.get('/admin/reservations')
def login(request: Request) :
    return templates.TemplateResponse(request, 'admin-reservations.html')

@app.get('/admin/users')
def login(request: Request) :
    return templates.TemplateResponse(request, 'admin-users.html')

# 레이아웃 페이지 이동용_AI건강체크
@app.get('/ai-health')
def login(request: Request) :
    return templates.TemplateResponse(request, 'ai-health.html')

# 레이아웃 페이지 이동용_주문서작성
@app.get('/checkout')
def login(request: Request) :
    return templates.TemplateResponse(request, 'checkout.html')

# 레이아웃 페이지 이동용_커뮤니티
@app.get('/notice')
def login(request: Request) :
    return templates.TemplateResponse(request, 'notice.html')

@app.get('/faq')
def login(request: Request) :
    return templates.TemplateResponse(request, 'faq.html')

@app.get('/inquiry-write')
def login(request: Request) :
    return templates.TemplateResponse(request, 'inquiry-write.html')

# 레이아웃 페이지 이동용_로그인/회원가입
@app.get('/login')
def login(request: Request) :
    return templates.TemplateResponse(request, 'login.html')

@app.get('/signup')
def login(request: Request) :
    return templates.TemplateResponse(request, 'signup.html')

@app.get('/terms')
def login(request: Request) :
    return templates.TemplateResponse(request, 'terms.html')

# 레이아웃 페이지 이동용_마이페이지
@app.get('/mypage')
def login(request: Request) :
    return templates.TemplateResponse(request, 'mypage-dashboard.html')

@app.get('/mypage/inquiries')
def login(request: Request) :
    return templates.TemplateResponse(request, 'mypage-inquiries.html')

@app.get('/mypage/orders')
def login(request: Request) :
    return templates.TemplateResponse(request, 'mypage-orders.html')

@app.get('/mypage/profile')
def login(request: Request) :
    return templates.TemplateResponse(request, 'mypage-profile.html')

@app.get('/mypage/reservations')
def login(request: Request) :
    return templates.TemplateResponse(request, 'mypage-reservations.html')


if __name__ == '__main__' :
    import uvicorn
    uvicorn.run('api:app', port=8000, reload=True, host="0.0.0.0")