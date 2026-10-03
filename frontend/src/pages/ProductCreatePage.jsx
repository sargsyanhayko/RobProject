import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createProduct } from '../api/client'
import './ProductFormPage.css'

export default function ProductCreatePage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ title: '', description: '', price: '', image_url: '' })
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  const handleChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setError(null)
    setSaving(true)

    const payload = {
      title: form.title,
      price: form.price,
      description: form.description || null,
      image_url: form.image_url || null,
    }

    createProduct(payload)
      .then(() => navigate('/admin'))
      .catch((err) => {
        const detail = err.response?.data?.detail
        if (Array.isArray(detail)) {
          setError(detail.map((d) => d.msg || d.message).join(', '))
        } else {
          setError(detail || 'Unable to create product.')
        }
        setSaving(false)
      })
  }

  return (
    <div className="admin">
      <header className="admin-header">
        <div className="container admin-header__inner">
          <span className="admin-header__title">RobProject Admin</span>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/admin')}>
            Back to list
          </button>
        </div>
      </header>

      <main className="container admin-main">
        <h2 className="form-page__title">Add product</h2>
        <ProductForm form={form} onChange={handleChange} onSubmit={handleSubmit} error={error} saving={saving} submitLabel="Save" />
      </main>
    </div>
  )
}

function ProductForm({ form, onChange, onSubmit, error, saving, submitLabel }) {
  return (
    <form onSubmit={onSubmit} className="product-form fade-in">
      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}
      <div className="form-group">
        <label className="form-label">Title</label>
        <input className="form-input" type="text" value={form.title} onChange={onChange('title')} required maxLength={255} placeholder="Product title" />
      </div>
      <div className="form-group">
        <label className="form-label">Price</label>
        <input className="form-input" type="number" step="0.01" min="0" value={form.price} onChange={onChange('price')} required placeholder="0.00" />
      </div>
      <div className="form-group">
        <label className="form-label">Description</label>
        <textarea className="form-textarea" value={form.description} onChange={onChange('description')} placeholder="Optional description" />
      </div>
      <div className="form-group">
        <label className="form-label">Image URL</label>
        <input className="form-input" type="url" value={form.image_url} onChange={onChange('image_url')} maxLength={1000} placeholder="https://example.com/image.jpg" />
      </div>
      <div className="product-form__actions">
        <button type="button" className="btn btn-secondary" onClick={() => window.history.back()}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Saving…' : submitLabel}
        </button>
      </div>
    </form>
  )
}
