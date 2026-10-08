export const PRODUCT_CATEGORIES = [
  { value: 'animals', label: 'Backdrops' },
  { value: 'wall', label: 'Shop/Storefront Backdrops' },
  { value: '3d_wall', label: 'Animals' },
  { value: 'home', label: 'Candles' },
  { value: 'other', label: 'Cake stands' },
]

export function getCategoryLabel(category) {
  return PRODUCT_CATEGORIES.find(({ value }) => value === category)?.label || category
}
