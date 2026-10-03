import { useEffect, useRef } from 'react'
import { resolveProductImageUrl } from '../api/client'

const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
const maxImageBytes = 5 * 1024 * 1024

export default function ProductImageInput({ file, currentImageUrl, onChange, onRemove, onError, disabled }) {
  const inputRef = useRef(null)
  const previewRef = useRef(null)

  useEffect(() => {
    if (!file) return
    const url = URL.createObjectURL(file)
    previewRef.current.src = url
    return () => URL.revokeObjectURL(url)
  }, [file])

  const handleChange = (event) => {
    const selected = event.target.files?.[0]
    if (!selected) return
    if (selected.size > maxImageBytes || (selected.type && !allowedTypes.includes(selected.type))) {
      event.target.value = ''
      onError('Choose a JPEG, PNG, WebP or GIF photo up to 5 MB.')
      return
    }
    onError(null)
    onChange(selected)
  }

  const handleRemove = () => {
    inputRef.current.value = ''
    onRemove()
    onError(null)
  }

  return (
    <div className="form-group">
      <label className="form-label" htmlFor="product-image">Photo</label>
      <input
        ref={inputRef}
        id="product-image"
        className="form-input"
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif"
        onChange={handleChange}
        disabled={disabled}
        aria-describedby="product-image-help"
      />
      <p className="product-photo__help" id="product-image-help">JPEG, PNG, WebP or GIF. Up to 5 MB.</p>
      {(file || currentImageUrl) && (
        <div className="product-photo">
          <img ref={previewRef} className="product-photo__preview" src={file ? undefined : resolveProductImageUrl(currentImageUrl)} alt="Product photo preview" />
          <button type="button" className="btn btn-secondary btn-sm" onClick={handleRemove} disabled={disabled}>
            Remove photo
          </button>
        </div>
      )}
    </div>
  )
}
