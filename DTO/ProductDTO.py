
from fastapi import UploadFile, File
from sqlmodel import SQLModel, Field      
from typing import Optional                  
from pydantic import field_validator   

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

    product_image : UploadFile = File(None)

    category_id : int = Field (
        foreign_key='category.category_id'
    )

    product_view_count : int = Field (
        default = 0
    )

    product_activate : int = Field (
        default = 1
    )

# =========================================================================
# [폼 데이터 파싱 처리기]
# HTML <form>에서 숫자 필드를 비워두고 전송하면 빈 문자열("")이 전송되는데,
# Pydantic이 이를 int/float로 형변환하려다 에러(ValidationError)를 일으키는 것을 방지
# =========================================================================
@field_validator('product_detail', 'product_image', mode='before')
@classmethod 
def empty_to_none(cls, value):
    # mode='before': 데이터 타입 검사 전(전처리 단계)에 가장 먼저 실행됨
        if value == '':
            return None  # 빈 문자열("")이 들어오면 None(NULL)으로 바꾸어 타입 에러 예방
        else:
             return value # 값이 채워져 있으면 그대로 넘겨줌