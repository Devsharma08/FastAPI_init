from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import database_model
from database import SessionLocal, engine, get_db
from model import Product


def initialize_database():
    database_model.Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(database_model.Product).first() is None:
            db.add_all(
                [
                    database_model.Product(
                        id=1,
                        name="car1",
                        desc="this is car1",
                        price=5000000.00,
                        rating=4.5,
                    ),
                    database_model.Product(
                        id=2,
                        name="car2",
                        desc="this is car2",
                        price=5064000.00,
                        rating=4.0,
                    ),
                    database_model.Product(
                        id=3,
                        name="car3",
                        desc="this is car3",
                        price=5024000.00,
                        rating=4.2,
                    ),
                ]
            )
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allowed_origins=["http://localhost:3000"],
    allowed_methods=["*"]
)


@app.get("/")
def healthy():
    return {"message": "server is healthy"}


@app.get("/products", response_model=list[Product])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(database_model.Product).all()


@app.get("/product/{id}", response_model=Product)
def get_product_by_id(id: int, db: Session = Depends(get_db)):
    product = db.query(database_model.Product).filter_by(id=id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/product", response_model=Product)
def add_product(
    id: int,
    name: str,
    desc: str,
    price: float,
    rating: float,
    db: Session = Depends(get_db),
):
    if db.query(database_model.Product).filter_by(id=id).first() is not None:
        raise HTTPException(status_code=409, detail="Product ID already exists")

    product = database_model.Product(
        id=id,
        name=name,
        desc=desc,
        price=price,
        rating=rating,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@app.put("/product/{id}", response_model=Product)
def update_product_by_id(
    id: int,
    name: str | None = None,
    desc: str | None = None,
    price: float | None = None,
    rating: float | None = None,
    db: Session = Depends(get_db),
):
    product = db.query(database_model.Product).filter_by(id=id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    updates = {
        "name": name,
        "desc": desc,
        "price": price,
        "rating": rating,
    }
    for field, value in updates.items():
        if value is not None:
            setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@app.delete("/product/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    product = db.query(database_model.Product).filter_by(id=id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": f"product {id} deleted successfully"}
