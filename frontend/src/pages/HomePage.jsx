import { useEffect, useState } from 'react'
import { getProducts } from '../api/client'
import Header from '../components/Header'
import ProductGrid from '../components/ProductGrid'
import LoadingState from '../components/LoadingState'
import './HomePage.css'

export default function HomePage() {
  const [products, setProducts] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getProducts(0, 100)
      .then(({ data }) => setProducts(data))
      .catch(() => setError('Unable to load products.'))
  }, [])

  return (
    <>
      <Header />
      <main className="container home">
        <section className="hero fade-in">
          <h1>Products</h1>
          <p className="hero__subtitle">Explore our collection.</p>
        </section>

        {error && (
          <div className="state-box">
            <h3>Something went wrong</h3>
            <p>{error}</p>
          </div>
        )}

        {!error && !products && <LoadingState />}

        {!error && products && products.length === 0 && (
          <div className="state-box">
            <h3>No products available.</h3>
            <p>Please check back later.</p>
          </div>
        )}

        {!error && products && products.length > 0 && <ProductGrid products={products} />}
      </main>
    </>
  )
}
