import { useState, useCallback } from 'react'
import { api } from '../api'
import type { Track } from '../types'
import CoverArt from '../components/CoverArt'

interface SearchProps {
  onPlay: () => void
}

export default function Search({ onPlay }: SearchProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Track[]>([])
  const [searching, setSearching] = useState(false)

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([])
      return
    }
    setSearching(true)
    try {
      const data = await api.search(q)
      setResults(data)
    } catch {}
    setSearching(false)
  }, [])

  const playTrack = async (track: Track) => {
    try {
      await api.playById(track.id)
      onPlay()
    } catch {}
  }

  return (
    <div>
      <div style={styles.searchBox}>
        <input
          style={styles.input}
          placeholder="Search artists, songs, albums..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            doSearch(e.target.value)
          }}
          autoFocus
        />
      </div>

      {searching && <p style={{ color: '#888', textAlign: 'center' }}>Searching...</p>}

      {results.length === 0 && query && !searching && (
        <p style={{ color: '#666', textAlign: 'center', marginTop: '40px' }}>
          No results for "{query}"
        </p>
      )}

      <div style={styles.results}>
        {results.map((track) => (
          <div key={track.id} style={styles.item} onClick={() => playTrack(track)}>
            <CoverArt path={track.cover} size={36} />
            <div style={styles.info}>
              <div style={styles.title}>{track.title}</div>
              <div style={styles.meta}>{track.artist} &middot; {track.album}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  searchBox: {
    marginBottom: '16px',
  },
  input: {
    width: '100%',
    padding: '14px 16px',
    borderRadius: '12px',
    border: '1px solid #2a2a3e',
    background: '#1a1a2e',
    color: '#e0e0e0',
    fontSize: '1rem',
    outline: 'none',
    boxSizing: 'border-box',
  } as React.CSSProperties,
  results: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  item: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px',
    background: '#1a1a2e',
    borderRadius: '10px',
    cursor: 'pointer',
    border: '1px solid #2a2a3e',
  },
  info: {
    flex: 1,
    minWidth: 0,
  },
  title: {
    fontWeight: 600,
    fontSize: '.9rem',
  },
  meta: {
    color: '#888',
    fontSize: '.75rem',
  },
}
