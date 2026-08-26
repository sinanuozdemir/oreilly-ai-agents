import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

function App() {
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [currentView, setCurrentView] = useState('products')
  const [loading, setLoading] = useState(true)
  const [userId] = useState(1)

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
      fetchCart()
      alert('Added to cart!')
    } catch (error) {
      alert('Failed to add to cart')
    }
  }

  const removeFromCart = async (itemId) => {
    try {
      await axios.delete(`${API_URL}/api/cart/${itemId}`)
      fetchCart()
    } catch (error) {
      console.error('Error removing from cart:', error)
    }
  }

  const checkout = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/orders`, { user_id: userId })
      alert(`Order placed! Order ID: ${response.data.order_id}`)
      setCart([])
      setCurrentView('orders')
    } catch (error) {
      alert('Checkout failed')
    }
  }

  const cartTotal = cart.reduce((sum, item) => sum + item.subtotal, 0)

  if (loading) return <div style={styles.loading}>Loading...</div>

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.logo}>🛍️ SmartTest Shop</h1>
        <nav style={styles.nav}>
          <button style={currentView === 'products' ? styles.navButtonActive : styles.navButton}
            onClick={() => setCurrentView('products')}>Products</button>
          <button style={currentView === 'cart' ? styles.navButtonActive : styles.navButton}
            onClick={() => setCurrentView('cart')}>Cart ({cart.length})</button>
          <button style={currentView === 'orders' ? styles.navButtonActive : styles.navButton}
            onClick={() => setCurrentView('orders')}>Orders</button>
        </nav>
      </header>

      <main style={styles.main}>
        {currentView === 'products' && <ProductList products={products} onAddToCart={addToCart} />}
        {currentView === 'cart' && <Cart items={cart} total={cartTotal} onRemove={removeFromCart} onCheckout={checkout} />}
        {currentView === 'orders' && <Orders userId={userId} />}
      </main>
    </div>
  )
}

function ProductList({ products, onAddToCart }) {
  return (
    <div style={styles.productGrid}>
      {products.map(product => (
        <div key={product.id} style={styles.productCard}>
          <img src={product.image_url} alt={product.name} style={styles.productImage} />
          <div style={styles.productInfo}>
            <h3>{product.name}</h3>
            <p style={styles.description}>{product.description}</p>
            <p style={styles.category}>{product.category}</p>
            <div style={styles.productFooter}>
              <span style={styles.price}>${product.price}</span>
              <button style={styles.addButton} onClick={() => onAddToCart(product.id)}>Add to Cart</button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function Cart({ items, total, onRemove, onCheckout }) {
  if (items.length === 0) {
    return <div style={styles.empty}><h2>Your cart is empty</h2></div>
  }

  return (
    <div style={styles.cart}>
      <h2>Shopping Cart</h2>
      {items.map(item => (
        <div key={item.id} style={styles.cartItem}>
          <img src={item.image_url} alt={item.product_name} style={styles.cartImage} />
          <div style={{flex: 1}}>
            <h4>{item.product_name}</h4>
            <p>Qty: {item.quantity} | ${item.subtotal.toFixed(2)}</p>
          </div>
          <button style={styles.removeButton} onClick={() => onRemove(item.id)}>Remove</button>
        </div>
      ))}
      <div style={styles.cartTotal}>
        <h3>Total: ${total.toFixed(2)}</h3>
        <button style={styles.checkoutButton} onClick={onCheckout}>Checkout</button>
      </div>
    </div>
  )
}

function Orders({ userId }) {
  const [orders, setOrders] = useState([])

  useEffect(() => {
    axios.get(`${API_URL}/api/orders/${userId}`).then(res => setOrders(res.data))
  }, [userId])

  if (orders.length === 0) return <div style={styles.empty}><h2>No orders yet</h2></div>

  return (
    <div style={styles.orders}>
      <h2>Your Orders</h2>
      {orders.map(order => (
        <div key={order.id} style={styles.orderCard}>
          <div style={styles.orderHeader}>
            <span>Order #{order.id}</span>
            <span style={styles.status}>{order.status}</span>
          </div>
          <p>Total: ${order.total.toFixed(2)} | Items: {order.items.length}</p>
        </div>
      ))}
    </div>
  )
}

const styles = {
  app: { minHeight: '100vh', display: 'flex', flexDirection: 'column' },
  header: { backgroundColor: '#2c3e50', color: 'white', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  logo: { fontSize: '1.5rem' },
  nav: { display: 'flex', gap: '1rem' },
  navButton: { padding: '0.5rem 1rem', backgroundColor: 'transparent', color: 'white', border: '1px solid white', borderRadius: '4px', cursor: 'pointer' },
  navButtonActive: { padding: '0.5rem 1rem', backgroundColor: '#3498db', color: 'white', border: '1px solid #3498db', borderRadius: '4px', cursor: 'pointer' },
  main: { flex: 1, padding: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' },
  loading: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontSize: '1.5rem' },
  productGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '2rem' },
  productCard: { backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', overflow: 'hidden' },
  productImage: { width: '100%', height: '180px', objectFit: 'cover' },
  productInfo: { padding: '1rem' },
  description: { color: '#666', fontSize: '0.9rem', margin: '0.5rem 0' },
  category: { color: '#3498db', fontSize: '0.8rem', textTransform: 'uppercase' },
  productFooter: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' },
  price: { fontSize: '1.25rem', fontWeight: 'bold', color: '#27ae60' },
  addButton: { padding: '0.5rem 1rem', backgroundColor: '#3498db', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' },
  empty: { textAlign: 'center', padding: '3rem', color: '#666' },
  cart: { maxWidth: '600px', margin: '0 auto' },
  cartItem: { display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', backgroundColor: 'white', borderRadius: '8px', marginBottom: '1rem' },
  cartImage: { width: '60px', height: '60px', objectFit: 'cover', borderRadius: '4px' },
  removeButton: { padding: '0.5rem', backgroundColor: '#e74c3c', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' },
  cartTotal: { marginTop: '2rem', padding: '1.5rem', backgroundColor: 'white', borderRadius: '8px', textAlign: 'center' },
  checkoutButton: { marginTop: '1rem', padding: '1rem 2rem', backgroundColor: '#27ae60', color: 'white', border: 'none', borderRadius: '4px', fontSize: '1.1rem', cursor: 'pointer' },
  orders: { maxWidth: '600px', margin: '0 auto' },
  orderCard: { padding: '1.5rem', backgroundColor: 'white', borderRadius: '8px', marginBottom: '1rem' },
  orderHeader: { display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' },
  status: { color: '#3498db', fontWeight: 'bold' },
}

export default App
