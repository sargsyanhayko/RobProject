export const PRODUCT_CATEGORIES = [
  { value: 'animals', label: 'Animals' },
  { value: 'wall', label: 'Wall' },
  { value: '3d_wall', label: '3D Wall' },
  { value: 'home', label: 'Home' },
  { value: 'other', label: 'Other' },
]

export function getCategoryLabel(category) {
  return PRODUCT_CATEGORIES.find(({ value }) => value === category)?.label || category
}
