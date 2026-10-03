import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getProduct, resolveProductImageUrl } from '../api/client'
import Header from '../components/Header'
import LoadingState from '../components/LoadingState'
import { getCategoryLabel } from '../config/productCategories'
import './ProductPage.css'

export default function ProductPage() {
  const { id } = useParams()
  const [product, setProduct] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getProduct(id)
      .then(({ data }) => setProduct(data))
      .catch((err) => {
        setError(err.response?.status === 404 ? 'Product not found.' : 'Unable to load product.')
      })
  }, [id])

  return (
    <div className="catalog-page">
      <Header />
      <main className="container product-detail">
        <Link to="/" className="back-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back
        </Link>

        {error && (
          <div className="state-box">
            <h3>{error}</h3>
            <Link to="/" className="btn btn-secondary btn-sm" style={{ marginTop: 16 }}>
              Return home
            </Link>
          </div>
        )}

        {!error && !product && <LoadingState />}

        {!error && product && (
          <div className="product-detail__grid fade-in">
            <div className="product-detail__image">
              {product.image_url ? (
                <img src={resolveProductImageUrl(product.image_url)} alt={product.title} />
              ) : (
                <div className="product-detail__placeholder">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <rect x="3" y="3" width="18" height="18" rx="2" />
                    <circle cx="8.5" cy="8.5" r="1.5" />
                    <path d="M21 15l-5-5L5 21" />
                  </svg>
                </div>
              )}
            </div>
            <div className="product-detail__content">
              <p className="product-detail__category">{getCategoryLabel(product.category)}</p>
              <h1>{product.title}</h1>
              <p className="product-detail__price">${product.price}</p>
              {product.description && (
                <p className="product-detail__description">{product.description}</p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
