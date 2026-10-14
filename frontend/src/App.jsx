import { useEffect, useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [text, setText] = useState('')
  const [entries, setEntries] = useState([])
  const [selected, setSelected] = useState(null)
  const [tagFilter, setTagFilter] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [listLoading, setListLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchEntries = async () => {
    setListLoading(true)
    try {
      const res = await fetch(`${API_BASE}/entries`)
      if (!res.ok) throw new Error('Failed to load entries')
      setEntries(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setListLoading(false)
    }
  }

  useEffect(() => {
    fetchEntries()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/entries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Something went wrong generating the summary.')
      }
      setText('')
      await fetchEntries()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const allTags = [...new Set(entries.flatMap((e) => e.tags))]
  const visibleEntries = tagFilter
    ? entries.filter((e) => e.tags.includes(tagFilter))
    : entries

  return (
    <div className="app">
      <h1>AI Content Assistant</h1>

      <form className="entry-form" onSubmit={handleSubmit}>
        <textarea
          placeholder="Paste a note, article draft, or meeting transcript..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={20000}
          rows={6}
          disabled={submitting}
        />
        <button type="submit" disabled={submitting || !text.trim()}>
          {submitting ? 'Summarizing...' : 'Summarize'}
        </button>
        {error && <p className="error">{error}</p>}
      </form>

      {allTags.length > 0 && (
        <div className="tag-filter">
          <span>Filter by tag:</span>
          <button
            className={tagFilter === null ? 'tag active' : 'tag'}
            onClick={() => setTagFilter(null)}
          >
            all
          </button>
          {allTags.map((tag) => (
            <button
              key={tag}
              className={tagFilter === tag ? 'tag active' : 'tag'}
              onClick={() => setTagFilter(tag)}
            >
              {tag}
            </button>
          ))}
        </div>
      )}

      <div className="layout">
        <div className="entry-list">
          {listLoading && <p>Loading entries...</p>}
          {!listLoading && visibleEntries.length === 0 && <p>No entries yet.</p>}
          {visibleEntries.map((entry) => (
            <div
              key={entry.id}
              className={`entry-card ${entry.status} ${selected?.id === entry.id ? 'selected' : ''}`}
              onClick={() => setSelected(entry)}
            >
              <p className="summary">
                {entry.status === 'failed' ? `Failed: ${entry.error_message}` : entry.summary}
              </p>
              <div className="tags">
                {entry.tags.map((t) => (
                  <span key={t} className="tag-pill">{t}</span>
                ))}
              </div>
            </div>
          ))}
        </div>

        {selected && (
          <div className="entry-detail">
            <button className="close" onClick={() => setSelected(null)}>x</button>
            <h2>Entry #{selected.id}</h2>
            <p className="meta">{new Date(selected.created_at).toLocaleString()}</p>
            <h3>Summary</h3>
            <p>{selected.summary || '(none — generation failed)'}</p>
            <h3>Tags</h3>
            <div className="tags">
              {selected.tags.map((t) => (
                <span key={t} className="tag-pill">{t}</span>
              ))}
            </div>
            <h3>Original text</h3>
            <p className="original-text">{selected.original_text}</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
