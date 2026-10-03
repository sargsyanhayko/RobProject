import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getProducts, deleteProduct, logout } from '../api/client'
import LoadingState from '../components/LoadingState'
import './AdminPage.css'

export default function AdminPage() {
  const navigate = useNavigate()
  const [products, setProducts] = useState(null)
  const [error, setError] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(() => {
    setError(null)
    getProducts(0, 100)
      .then(({ data }) => setProducts(data))
      .catch(() => setError('Unable to load products.'))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleLogout = () => {
    logout()
    navigate('/admin/login')
  }

  const confirmDelete = () => {
    setDeleting(true)
    deleteProduct(deleteTarget.id)
      .then(() => {
        setProducts((prev) => prev.filter((p) => p.id !== deleteTarget.id))
        setDeleteTarget(null)
      })
      .catch(() => setError('Unable to delete product.'))
      .finally(() => setDeleting(false))
  }

  return (
    <div className="admin">
      <header className="admin-header">
        <div className="container admin-header__inner">
          <span className="admin-header__title">RobProject Admin</span>
          <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <main className="container admin-main">
        <div className="admin-bar">
          <h2>Products</h2>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/admin/products/new')}>
            + Add product
          </button>
        </div>

        {error && <div className="alert alert-error" style={{ marginBottom: 24 }}>{error}</div>}

        {!error && !products && <LoadingState />}

        {!error && products && products.length === 0 && (
          <div className="state-box">
            <h3>No products yet</h3>
            <p>Click "Add product" to create your first one.</p>
          </div>
        )}

        {!error && products && products.length > 0 && (
          <div className="admin-list fade-in">
            {products.map((p) => (
              <div key={p.id} className="admin-item">
                <div className="admin-item__image">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.title} />
                  ) : (
                    <div className="admin-item__placeholder">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <rect x="3" y="3" width="18" height="18" rx="2" />
                        <circle cx="8.5" cy="8.5" r="1.5" />
                        <path d="M21 15l-5-5L5 21" />
                      </svg>
                    </div>
                  )}
                </div>
                <div className="admin-item__info">
                  <span className="admin-item__title">{p.title}</span>
                  <span className="admin-item__price">{p.price}</span>
                </div>
                <div className="admin-item__actions">
                  <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/admin/products/${p.id}/edit`)}>
                    Edit
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => setDeleteTarget(p)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {deleteTarget && (
        <div className="modal-overlay" onClick={() => !deleting && setDeleteTarget(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Delete this product?</h3>
            <p className="modal__text">"{deleteTarget.title}" will be permanently removed.</p>
            <div className="modal__actions">
              <button className="btn btn-secondary" onClick={() => setDeleteTarget(null)} disabled={deleting}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={confirmDelete} disabled={deleting}>
                {deleting ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
