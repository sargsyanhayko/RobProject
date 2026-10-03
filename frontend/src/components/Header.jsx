import { Link } from 'react-router-dom'
import './Header.css'

export default function Header() {
  return (
    <header className="site-header">
      <div className="container site-header__inner">
        <Link to="/" className="site-header__logo">
          RobProject
        </Link>
        <nav className="site-header__nav">
          <Link to="/" className="site-header__link">
            Products
          </Link>
        </nav>
      </div>
    </header>
  )
}
