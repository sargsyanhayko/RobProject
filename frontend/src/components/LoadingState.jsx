export default function LoadingState({ text = 'Loading…' }) {
  return (
    <div className="loading">
      <div className="spinner" style={{ marginRight: 12 }} />
      {text}
    </div>
  )
}
