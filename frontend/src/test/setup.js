import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

URL.createObjectURL = vi.fn(() => 'blob:product-photo')
URL.revokeObjectURL = vi.fn()

afterEach(() => {
  cleanup()
  localStorage.clear()
})
