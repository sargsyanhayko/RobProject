import { useEffect, useState } from 'react'
import { getAllProducts } from '../api/client'
import Header from '../components/Header'
import ProductGrid from '../components/ProductGrid'
import ProductCategoryTabs from '../components/ProductCategoryTabs'
import LoadingState from '../components/LoadingState'
import { PRODUCT_CATEGORIES } from '../config/productCategories'
import './HomePage.css'

export default function HomePage() {
  const [products, setProducts] = useState(null)
  const [error, setError] = useState(null)
  const [category, setCategory] = useState(PRODUCT_CATEGORIES[0].value)

  useEffect(() => {
    const controller = new AbortController()
    getAllProducts(category, { signal: controller.signal })
      .then(({ data }) => {
        if (!controller.signal.aborted) setProducts(data)
      })
      .catch(() => {
        if (!controller.signal.aborted) setError('Unable to load products.')
      })
    return () => controller.abort()
  }, [category])

  const handleCategoryChange = (value) => {
    if (value === category) return
    setProducts(null)
    setError(null)
    setCategory(value)
  }

  return (
    <div className="catalog-page">
      <Header />
      <main className="container home">
        <section className="hero fade-in">
          <h1>Products</h1>
          <p className="hero__subtitle">Explore our collection.</p>
        </section>

        <ProductCategoryTabs category={category} onChange={handleCategoryChange} />

        <section aria-label="Products" aria-live="polite" aria-busy={!error && !products}>
          {error && (
            <div className="state-box">
              <h3>Something went wrong</h3>
              <p>{error}</p>
            </div>
          )}

          {!error && !products && <LoadingState />}

          {!error && products && products.length === 0 && (
            <div className="state-box">
              <h3>No products in this category.</h3>
              <p>Explore another category.</p>
            </div>
          )}

          {!error && products && products.length > 0 && <ProductGrid products={products} />}
        </section>
      </main>
    </div>
  )
}
