##########
# 필요한 모듈 호출 영역
##########
from sqlmodel import create_engine, Session
from fastapi import FastAPI, Depends, Request, Form, UploadFile
from fastapi.templating import Jinja2Templates         
from fastapi.responses import RedirectResponse        
from sqlalchemy import text, URL                         
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil

from DTO.ProductDTO import Product
# /static/images : 절대 경로로 하면 컴퓨터 최상위 루트부터 찾기 때문에 오류가 발생할 수 있으니 주의
dir = Path('static/images') 

app = FastAPI()  # FastAPI 웹 서버 인스턴스 생성
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
    with Session(engine) as session: 
        yield session     
        session.commit()   

##########
# 페이지 이동 라우터
##########
# 관리자 대시보드 페이지
@app.get('/admin')
def dashboard(request: Request, session: Session = Depends(get_session)):
    print('/admin 실행')
    return templates.TemplateResponse(request, 'admin-dashboard.html')

# 메인 페이지 이동 
@app.get('/')
def main (request:Request, session:Session = Depends(get_session)):
    print('/ 실행')
    return templates.TemplateResponse(request, 'main.html')
##########
# 페이지 이동 라우터 끝
##########

##########
# 상품/재고관리 CRUD
##########
# 상품 목록 이동 및 출력 
@app.get('/admin/products')
def product_list (request: Request, session: Session = Depends(get_session)) :
    print('상품 목록 출력')
    sql = text ('''
        select * from product
    ''')
    results = session.execute(sql).mappings().fetchall()

    return templates.TemplateResponse(request, 'admin-products.html', {
        'product_list' : results
    })

# 상품 추가
@app.post('/api/add')
def add_product(product : Product = Form(), session: Session = Depends(get_session)):
    print('/api/add 실행')
    try :
        # 첨부된 이미지 파일이 static/images 폴더에 실제로 저장
        filename = f'{product.product_image.filename}'
        image_path = dir / filename 
        with image_path.open('wb') as buffer :
            shutil.copyfileobj(product.product_image.file, buffer)
        db_image_path = f'/static/images/{filename}'
        #=========================================
        # model.dump()는 Pydantic 객체 안에 들어있는 데이터들을 파이썬의 dict(딕셔너리) 형태로 한 방에 
        # 짠! 하고 바꿔주는 아주 효과적인 메서드라고합니다. by Google Gemini
        #=========================================
        params = product.model.dump() 
        params['product_image'] = db_image_path
        sql = text ('''
            insert into product
            (
            product_brand, 
            product_name, 
            product_detail, 
            product_image, 
            product_price, 
            product_sale_stock,
            product_reservation_stock,
            category_id
            )
            values(
            :product_brand, 
            :product_name, 
            :product_detail, 
            :product_image, 
            :product_price,
            :product_sale_stock,
            :product_reservation_stock,
            :category_id
            )
        ''')
        session.execute(sql, params)
        session.commit()
    except Exception as e :
        print(e)

    return RedirectResponse(url='/admin/products', status_code=303)

# 상품 수정 
@app.post('/api/modify')
def  update_product(product : Product = Form(), session: Session = Depends(get_session)):
    print('/api/modify 실행' , product)
    try:
        filename = f'{product.product_image.filename}'
        image_path = dir / filename 
        with image_path.open('wb') as buffer :
            shutil.copyfileobj(product.product_image.file, buffer)
        db_image_path = f'/static/images/{filename}'
        params = product.model.dump() 
        params['product_image'] = db_image_path
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

# 상품 삭제 
@app.get('/api/delete/{product_id}')
def delete_product(product_id : int, session:Session = Depends(get_session)):
    print('/api/delete 실행', product_id)
    try:
        sql = text('''
            delete from product
            where product_id = :product_id
        ''')
        session.execute(sql,{'product_id' : product_id})
        session.commit()
    except Exception as e:
        print(e)

    return RedirectResponse(url='/admin/products', status_code=303)


#########
# uvicorn 서버 실행 
#########
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("admin:app", port=8085, reload=True, host="0.0.0.0")
    #########
    #  uvicorn  서버 실행 끝. 여기가 코드의 마지막입니다.
    #########