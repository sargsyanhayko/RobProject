import { PRODUCT_CATEGORIES } from '../config/productCategories'
import './ProductCategoryTabs.css'

export default function ProductCategoryTabs({ category, onChange, disabled = false }) {
  return (
    <nav className="category-menu" aria-label="Product categories">
      {PRODUCT_CATEGORIES.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          className={`category-menu__item${category === value ? ' category-menu__item--active' : ''}`}
          aria-pressed={category === value}
          disabled={disabled}
          onClick={() => onChange(value)}
        >
          {label}
        </button>
      ))}
    </nav>
  )
}
