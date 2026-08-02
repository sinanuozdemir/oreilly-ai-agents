"""Step 2: Populating the Vector DB with Code, Docs, and Tests

WHAT WE'LL DO
-------------
Create a realistic mock codebase and load it into the vector database.

REALISTIC SCENARIO
------------------
Imagine we're building a RAG system for an e-commerce platform with:
- User authentication
- Product catalog
- Payment processing
- Order management

This mirrors what you'd find at:
- Amazon, Shopify, Stripe
- Any SaaS company
- Your current/future workplace

TYPES OF DATA WE'LL STORE
-------------------------
1. CODE FILES: Python modules, functions, classes
2. API SPECS: OpenAPI specs, endpoint documentation
3. TEST FILES: Unit tests, integration tests
4. PR DESCRIPTIONS: Past changes and their context
"""

import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Connect to our database
print("🔌 Connecting to vector database...")
client = chromadb.PersistentClient(path="./vector_db")

# Get or create the collection
try:
    collection = client.get_collection("codebase")
    print("✓ Connected to 'codebase' collection")
except:
    collection = client.create_collection("codebase")
    print("✓ Created 'codebase' collection")

# Use OpenAI embeddings (free tier available)
# In production, you might use local embeddings to save costs
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("\n⚠️  WARNING: OPENAI_API_KEY not found!")
    print("   Please set it: export OPENAI_API_KEY='sk-your-key'")
    print("   Or create a .env file with: OPENAI_API_KEY=sk-your-key")
    print("\n   For now, using simple keyword-based embeddings (limited functionality)\n")
    
    # Simple fallback embedding function (word overlap based)
    class SimpleEmbeddingFunction:
        def __init__(self):
            pass
        
        def __call__(self, texts):
            # Simple bag-of-words embedding (for demo purposes)
            import numpy as np
            embeddings = []
            for text in texts:
                # Create a simple embedding based on word presence
                words = set(text.lower().split())
                # Create a 384-dim vector (common embedding size)
                np.random.seed(42)
                vec = np.random.randn(384)
                # Modify based on text length as a simple signal
                vec[0] = len(words) / 100.0
                embeddings.append(vec.tolist())
            return embeddings
    
    openai_ef = SimpleEmbeddingFunction()
else:
    print(f"✓ OpenAI API key found (ends with ...{openai_api_key[-4:]})")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=openai_api_key,
        model_name="text-embedding-3-small"
    )

print("\n📦 Preparing sample data...")

# ============================================================================
# SAMPLE CODE REPOSITORY DATA
# ============================================================================

code_documents = [
    # AUTHENTICATION MODULE
    {
        "id": "auth_login_001",
        "type": "code",
        "file": "auth/login.py",
        "content": """
def authenticate_user(username: str, password: str) -> dict:
    \"\"\"
    Authenticate a user with username and password.
    Returns user data with JWT token on success.
    Raises AuthenticationError on failure.
    \"\"\"
    user = db.users.find_one({"username": username})
    if not user or not verify_password(password, user["password_hash"]):
        raise AuthenticationError("Invalid credentials")
    
    token = generate_jwt(user["id"], expires_in=3600)
    return {"user": user, "token": token}
        """,
        "metadata": {
            "module": "auth",
            "function": "authenticate_user",
            "description": "User login with JWT token generation"
        }
    },
    
    {
        "id": "auth_middleware_001",
        "type": "code",
        "file": "auth/middleware.py",
        "content": """
class AuthMiddleware:
    \"\"\"Middleware to validate JWT tokens on protected routes.\"\"\"
    
    def process_request(self, request):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            raise UnauthorizedError("No token provided")
        
        try:
            payload = decode_jwt(token)
            request.user_id = payload["user_id"]
        except JWTError:
            raise UnauthorizedError("Invalid token")
        """,
        "metadata": {
            "module": "auth",
            "class": "AuthMiddleware",
            "description": "JWT validation middleware for protected routes"
        }
    },
    
    # PAYMENT MODULE
    {
        "id": "payment_process_001",
        "type": "code",
        "file": "payments/processor.py",
        "content": """
class PaymentProcessor:
    \"\"\"Process payments through Stripe integration.\"\"\"
    
    def charge(self, amount: float, currency: str, card_token: str) -> Payment:
        \"\"\"Charge a customer's card.\"\"\"
        try:
            stripe_charge = stripe.Charge.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                source=card_token,
                capture=True
            )
            return Payment(
                id=stripe_charge.id,
                amount=amount,
                status="completed"
            )
        except stripe.error.CardError as e:
            raise PaymentError(f"Card declined: {e.message}")
        """,
        "metadata": {
            "module": "payments",
            "class": "PaymentProcessor",
            "description": "Stripe payment processing with error handling"
        }
    },
    
    {
        "id": "payment_refund_001",
        "type": "code",
        "file": "payments/refunds.py",
        "content": """
def process_refund(payment_id: str, amount: float = None) -> Refund:
    \"\"\"
    Process a refund for a previous payment.
    If amount is None, refunds the full payment amount.
    \"\"\"
    payment = db.payments.find_one({"id": payment_id})
    if not payment:
        raise NotFoundError(f"Payment {payment_id} not found")
    
    refund_amount = amount or payment["amount"]
    
    stripe_refund = stripe.Refund.create(
        charge=payment["stripe_charge_id"],
        amount=int(refund_amount * 100)
    )
    
    return Refund(
        id=stripe_refund.id,
        payment_id=payment_id,
        amount=refund_amount
    )
        """,
        "metadata": {
            "module": "payments",
            "function": "process_refund",
            "description": "Process partial or full refunds via Stripe"
        }
    },
    
    # ORDER MODULE
    {
        "id": "order_create_001",
        "type": "code",
        "file": "orders/service.py",
        "content": """
class OrderService:
    \"\"\"Handle order creation and lifecycle.\"\"\"
    
    def create_order(self, user_id: str, items: list) -> Order:
        \"\"\"Create a new order from cart items.\"\"\"
        # Calculate totals
        total = sum(item["price"] * item["quantity"] for item in items)
        
        order = Order(
            user_id=user_id,
            items=items,
            total=total,
            status="pending"
        )
        
        # Save to database
        db.orders.insert_one(order.to_dict())
        
        # Send confirmation email
        self.email_service.send_order_confirmation(order)
        
        return order
    
    def cancel_order(self, order_id: str) -> Order:
        \"\"\"Cancel an order and refund payment.\"\"\"
        order = self.get_order(order_id)
        
        if order.status == "shipped":
            raise OrderError("Cannot cancel shipped order")
        
        # Process refund
        if order.payment_id:
            process_refund(order.payment_id)
        
        order.status = "cancelled"
        order.save()
        
        return order
        """,
        "metadata": {
            "module": "orders",
            "class": "OrderService",
            "description": "Order creation, cancellation, and refund integration"
        }
    },
]

# ============================================================================
# API DOCUMENTATION
# ============================================================================

api_documents = [
    {
        "id": "api_auth_post",
        "type": "api_spec",
        "file": "api/auth.yaml",
        "content": """
POST /api/v1/auth/login
Authenticate a user and return JWT token.

Request Body:
  - username (string, required): User's username
  - password (string, required): User's password

Response 200:
  - user (object): User profile data
  - token (string): JWT access token

Response 401:
  - error: Invalid credentials

Related: authenticate_user function in auth/login.py
        """,
        "metadata": {
            "endpoint": "/api/v1/auth/login",
            "method": "POST",
            "tags": ["authentication", "login"],
            "related_code": "auth/login.py"
        }
    },
    
    {
        "id": "api_payment_post",
        "type": "api_spec",
        "file": "api/payments.yaml",
        "content": """
POST /api/v1/payments/charge
Process a payment for an order.

Request Body:
  - order_id (string, required): Order to pay for
  - card_token (string, required): Stripe card token
  - amount (number, required): Amount to charge

Response 200:
  - payment_id (string): Payment transaction ID
  - status (string): "completed" or "pending"

Response 402:
  - error: Payment failed
  - reason: Card declined or insufficient funds

Notes: 
  - Requires authentication
  - Idempotent - safe to retry
  - Webhook confirms async processing
        """,
        "metadata": {
            "endpoint": "/api/v1/payments/charge",
            "method": "POST",
            "tags": ["payments", "stripe", "charging"],
            "related_code": "payments/processor.py"
        }
    },
    
    {
        "id": "api_refund_post",
        "type": "api_spec",
        "file": "api/payments.yaml",
        "content": """
POST /api/v1/payments/refund
Refund a previous payment.

Request Body:
  - payment_id (string, required): Payment to refund
  - amount (number, optional): Amount to refund (default: full amount)

Response 200:
  - refund_id (string): Refund transaction ID
  - amount (number): Refunded amount
  - status: "refunded"

Response 404:
  - error: Payment not found

Related: process_refund function in payments/refunds.py
        """,
        "metadata": {
            "endpoint": "/api/v1/payments/refund",
            "method": "POST",
            "tags": ["payments", "refunds"],
            "related_code": "payments/refunds.py"
        }
    },
]

# ============================================================================
# TEST FILES
# ============================================================================

test_documents = [
    {
        "id": "test_auth_login",
        "type": "test",
        "file": "tests/test_auth.py",
        "content": """
def test_successful_login():
    \"\"\"Test login with valid credentials.\"\"\"
    result = authenticate_user("testuser", "correctpassword")
    assert "token" in result
    assert result["user"]["username"] == "testuser"

def test_invalid_password():
    \"\"\"Test login fails with wrong password.\"\"\"
    with pytest.raises(AuthenticationError):
        authenticate_user("testuser", "wrongpassword")

def test_missing_user():
    \"\"\"Test login fails for non-existent user.\"\"\"
    with pytest.raises(AuthenticationError):
        authenticate_user("nonexistent", "password")
        """,
        "metadata": {
            "test_type": "unit",
            "module_tested": "auth",
            "coverage": ["authenticate_user"]
        }
    },
    
    {
        "id": "test_payment_charge",
        "type": "test",
        "file": "tests/test_payments.py",
        "content": """
def test_successful_payment():
    \"\"\"Test charging a valid card.\"\"\"
    processor = PaymentProcessor()
    payment = processor.charge(
        amount=99.99,
        currency="USD",
        card_token="tok_visa"
    )
    assert payment.status == "completed"
    assert payment.amount == 99.99

def test_payment_with_card_error():
    \"\"\"Test handling declined card.\"\"\"
    processor = PaymentProcessor()
    with pytest.raises(PaymentError) as exc_info:
        processor.charge(
            amount=99.99,
            currency="USD",
            card_token="tok_charge_declined"
        )
    assert "declined" in str(exc_info.value)

def test_refund_full_amount():
    \"\"\"Test full refund of payment.\"\"\"
    payment = create_test_payment(amount=50.00)
    refund = process_refund(payment.id)
    assert refund.amount == 50.00

def test_refund_partial_amount():
    \"\"\"Test partial refund.\"\"\"
    payment = create_test_payment(amount=100.00)
    refund = process_refund(payment.id, amount=30.00)
    assert refund.amount == 30.00
        """,
        "metadata": {
            "test_type": "unit",
            "module_tested": "payments",
            "coverage": ["PaymentProcessor.charge", "process_refund"]
        }
    },
    
    {
        "id": "test_order_cancel",
        "type": "test",
        "file": "tests/test_orders.py",
        "content": """
def test_cancel_pending_order():
    \"\"\"Test cancelling an order that hasn't shipped.\"\"\"
    order = create_test_order(status="pending")
    service = OrderService()
    
    cancelled = service.cancel_order(order.id)
    assert cancelled.status == "cancelled"

def test_cancel_shipped_order_fails():
    \"\"\"Test that shipped orders cannot be cancelled.\"\"\"
    order = create_test_order(status="shipped")
    service = OrderService()
    
    with pytest.raises(OrderError):
        service.cancel_order(order.id)

def test_cancel_triggers_refund():
    \"\"\"Test that cancelling triggers payment refund.\"\"\"
    order = create_test_order(status="pending", paid=True)
    service = OrderService()
    
    with patch('orders.service.process_refund') as mock_refund:
        service.cancel_order(order.id)
        mock_refund.assert_called_once()
        """,
        "metadata": {
            "test_type": "unit",
            "module_tested": "orders",
            "coverage": ["OrderService.cancel_order", "refund integration"]
        }
    },
]

# ============================================================================
# PAST PR DESCRIPTIONS (For pattern matching)
# ============================================================================

pr_documents = [
    {
        "id": "pr_auth_001",
        "type": "pr_description",
        "file": "PR #123",
        "content": """
PR #123: Add JWT refresh token support

Changes:
- Modified authenticate_user() to return refresh_token
- Added /auth/refresh endpoint
- Updated AuthMiddleware to handle token expiration

Testing:
- Added tests for token refresh flow
- Verified backward compatibility

Related Files:
- auth/login.py
- auth/middleware.py
- tests/test_auth.py
        """,
        "metadata": {
            "pr_number": "123",
            "type": "feature",
            "affected_modules": ["auth"],
            "testing_required": True
        }
    },
    
    {
        "id": "pr_payment_001",
        "type": "pr_description",
        "file": "PR #456",
        "content": """
PR #456: Implement partial refunds

Changes:
- Modified process_refund() to accept optional amount parameter
- Added validation for refund amount <= payment amount
- Updated API spec with amount field

Testing:
- Added test_refund_partial_amount()
- Added edge case: refund amount = 0

Related Files:
- payments/refunds.py
- api/payments.yaml
- tests/test_payments.py
        """,
        "metadata": {
            "pr_number": "456",
            "type": "feature",
            "affected_modules": ["payments"],
            "testing_required": True
        }
    },
]

# ============================================================================
# LOAD ALL DATA INTO VECTOR DB
# ============================================================================

print("\n🚀 Loading data into vector database...")

all_documents = code_documents + api_documents + test_documents + pr_documents

# Add to collection
for doc in all_documents:
    collection.add(
        ids=[doc["id"]],
        documents=[doc["content"]],
        metadatas=[{**doc["metadata"], "type": doc["type"], "file": doc["file"]}]
    )

print(f"✅ Loaded {len(all_documents)} documents:")
print(f"  - {len(code_documents)} code files")
print(f"  - {len(api_documents)} API specs")
print(f"  - {len(test_documents)} test files")
print(f"  - {len(pr_documents)} PR descriptions")

# Verify count
count = collection.count()
print(f"\n📊 Total documents in database: {count}")

print("\n" + "="*60)
print("WHAT JUST HAPPENED?")
print("="*60)
print("""
We created a realistic mock codebase with:

1. CODE MODULES:
   - Authentication (login, middleware)
   - Payments (Stripe integration, refunds)
   - Orders (create, cancel with refund)

2. API DOCUMENTATION:
   - OpenAPI-style specs for each endpoint
   - Links between APIs and code

3. TEST FILES:
   - Unit tests for each module
   - Integration tests (order + refund)

4. PR HISTORY:
   - Past changes for pattern matching
   - Shows what files typically change together

All of this is now embedded in the vector database and ready
for semantic search!
""")

print("\n✅ Step 2 complete! Database populated with code data.")
print("\nNEXT: Build the RAG pipeline to query this data.")
