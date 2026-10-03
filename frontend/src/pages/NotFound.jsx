import { Link } from 'react-router-dom'
import './NotFound.css'

export default function NotFound() {
  return (
    <main className="container not-found">
      <h1>404</h1>
      <p>Page not found.</p>
      <Link to="/" className="btn btn-primary" style={{ marginTop: 24 }}>
        Return home
      </Link>
    </main>
  )
}
