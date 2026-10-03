import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProduct, updateProduct } from '../api/client'
import LoadingState from '../components/LoadingState'
import ProductImageInput from '../components/ProductImageInput'
import './ProductFormPage.css'

export default function ProductEditPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [form, setForm] = useState(null)
  const [image, setImage] = useState(null)
  const [removeImage, setRemoveImage] = useState(false)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getProduct(id)
      .then(({ data }) => {
        setImage(null)
        setRemoveImage(false)
        setForm({
          title: data.title,
          description: data.description || '',
          price: data.price,
          image_url: data.image_url || '',
        })
      })
      .catch(() => setError('Unable to load product.'))
  }, [id])

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
      ...(removeImage ? { image_url: null } : {}),
    }

    updateProduct(id, payload, image)
      .then(() => navigate('/admin'))
      .catch((err) => {
        const detail = err.response?.data?.detail
        if (Array.isArray(detail)) {
          setError(detail.map((d) => d.msg || d.message).join(', '))
        } else {
          setError(detail || 'Unable to save changes.')
        }
        setSaving(false)
      })
  }

  if (!form && !error) return (
    <div className="admin">
      <header className="admin-header">
        <div className="container admin-header__inner">
          <span className="admin-header__title">RobProject Admin</span>
        </div>
      </header>
      <main className="container admin-main"><LoadingState /></main>
    </div>
  )

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
        <h2 className="form-page__title">Edit product</h2>
        {error && !form ? (
          <div className="alert alert-error">{error}</div>
        ) : (
          <form onSubmit={handleSubmit} className="product-form fade-in">
            {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}
            <div className="form-group">
              <label className="form-label">Title</label>
              <input className="form-input" type="text" value={form.title} onChange={handleChange('title')} required maxLength={255} />
            </div>
            <div className="form-group">
              <label className="form-label">Price ($)</label>
              <input className="form-input" type="number" step="0.01" min="0" value={form.price} onChange={handleChange('price')} required />
            </div>
            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea className="form-textarea" value={form.description} onChange={handleChange('description')} />
            </div>
            <ProductImageInput
              file={image}
              currentImageUrl={removeImage ? null : form.image_url}
              onChange={(file) => { setImage(file); setRemoveImage(false) }}
              onRemove={() => { setImage(null); setRemoveImage(true) }}
              onError={setError}
              disabled={saving}
            />
            <div className="product-form__actions">
              <button type="button" className="btn btn-secondary" onClick={() => navigate('/admin')}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Saving…' : 'Save changes'}
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  )
}
