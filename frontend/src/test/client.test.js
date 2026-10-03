import { beforeEach, expect, it, vi } from 'vitest'
import api, { createProduct, getAllProducts, getProducts, updateProduct } from '../api/client'

let adapter

beforeEach(() => {
  adapter = vi.fn(async (config) => ({
    data: [], status: 200, statusText: 'OK', headers: {}, config,
  }))
  api.defaults.adapter = adapter
})

it('omits an unspecified category and sends each API category unchanged', async () => {
  for (const category of [undefined, 'animals', 'wall', '3d_wall', 'home', 'other']) {
    await getProducts(category)
    const config = adapter.mock.calls.at(-1)[0]
    expect(config.url).toBe('/api/products')
    expect(config.params.category).toBe(category)
    expect(config.baseURL).toBe(api.defaults.baseURL)
  }
})

it('loads the full selected category beyond the first hundred products', async () => {
  const products = Array.from({ length: 205 }, (_, index) => ({ id: index + 1, category: 'animals' }))
  adapter.mockImplementation(async (config) => ({
    data: products.slice(config.params.skip, config.params.skip + config.params.limit),
    status: 200, statusText: 'OK', headers: {}, config,
  }))
  const result = await getAllProducts('animals')
  expect(result.data).toEqual(products)
  expect(adapter.mock.calls.map(([config]) => config.params)).toEqual([
    { category: 'animals', skip: 0, limit: 100 },
    { category: 'animals', skip: 100, limit: 100 },
    { category: 'animals', skip: 200, limit: 100 },
  ])
})

it('stops fetching pages when the selected category request is aborted', async () => {
  const controller = new AbortController()
  adapter.mockImplementation(async (config) => {
    controller.abort()
    return { data: Array(100).fill({ category: 'animals' }), status: 200, headers: {}, config }
  })
  await expect(getAllProducts('animals', { signal: controller.signal })).rejects.toMatchObject({ code: 'ERR_CANCELED' })
  expect(adapter).toHaveBeenCalledTimes(1)
})

it('preserves Bearer auth and includes category in JSON and multipart mutations', async () => {
  localStorage.setItem('admin_token', 'test-jwt')
  const product = { title: 'Cat figure', price: '12.00', description: 'Cat', category: 'animals' }
  await createProduct(product)
  let config = adapter.mock.calls.at(-1)[0]
  expect(JSON.parse(config.data).category).toBe('animals')
  expect(config.headers.Authorization).toBe('Bearer test-jwt')
  const image = new File(['photo'], 'cat.png', { type: 'image/png' })
  await createProduct(product, image)
  config = adapter.mock.calls.at(-1)[0]
  expect(config.url).toBe('/api/admin/products/upload')
  expect(config.data.get('category')).toBe('animals')
  expect(config.data.get('file')).toBe(image)
  await updateProduct(1, { ...product, category: 'wall' }, image)
  config = adapter.mock.calls.at(-1)[0]
  expect(config.url).toBe('/api/admin/products/1/upload')
  expect(config.data.get('category')).toBe('wall')
  expect(config.headers.Authorization).toBe('Bearer test-jwt')
})
