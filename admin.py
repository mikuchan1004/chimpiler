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
@app.get('/dashboard')
def dashboard(request: Request, session: Session = Depends(get_session)):
    print('/dashboard 실행')
    return templates.TemplateResponse(request, 'admin-dashboard.html')

# 메인 페이지 이동 
@app.get('/main')
def main (request:Request, session:Session = Depends(get_session)):
    print('/main 실행')
    return templates.TemplateResponse(request, 'main.html')
##########
# 페이지 이동 라우터 끝
##########

##########
# 상품/재고관리 CRUD
##########
# 상품 목록 이동 및 출력 
@app.get('/products')
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
        # -----------------------------------------------   
        # [이미지 파일 업로드 및 서버 저장 로직]  (주석은 Google Gemini가 남겨줬습니다.)
        # --------------------------------------------------
        image_path = ""
        # 1. 폼(Form)을 통해 실제 사진 파일이 첨부되어 들어왔는지 확인합니다.
        if product.product_image and product.product_image.filename:
            # 2. 서버의 'static/images/' 폴더 안에 저장될 파일의 전체 경로를 만듭니다.
            #  (예: static/images/cloth1.jpg)
            file_location = dir / product.product_image.filename
            # 3. 서버 컴퓨터의 디스크에 진짜 실물 파일로 쓰기(저장) 작업을 시작합니다.
            #'wb'는 바이너리(이미지/파일 데이터) 쓰기 모드로 파일을 연다는 뜻입니다.
            with file_location.open('wb') as buffer:
                # 4. 사용자가 업로드한 파일의 실제 데이터 Stream(.file)을 
                # 방금 열어둔 서버의 파일 공간(buffer)으로 쏙 복사해 넣습니다.
                shutil.copyfileobj(product.product_image.file, buffer)
           # 5. 파일 저장이 무사히 끝났으니, 데이터베이스(DB)의 product_image 컬럼에 
           # 문자열로 기록해 둘 웹 접근용 경로를 만듭니다. (예: /static/images/cloth1.jpg)
            image_path = f'/static/images/{product.product_image.filename}'
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
        session.execute(sql, {
            'product_brand' :product.product_brand,
            'product_name' : product.product_name,
            'product_detail' : product.product_detail,
            'product_image' : product.product_image,
            'product_price' : product.product_price,
            'product_sale_stock' : product.product_sale_stock,
            'product_reservation_stock' : product.product_reservation_stock,
            "category_id" : product.category_id
        })
        session.commit()
    except Exception as e :
        print(e)

    return RedirectResponse(url='/products', status_code=303)

# 상품 수정 
@app.post('/api/modify')
def  update_product(product : Product = Form(), session: Session = Depends(get_session)):
    print('/api/modify 실행' , product)
    try:
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
        session.execute(sql, {
            'product_id' : product.product_id,
            'product_brand' :product.product_brand,
            'product_name' : product.product_name,
            'product_detail' : product.product_detail,
            'product_image' : product.product_image,
            'product_price' : product.product_price,
            'product_sale_stock' : product.product_sale_stock,
            'product_reservation_stock' : product.product_reservation_stock,
            "category_id" : product.category_id
        })
        session.commit()

    except Exception as e :
        print(e)

    return RedirectResponse(url='/products', status_code=303)


#########
# uvicorn 서버 실행 
#########
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("admin:app", port=8085, reload=True, host="0.0.0.0")
    #########
    #  uvicorn  서버 실행 끝. 여기가 코드의 마지막입니다.
    #########