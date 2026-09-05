from fastapi import FastAPI


@app.get("/product")
def get_product(request: Request):
    products = session.exec(select(Product)).all()

    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "products": products
        }
    )

