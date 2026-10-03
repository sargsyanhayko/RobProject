import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createProduct, deleteProduct, getAllProducts, getProduct, updateProduct } from '../api/client'
import HomePage from '../pages/HomePage'
import AdminPage from '../pages/AdminPage'
import ProductCreatePage from '../pages/ProductCreatePage'
import ProductEditPage from '../pages/ProductEditPage'
import ProductPage from '../pages/ProductPage'

vi.mock('../api/client', () => ({
  getAllProducts: vi.fn(),
  getProduct: vi.fn(),
  createProduct: vi.fn(),
  updateProduct: vi.fn(),
  deleteProduct: vi.fn(),
  logout: vi.fn(),
  resolveProductImageUrl: (url) => url,
}))

const products = ['animals', 'wall', '3d_wall', 'other'].map((category, index) => ({
  id: index + 1,
  title: `Product ${category}`,
  price: '12.00',
  description: 'A catalog item',
  image_url: null,
  category,
}))

beforeEach(() => {
  getAllProducts.mockImplementation(async (category) => ({
    data: products.filter((product) => product.category === category),
  }))
  getProduct.mockResolvedValue({ data: products[0] })
  createProduct.mockResolvedValue({ data: products[0] })
  updateProduct.mockResolvedValue({ data: products[0] })
  deleteProduct.mockResolvedValue({ data: { message: 'Product deleted' } })
})

function renderCatalog(Page) {
  return render(<MemoryRouter><Page /></MemoryRouter>)
}

function renderAdmin(Page, path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/admin/products/new" element={<Page />} />
        <Route path="/admin/products/:id/edit" element={<Page />} />
        <Route path="/admin" element={<p>Admin list</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe.each([['public', HomePage], ['admin', AdminPage]])('%s category menu', (_, Page) => {
  it('shows Animals by default and filters the five available categories', async () => {
    const user = userEvent.setup()
    renderCatalog(Page)
    await screen.findByText('Product animals')
    expect(screen.getAllByText(/^Product /)).toHaveLength(1)
    const menu = screen.getByRole('navigation', { name: 'Product categories' })
    expect(within(menu).getAllByRole('button').map((button) => button.textContent)).toEqual(['Animals', 'Wall', '3D Wall', 'Home', 'Other'])
    expect(screen.getByRole('button', { name: 'Animals', exact: true }).getAttribute('aria-pressed')).toBe('true')
    for (const [label, category] of [['Animals', 'animals'], ['Wall', 'wall'], ['3D Wall', '3d_wall'], ['Other', 'other']]) {
      await user.click(screen.getByRole('button', { name: label, exact: true }))
      await screen.findByText(`Product ${category}`)
      expect(screen.getAllByText(/^Product /)).toHaveLength(1)
      expect(getAllProducts).toHaveBeenLastCalledWith(category, { signal: expect.any(AbortSignal) })
      expect(screen.getByRole('button', { name: label, exact: true }).getAttribute('aria-pressed')).toBe('true')
    }
    await user.click(screen.getByRole('button', { name: 'Home', exact: true }))
    await screen.findByText('No products in this category.')
    await user.click(screen.getByRole('button', { name: 'Animals', exact: true }))
    await screen.findByText('Product animals')
    expect(screen.getAllByText(/^Product /)).toHaveLength(1)
  })

  it('keeps the selected category when an older request completes later', async () => {
    let resolveAnimals
    let animalsSignal
    let animalsRequests = 0
    getAllProducts.mockImplementation((category, { signal }) => {
      if (category === 'animals') {
        if (animalsRequests++ === 0) return Promise.resolve({ data: [products[0]] })
        animalsSignal = signal
        return new Promise((resolve) => { resolveAnimals = resolve })
      }
      return Promise.resolve({ data: [products[1]] })
    })
    const user = userEvent.setup()
    renderCatalog(Page)
    await screen.findByText('Product animals')
    await user.click(screen.getByRole('button', { name: 'Wall', exact: true }))
    await screen.findByText('Product wall')
    await user.click(screen.getByRole('button', { name: 'Animals', exact: true }))
    await user.click(screen.getByRole('button', { name: 'Wall', exact: true }))
    await screen.findByText('Product wall')
    expect(animalsSignal.aborted).toBe(true)
    await act(async () => { resolveAnimals({ data: [products[0]] }) })
    expect(screen.queryByText('Product animals')).toBeNull()
    expect(screen.getByText('Product wall')).toBeTruthy()
  })

  it('recovers from a failed category request when another category is selected', async () => {
    getAllProducts.mockRejectedValueOnce(new Error('Offline'))
    const user = userEvent.setup()
    renderCatalog(Page)
    await screen.findByText('Unable to load products.')
    await user.click(screen.getByRole('button', { name: 'Wall', exact: true }))
    await screen.findByText('Product wall')
    expect(screen.queryByText('Unable to load products.')).toBeNull()
  })
})

describe('admin categories', () => {
  it('deletes a product in the selected category and keeps category tabs usable', async () => {
    let resolveDeletion
    deleteProduct.mockImplementation(() => new Promise((resolve) => { resolveDeletion = resolve }))
    const user = userEvent.setup()
    renderCatalog(AdminPage)
    await screen.findByText('Product animals')
    await user.click(screen.getByRole('button', { name: 'Delete', exact: true }))
    const modal = screen.getByRole('heading', { name: 'Delete this product?' }).parentElement
    await user.click(within(modal).getByRole('button', { name: 'Delete', exact: true }))
    expect(deleteProduct).toHaveBeenCalledWith(products[0].id)
    const menu = screen.getByRole('navigation', { name: 'Product categories' })
    expect(within(menu).getAllByRole('button').every((button) => button.disabled)).toBe(true)
    await act(async () => { resolveDeletion({ data: { message: 'Product deleted' } }) })
    await screen.findByText('No products in this category.')
    expect(within(menu).getAllByRole('button').every((button) => !button.disabled)).toBe(true)
    await user.click(screen.getByRole('button', { name: 'Wall', exact: true }))
    await screen.findByText('Product wall')
  })

  it('requires a category and sends the selected value when creating a product', async () => {
    const user = userEvent.setup()
    renderAdmin(ProductCreatePage, '/admin/products/new')
    const category = screen.getByLabelText('Category')
    expect(category.required).toBe(true)
    expect(category.value).toBe('')
    expect(screen.queryByRole('option', { name: 'All' })).toBeNull()
    await user.type(screen.getByLabelText('Title'), 'Cat figure')
    await user.type(screen.getByLabelText('Price ($)'), '12000')
    await user.click(screen.getByRole('button', { name: 'Save', exact: true }))
    expect(createProduct).not.toHaveBeenCalled()
    await user.selectOptions(category, 'animals')
    await user.type(screen.getByLabelText('Image URL'), 'https://example.com/cat.jpg')
    await user.click(screen.getByRole('button', { name: 'Save', exact: true }))
    await waitFor(() => expect(createProduct).toHaveBeenCalledWith({
      title: 'Cat figure', price: '12000', category: 'animals', description: null, image_url: 'https://example.com/cat.jpg',
    }, null))
    await screen.findByText('Admin list')
  })

  it('sends category alongside the uploaded photo', async () => {
    const user = userEvent.setup()
    renderAdmin(ProductCreatePage, '/admin/products/new')
    await user.type(screen.getByLabelText('Title'), 'Wall relief')
    await user.type(screen.getByLabelText('Price ($)'), '25')
    await user.selectOptions(screen.getByLabelText('Category'), '3d_wall')
    const file = new File(['photo'], 'wall.png', { type: 'image/png' })
    await user.upload(screen.getByLabelText('Photo'), file)
    await user.click(screen.getByRole('button', { name: 'Save', exact: true }))
    await waitFor(() => expect(createProduct).toHaveBeenCalledWith(expect.objectContaining({ category: '3d_wall' }), file))
  })

  it('preselects the existing category and saves a new category', async () => {
    const user = userEvent.setup()
    renderAdmin(ProductEditPage, '/admin/products/1/edit')
    const category = await screen.findByLabelText('Category')
    expect(category.value).toBe('animals')
    await user.selectOptions(category, 'home')
    await user.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(updateProduct).toHaveBeenCalledWith('1', {
      title: products[0].title, price: '12.00', description: products[0].description, category: 'home', image_url: null,
    }, null))
    await screen.findByText('Admin list')
  })
})

it('shows a readable category on the public product details', async () => {
  getProduct.mockResolvedValue({ data: { ...products[0], category: '3d_wall' } })
  render(
    <MemoryRouter initialEntries={['/products/1']}>
      <Routes><Route path="/products/:id" element={<ProductPage />} /></Routes>
    </MemoryRouter>,
  )
  await screen.findByText('3D Wall')
  expect(screen.getByText('$12.00')).toBeTruthy()
})
