# Step 1: Building the E-Commerce Application

> **Learning Time: 45 minutes**  
> **Goal: Create a real web app that we'll test with AI**

---

## 🎯 What You're Building

A complete e-commerce platform with:
- **Backend**: FastAPI REST API with authentication
- **Frontend**: React web app with product catalog
- **Database**: PostgreSQL for data persistence
- **Docker**: Easy infrastructure setup

## 📚 Why This Matters

**Interview Context:**
> "To demonstrate AI-powered testing, I built a realistic e-commerce application with user authentication, product catalog, shopping cart, and checkout flow. This gives the AI system real functionality to analyze and test."

**Key Learning:**
- Real-world applications have complex user flows
- Testing needs to cover authentication, state management, and payment flows
- Modern web apps use API + frontend architecture

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    E-COMMERCE APP                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │     FRONTEND         │      │      BACKEND         │    │
│  │    (React 18)        │◄────►│     (FastAPI)        │    │
│  │                      │ HTTP │                      │    │
│  │  ┌────────────────┐  │      │  ┌────────────────┐  │    │
│  │  │  Product List  │  │      │  │  /api/products │  │    │
│  │  └────────────────┘  │      │  └────────────────┘  │    │
│  │                      │      │                      │    │
│  │  ┌────────────────┐  │      │  ┌────────────────┐  │    │
│  │  │  Shopping Cart │  │      │  │  /api/cart     │  │    │
│  │  └────────────────┘  │      │  └────────────────┘  │    │
│  │                      │      │                      │    │
│  │  ┌────────────────┐  │      │  ┌────────────────┐  │    │
│  │  │  Checkout      │  │      │  │  /api/orders   │  │    │
│  │  └────────────────┘  │      │  └────────────────┘  │    │
│  │                      │      │                      │    │
│  │  ┌────────────────┐  │      │  ┌────────────────┐  │    │
│  │  │  User Login    │  │      │  │  /api/auth     │  │    │
│  │  └────────────────┘  │      │  └────────────────┘  │    │
│  └──────────────────────┘      └──────────┬───────────┘    │
│                                           │                 │
│                                           ▼                 │
│                              ┌──────────────────────┐      │
│                              │   DATABASE           │      │
│                              │   (PostgreSQL)       │      │
│                              │                      │      │
│                              │  • users table       │      │
│                              │  • products table    │      │
│                              │  • cart_items table  │      │
│                              │  • orders table      │      │
│                              └──────────────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Step-by-Step Implementation

### Step 1.1: Create Project Structure

**What you're doing:** Creating organized folder structure

**Why:** Professional projects need clear organization

```bash
cd smarttest-ai
mkdir -p ecommerce-app/{backend,frontend}
mkdir -p ecommerce-app/backend/{app,tests}
mkdir -p ecommerce-app/frontend/{src,public,tests}
```

### Step 1.2: Backend - FastAPI Setup

**File:** `ecommerce-app/backend/requirements.txt`

**What you're doing:** Defining Python dependencies

**Why:** FastAPI is modern, fast, and has automatic API documentation

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Environment
python-dotenv==1.0.0

# Testing
pytest==7.4.3
httpx==0.25.2
```

---

**File:** `ecommerce-app/backend/app/models.py`

**What you're doing:** Creating database models

**Why:** SQLAlchemy ORM maps Python classes to database tables

**Key Concepts:**
- **ORM (Object-Relational Mapping)**: Write Python, not SQL
- **Relationships**: Connect tables (user has many orders)
- **Migrations**: Track database schema changes

```python
"""
Database Models

This file defines the data structure for our e-commerce app.
Each class = one database table.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    """
    User model - stores authentication info.
    
    Learning: One-to-Many relationship
    One user can have many orders.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship: User has many orders
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")

class Product(Base):
    """
    Product model - items available for purchase.
    
    Learning: Simple entity with attributes
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    stock = Column(Integer, default=0)
    image_url = Column(String)
    category = Column(String, index=True)
    
    # Relationships
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

class CartItem(Base):
    """
    Shopping cart item - temporary hold on products.
    
    Learning: Junction table (many-to-many with attributes)
    Users <-> Products through CartItem
    """
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

class Order(Base):
    """
    Order - completed purchase.
    
    Learning: Status workflow (pending -> paid -> shipped)
    """
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")  # pending, paid, shipped, delivered
    total_amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    """
    Individual item within an order.
    
    Learning: Snapshots - stores price at time of purchase
    """
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    unit_price = Column(Float)  # Price at time of order
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

# Database setup helper
def get_engine():
    """Create database engine from environment variable."""
    database_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/ecommerce")
    return create_engine(database_url)

def init_db():
    """Create all tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine

def get_session(engine):
    """Get a database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
```

---

**File:** `ecommerce-app/backend/app/main.py`

**What you're doing:** Creating REST API endpoints

**Why:** REST APIs allow frontend to communicate with backend

**Key Concepts:**
- **REST**: Standard way to design APIs (GET, POST, PUT, DELETE)
- **JSON**: Data format for API requests/responses
- **Pydantic**: Validates data automatically

```python
"""
FastAPI Application - REST API for E-Commerce

This creates the API endpoints that the frontend will call.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import os

from .models import (
    init_db, get_session, get_engine,
    User, Product, CartItem, Order, OrderItem
)

# Initialize FastAPI app
app = FastAPI(
    title="SmartTest E-Commerce API",
    description="API for AI-powered testing demo",
    version="1.0.0"
)

# Enable CORS (Cross-Origin Resource Sharing)
# This allows the frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
engine = init_db()

# Dependency: Get database session
def get_db():
    db = get_session(engine)
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# PYDANTIC SCHEMAS (API Request/Response Models)
# ============================================================================

class ProductCreate(BaseModel):
    """Schema for creating a product."""
    name: str
    description: str
    price: float
    stock: int
    category: str
    image_url: Optional[str] = None

class ProductResponse(BaseModel):
    """Schema for product response."""
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
    """Schema for adding to cart."""
    product_id: int
    quantity: int = 1

class CartItemResponse(BaseModel):
    """Schema for cart item response."""
    id: int
    product_name: str
    product_price: float
    quantity: int
    subtotal: float

class OrderCreate(BaseModel):
    """Schema for creating an order."""
    user_id: int

class OrderResponse(BaseModel):
    """Schema for order response."""
    id: int
    status: str
    total_amount: float
    created_at: str
    items: List[dict]

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "message": "SmartTest E-Commerce API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# ---------------------------------------------------------------------------
# PRODUCT ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/api/products", response_model=List[ProductResponse])
def get_products(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all products, optionally filtered by category.
    
    Query params:
        - category: Filter by product category
        - skip: Pagination offset
        - limit: Max items to return
    """
    query = db.query(Product)
    
    if category:
        query = query.filter(Product.category == category)
    
    products = query.offset(skip).limit(limit).all()
    return products

@app.get("/api/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/api/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product (admin only in real app)."""
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# ---------------------------------------------------------------------------
# CART ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/api/cart/{user_id}")
def get_cart(user_id: int, db: Session = Depends(get_db)):
    """Get user's shopping cart with calculated totals."""
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
    
    return {
        "items": result,
        "total": total,
        "item_count": len(result)
    }

@app.post("/api/cart")
def add_to_cart(item: CartItemCreate, user_id: int, db: Session = Depends(get_db)):
    """Add item to user's cart."""
    # Check if product exists and has stock
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Check if item already in cart
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
    """Remove item from cart."""
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(item)
    db.commit()
    return {"message": "Item removed from cart"}

# ---------------------------------------------------------------------------
# ORDER ENDPOINTS
# ---------------------------------------------------------------------------

@app.post("/api/orders")
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """
    Create order from user's cart.
    
    This is the checkout process:
    1. Get cart items
    2. Calculate total
    3. Create order
    4. Clear cart
    """
    # Get cart items
    cart_items = db.query(CartItem).filter(CartItem.user_id == order.user_id).all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate total
    total = 0
    for item in cart_items:
        total += item.product.price * item.quantity
    
    # Create order
    new_order = Order(
        user_id=order.user_id,
        status="pending",
        total_amount=total
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # Create order items
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.product.price
        )
        db.add(order_item)
    
    # Clear cart
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
    """Get all orders for a user."""
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    
    result = []
    for order in orders:
        items = []
        for item in order.items:
            items.append({
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price
            })
        
        result.append({
            "id": order.id,
            "status": order.status,
            "total": order.total_amount,
            "created_at": order.created_at.isoformat(),
            "items": items
        })
    
    return result

# ---------------------------------------------------------------------------
# SEED DATA (For demo purposes)
# ---------------------------------------------------------------------------

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
```

---

### Step 1.3: Frontend - React Setup

**File:** `ecommerce-app/frontend/package.json`

**What you're doing:** Defining JavaScript dependencies

**Why:** React is the most popular frontend framework

```json
{
  "name": "smarttest-ecommerce-frontend",
  "version": "1.0.0",
  "description": "E-commerce frontend for SmartTest AI demo",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  },
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

---

**File:** `ecommerce-app/frontend/index.html`

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SmartTest E-Commerce</title>
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        background-color: #f5f5f5;
      }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

---

**File:** `ecommerce-app/frontend/src/main.jsx`

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

---

**File:** `ecommerce-app/frontend/src/App.jsx`

**What you're doing:** Creating the main React application

**Why:** React components make UI development modular and reusable

**Key Concepts:**
- **Components**: Reusable UI pieces
- **State**: Data that changes over time
- **Props**: Data passed to components
- **useEffect**: Run code when component mounts/updates
- **useState**: Manage component state

```jsx
import React, { useState, useEffect } from 'react'
import axios from 'axios'

// API base URL
const API_URL = 'http://localhost:8000'

/**
 * Main App Component
 * 
 * Manages global state: cart, current view, products
 */
function App() {
  // State management
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [currentView, setCurrentView] = useState('products') // products, cart, orders
  const [loading, setLoading] = useState(true)
  const [userId] = useState(1) // Demo user

  // Load products on mount
  useEffect(() => {
    fetchProducts()
    fetchCart()
  }, [])

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/products`)
      setProducts(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching products:', error)
      setLoading(false)
    }
  }

  const fetchCart = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/cart/${userId}`)
      setCart(response.data.items || [])
    } catch (error) {
      console.error('Error fetching cart:', error)
    }
  }

  const addToCart = async (productId) => {
    try {
      await axios.post(`${API_URL}/api/cart?user_id=${userId}`, {
        product_id: productId,
        quantity: 1
      })
      fetchCart() // Refresh cart
      alert('Added to cart!')
    } catch (error) {
      console.error('Error adding to cart:', error)
      alert('Failed to add to cart')
    }
  }

  const removeFromCart = async (itemId) => {
    try {
      await axios.delete(`${API_URL}/api/cart/${itemId}`)
      fetchCart() // Refresh cart
    } catch (error) {
      console.error('Error removing from cart:', error)
    }
  }

  const checkout = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/orders`, {
        user_id: userId
      })
      alert(`Order placed! Order ID: ${response.data.order_id}`)
      setCart([])
      setCurrentView('orders')
    } catch (error) {
      console.error('Error during checkout:', error)
      alert('Checkout failed')
    }
  }

  // Calculate cart total
  const cartTotal = cart.reduce((sum, item) => sum + item.subtotal, 0)

  if (loading) {
    return <div style={styles.loading}>Loading...</div>
  }

  return (
    <div style={styles.app}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.logo}>🛍️ SmartTest Shop</h1>
        <nav style={styles.nav}>
          <button 
            style={currentView === 'products' ? styles.navButtonActive : styles.navButton}
            onClick={() => setCurrentView('products')}
          >
            Products
          </button>
          <button 
            style={currentView === 'cart' ? styles.navButtonActive : styles.navButton}
            onClick={() => setCurrentView('cart')}
          >
            Cart ({cart.length})
          </button>
          <button 
            style={currentView === 'orders' ? styles.navButtonActive : styles.navButton}
            onClick={() => setCurrentView('orders')}
          >
            Orders
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main style={styles.main}>
        {currentView === 'products' && (
          <ProductList products={products} onAddToCart={addToCart} />
        )}
        {currentView === 'cart' && (
          <Cart 
            items={cart} 
            total={cartTotal}
            onRemove={removeFromCart}
            onCheckout={checkout}
          />
        )}
        {currentView === 'orders' && (
          <Orders userId={userId} />
        )}
      </main>
    </div>
  )
}

/**
 * Product List Component
 * Displays grid of products
 */
function ProductList({ products, onAddToCart }) {
  return (
    <div style={styles.productGrid}>
      {products.map(product => (
        <div key={product.id} style={styles.productCard}>
          <img 
            src={product.image_url} 
            alt={product.name}
            style={styles.productImage}
          />
          <div style={styles.productInfo}>
            <h3 style={styles.productName}>{product.name}</h3>
            <p style={styles.productDescription}>{product.description}</p>
            <p style={styles.productCategory}>{product.category}</p>
            <div style={styles.productFooter}>
              <span style={styles.productPrice}>${product.price}</span>
              <button 
                style={styles.addButton}
                onClick={() => onAddToCart(product.id)}
              >
                Add to Cart
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * Cart Component
 * Shows cart items and checkout
 */
function Cart({ items, total, onRemove, onCheckout }) {
  if (items.length === 0) {
    return (
      <div style={styles.emptyState}>
        <h2>Your cart is empty</h2>
        <p>Add some products to get started!</p>
      </div>
    )
  }

  return (
    <div style={styles.cart}>
      <h2 style={styles.cartTitle}>Shopping Cart</h2>
      {items.map(item => (
        <div key={item.id} style={styles.cartItem}>
          <img src={item.image_url} alt={item.product_name} style={styles.cartItemImage} />
          <div style={styles.cartItemInfo}>
            <h4>{item.product_name}</h4>
            <p>Quantity: {item.quantity}</p>
            <p>${item.subtotal.toFixed(2)}</p>
          </div>
          <button 
            style={styles.removeButton}
            onClick={() => onRemove(item.id)}
          >
            Remove
          </button>
        </div>
      ))}
      <div style={styles.cartTotal}>
        <h3>Total: ${total.toFixed(2)}</h3>
        <button style={styles.checkoutButton} onClick={onCheckout}>
          Proceed to Checkout
        </button>
      </div>
    </div>
  )
}

/**
 * Orders Component
 * Shows order history
 */
function Orders({ userId }) {
  const [orders, setOrders] = useState([])

  useEffect(() => {
    fetchOrders()
  }, [userId])

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/orders/${userId}`)
      setOrders(response.data)
    } catch (error) {
      console.error('Error fetching orders:', error)
    }
  }

  if (orders.length === 0) {
    return (
      <div style={styles.emptyState}>
        <h2>No orders yet</h2>
        <p>Your order history will appear here</p>
      </div>
    )
  }

  return (
    <div style={styles.orders}>
      <h2 style={styles.ordersTitle}>Your Orders</h2>
      {orders.map(order => (
        <div key={order.id} style={styles.orderCard}>
          <div style={styles.orderHeader}>
            <span>Order #{order.id}</span>
            <span style={styles.orderStatus}>{order.status}</span>
          </div>
          <p>Total: ${order.total.toFixed(2)}</p>
          <p>Items: {order.items.length}</p>
        </div>
      ))}
    </div>
  )
}

// Styles (inline for simplicity)
const styles = {
  app: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    backgroundColor: '#2c3e50',
    color: 'white',
    padding: '1rem 2rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    fontSize: '1.5rem',
  },
  nav: {
    display: 'flex',
    gap: '1rem',
  },
  navButton: {
    padding: '0.5rem 1rem',
    backgroundColor: 'transparent',
    color: 'white',
    border: '1px solid white',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  navButtonActive: {
    padding: '0.5rem 1rem',
    backgroundColor: '#3498db',
    color: 'white',
    border: '1px solid #3498db',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  main: {
    flex: 1,
    padding: '2rem',
    maxWidth: '1200px',
    margin: '0 auto',
    width: '100%',
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    fontSize: '1.5rem',
  },
  productGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '2rem',
  },
  productCard: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  },
  productImage: {
    width: '100%',
    height: '200px',
    objectFit: 'cover',
  },
  productInfo: {
    padding: '1rem',
  },
  productName: {
    marginBottom: '0.5rem',
  },
  productDescription: {
    color: '#666',
    fontSize: '0.9rem',
    marginBottom: '0.5rem',
  },
  productCategory: {
    color: '#3498db',
    fontSize: '0.8rem',
    textTransform: 'uppercase',
    marginBottom: '1rem',
  },
  productFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  productPrice: {
    fontSize: '1.25rem',
    fontWeight: 'bold',
    color: '#27ae60',
  },
  addButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  emptyState: {
    textAlign: 'center',
    padding: '3rem',
    color: '#666',
  },
  cart: {
    maxWidth: '600px',
    margin: '0 auto',
  },
  cartTitle: {
    marginBottom: '1.5rem',
  },
  cartItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    padding: '1rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    marginBottom: '1rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  cartItemImage: {
    width: '80px',
    height: '80px',
    objectFit: 'cover',
    borderRadius: '4px',
  },
  cartItemInfo: {
    flex: 1,
  },
  removeButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#e74c3c',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  cartTotal: {
    marginTop: '2rem',
    padding: '1.5rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    textAlign: 'center',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  checkoutButton: {
    marginTop: '1rem',
    padding: '1rem 2rem',
    backgroundColor: '#27ae60',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1.1rem',
    cursor: 'pointer',
  },
  orders: {
    maxWidth: '600px',
    margin: '0 auto',
  },
  ordersTitle: {
    marginBottom: '1.5rem',
  },
  orderCard: {
    padding: '1.5rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    marginBottom: '1rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  orderHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '0.5rem',
  },
  orderStatus: {
    color: '#3498db',
    fontWeight: 'bold',
  },
}

export default App
```

---

### Step 1.4: Docker Setup

**File:** `ecommerce-app/docker-compose.yml`

**What you're doing:** Defining infrastructure as code

**Why:** Docker ensures consistent environments across machines

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: smarttest-db
    environment:
      POSTGRES_USER: smarttest
      POSTGRES_PASSWORD: smarttest123
      POSTGRES_DB: ecommerce
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U smarttest"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build: ./backend
    container_name: smarttest-backend
    environment:
      DATABASE_URL: postgresql://smarttest:smarttest123@db:5432/ecommerce
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend (optional - can also run locally)
  frontend:
    build: ./frontend
    container_name: smarttest-frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host

volumes:
  postgres_data:
```

---

**File:** `ecommerce-app/backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./app ./app

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**File:** `ecommerce-app/frontend/Dockerfile`

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json .
RUN npm install

# Copy application
COPY . .

# Expose port
EXPOSE 3000

# Run application
CMD ["npm", "run", "dev", "--", "--host"]
```

---

## 🧪 Verification Steps

### Step 1: Start the Database

```bash
cd ecommerce-app
docker-compose up -d db

# Wait for database to be ready
docker-compose logs -f db
# Look for: "database system is ready to accept connections"
```

**Expected:** PostgreSQL running on port 5432

### Step 2: Start the Backend

```bash
# Option A: With Docker
docker-compose up -d backend

# Option B: Local development
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://smarttest:smarttest123@localhost:5432/ecommerce"
uvicorn app.main:app --reload
```

**Expected:** API running at http://localhost:8000

**Test it:**
```bash
curl http://localhost:8000/
# Should return: {"message": "SmartTest E-Commerce API", ...}
```

### Step 3: Seed the Database

```bash
curl -X POST http://localhost:8000/api/seed
```

**Expected:** `{"message": "Added 6 sample products"}`

### Step 4: Start the Frontend

```bash
# Option A: With Docker
docker-compose up -d frontend

# Option B: Local development
cd frontend
npm install
npm run dev
```

**Expected:** Frontend at http://localhost:3000

---

## ✅ Success Checklist

- [ ] Database is running (check with `docker ps`)
- [ ] Backend API responds at http://localhost:8000
- [ ] API docs available at http://localhost:8000/docs
- [ ] Frontend loads at http://localhost:3000
- [ ] Can see product list
- [ ] Can add items to cart
- [ ] Can checkout (creates order)

---

## 💡 Key Takeaways

### What You Learned

1. **FastAPI**: Modern Python web framework
   - Automatic API documentation
   - Type hints with Pydantic
   - Dependency injection

2. **SQLAlchemy**: Database ORM
   - Models = Tables
   - Relationships between tables
   - Session management

3. **React**: Component-based frontend
   - State management with hooks
   - Effect handling
   - Component composition

4. **Docker**: Containerization
   - Consistent environments
   - Easy database setup
   - Service orchestration

### Interview Talking Points

> "I built a full-stack e-commerce application with FastAPI backend and React frontend. The backend uses SQLAlchemy ORM with PostgreSQL for data persistence, and includes REST endpoints for products, cart, and orders. The frontend is a single-page application with React hooks for state management."

### Architecture Decisions

| Decision | Why |
|----------|-----|
| FastAPI | Modern, fast, automatic docs |
| React | Industry standard, component-based |
| PostgreSQL | Robust, production-ready |
| Docker | Easy setup, consistent environments |
| SQLAlchemy | Pythonic ORM, migration support |

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" to DB | Wait for DB to start: `docker-compose logs db` |
| "Module not found" | Run from correct directory, check imports |
| Port already in use | Kill process on port 8000/3000 or change ports |
| CORS errors | Backend CORS middleware should allow all origins |

---

## 🎉 Next Step

**Go to: [Step 2 - RAG Code Indexer](STEP2.md)**

You'll build the AI system that indexes this codebase!
