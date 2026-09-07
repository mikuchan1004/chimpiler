from fastapi import Form, UploadFile, File
from sqlmodel import SQLModel, Field      
from typing import Optional                  
from pydantic import field_validator   

# =========================================================================
# [상품 데이터 모델 (DTO)]
# 데이터베이스 Table 및 Form 전송 데이터의 규격을 정의하는 클래스
# =========================================================================
class Product(SQLModel):
    product_id : int | None = Field (
        default=None,
        primary_key=True
    )
    product_brand : str 

    product_name : str 

    product_price : int 

    product_sale_stock : int = Field (
        default = 0
    )

    product_reservation_stock : int = Field (
        default = 0
    )

    product_detail : Optional[str] = None

    category_id : int = Field (
        foreign_key='category.category_id'
    )

    product_view_count : int = Field (
        default = 0
    )

    product_activate : int = Field (
        default = 1
    )

    # =====================================================================
    # [💡 HTML Form 데이터 파싱용 클래스 메서드]
    # HTML <form>은 데이터를 객체가 아닌 낱개(Key-Value) 형태로 전달합니다.
    # FastAPI 라우터에서 Depends(Product.as_form) 형태로 호출하면,
    # 폼으로 수신된 낱개 항목들을 자동으로 읽어와 Product 객체로 묶어 생성해 줍니다.
    # by Google Gemini
    # =====================================================================
    @classmethod
    def as_form(
        cls,
        product_id: Optional[int] = Form(None),              # 수정 시에만 값이 들어오는 PK (기본값 None)
        product_brand: str = Form(...),                      # 필수 입력값
        product_name: str = Form(...),                       # 필수 입력값
        product_detail: Optional[str] = Form(None),          # 선택 입력값
        product_price: int = Form(...),                      # 필수 입력값
        product_sale_stock: int = Form(0),                   # 기본값 0
        product_reservation_stock: int = Form(0),            # 기본값 0
        category_id: int = Form(...)                         # 필수 입력값
    ):
        return cls(
            product_id=product_id,
            product_brand=product_brand,
            product_name=product_name,
            product_detail=product_detail,
            product_price=product_price,
            product_sale_stock=product_sale_stock,
            product_reservation_stock=product_reservation_stock,
            category_id=category_id
        )
    

# =========================================================================
# [폼 데이터 전처리 검증기]
# HTML <form>에서 입력란을 비워두고 제출하면 빈 문자열("")이 들어오는데,
# 이를 int/float나 None 타입으로 올바르게 변환하지 못해 발생하는 ValidationError 예방
# Note: DTO에 더 이상 존재하지 않는 'product_image'는 검증 대상 목록에서 제거했습니다.
# =========================================================================
@field_validator('product_detail', mode='before')
@classmethod 
def empty_to_none(cls, value):
    # mode='before': 데이터 타입 검사 전(전처리 단계)에 가장 먼저 실행됨
    if value == '':
        return None  # 빈 문자열("")이 들어오면 None(NULL)으로 바꾸어 타입 에러 예방
    else:
        return value # 값이 채워져 있으면 그대로 넘겨줌