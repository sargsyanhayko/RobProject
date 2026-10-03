import { Link } from 'react-router-dom'
import { resolveProductImageUrl } from '../api/client'
import './ProductCard.css'

export default function ProductCard({ product }) {
  return (
    <Link to={`/products/${product.id}`} className="product-card fade-in">
      <div className="product-card__image">
        {product.image_url ? (
          <img src={resolveProductImageUrl(product.image_url)} alt={product.title} loading="lazy" />
        ) : (
          <div className="product-card__placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="M21 15l-5-5L5 21" />
            </svg>
          </div>
        )}
      </div>
      <div className="product-card__body">
        <h3 className="product-card__title">{product.title}</h3>
        {product.description && (
          <p className="product-card__desc">{product.description}</p>
        )}
        <p className="product-card__price">${product.price}</p>
      </div>
    </Link>
  )
}
