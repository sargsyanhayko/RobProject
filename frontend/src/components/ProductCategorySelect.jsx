import { PRODUCT_CATEGORIES } from '../config/productCategories'

export default function ProductCategorySelect({ value, onChange, disabled }) {
  return (
    <div className="form-group">
      <label className="form-label" htmlFor="product-category">Category</label>
      <select
        id="product-category"
        className="form-input"
        value={value}
        onChange={onChange}
        disabled={disabled}
        required
      >
        <option value="" disabled>Select a category</option>
        {PRODUCT_CATEGORIES.map(({ value, label }) => (
          <option key={value} value={value}>{label}</option>
        ))}
      </select>
    </div>
  )
}
