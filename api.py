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

print(random.randint(1,10))

@app.get('/')
def login(request: Request, session: Session = Depends(get_session)) :

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

# @app.get('/products/{category}')
        

@app.get('/products/detail')
def login(request: Request) :
    return templates.TemplateResponse(request, 'product-detail.html')

@app.get('/cart')
def login(request: Request) :
    return templates.TemplateResponse(request, 'cart.html')


if __name__ == '__main__' :
    import uvicorn
    uvicorn.run('api:app', port=8000, reload=True, host="0.0.0.0")