"""FastAPI Application - REST API for E-Commerce"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from .models import (
    init_db, get_session, get_engine,
    User, Product, CartItem, Order, OrderItem
)

app = FastAPI(
    title="SmartTest E-Commerce API",
    description="API for AI-powered testing demo",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = init_db()

def get_db():
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str
    image_url: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    category: str
    image_url: Optional[str]
    
    class Config:
        from_attributes = True

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class OrderCreate(BaseModel):
    user_id: int

# Routes
@app.get("/")
def read_root():
    return {
        "message": "SmartTest E-Commerce API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/products", response_model=List[ProductResponse])
def get_products(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    return query.offset(skip).limit(limit).all()

@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/api/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/api/cart/{user_id}")
def get_cart(user_id: int, db: Session = Depends(get_db)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    
    result = []
    total = 0
    
    for item in cart_items:
        product = item.product
        subtotal = product.price * item.quantity
        total += subtotal
        
        result.append({
            "id": item.id,
            "product_id": product.id,
            "product_name": product.name,
            "product_price": product.price,
            "quantity": item.quantity,
            "subtotal": subtotal,
            "image_url": product.image_url
        })
    
    return {"items": result, "total": total, "item_count": len(result)}

@app.post("/api/cart")
def add_to_cart(item: CartItemCreate, user_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    existing = db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == item.product_id
    ).first()
    
    if existing:
        existing.quantity += item.quantity
    else:
        new_item = CartItem(
            user_id=user_id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(new_item)
    
    db.commit()
    return {"message": "Item added to cart"}

@app.delete("/api/cart/{item_id}")
def remove_from_cart(item_id: int, db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Item removed from cart"}

@app.post("/api/orders")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == order.user_id).all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    new_order = Order(
        user_id=order.user_id,
        status="pending",
        total_amount=total
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.product.price
        )
        db.add(order_item)
    
    for item in cart_items:
        db.delete(item)
    
    db.commit()
    
    return {
        "message": "Order created successfully",
        "order_id": new_order.id,
        "total": total,
        "status": "pending"
    }

@app.get("/api/orders/{user_id}")
def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    
    result = []
    for order in orders:
        items = [{
            "product_name": item.product.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price
        } for item in order.items]
        
        result.append({
            "id": order.id,
            "status": order.status,
            "total": order.total_amount,
            "created_at": order.created_at.isoformat(),
            "items": items
        })
    
    return result

@app.post("/api/seed")
def seed_data(db: Session = Depends(get_db)):
    """Add sample products to the database."""
    sample_products = [
        Product(
            name="Wireless Headphones",
            description="Premium noise-canceling headphones",
            price=299.99,
            stock=50,
            category="Electronics",
            image_url="https://via.placeholder.com/300x200?text=Headphones"
        ),
        Product(
            name="Smart Watch",
            description="Fitness tracking smartwatch",
            price=199.99,
            stock=30,
            category="Electronics",
            image_url="https://via.placeholder.com/300x200?text=SmartWatch"
        ),
        Product(
            name="Running Shoes",
            description="Professional running shoes",
            price=129.99,
            stock=100,
            category="Sports",
            image_url="https://via.placeholder.com/300x200?text=Shoes"
        ),
        Product(
            name="Coffee Maker",
            description="Automatic espresso machine",
            price=399.99,
            stock=20,
            category="Home",
            image_url="https://via.placeholder.com/300x200?text=CoffeeMaker"
        ),
        Product(
            name="Yoga Mat",
            description="Non-slip exercise mat",
            price=29.99,
            stock=200,
            category="Sports",
            image_url="https://via.placeholder.com/300x200?text=YogaMat"
        ),
        Product(
            name="Desk Lamp",
            description="LED desk lamp with wireless charging",
            price=79.99,
            stock=40,
            category="Home",
            image_url="https://via.placeholder.com/300x200?text=Lamp"
        ),
    ]
    
    for product in sample_products:
        db.add(product)
    
    db.commit()
    return {"message": f"Added {len(sample_products)} sample products"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
