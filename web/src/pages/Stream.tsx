import { useState, useCallback } from 'react'
import { api } from '../api'
import type { StreamTrack } from '../types'

interface StreamProps {
  onPlay: () => void
}

export default function Stream({ onPlay }: StreamProps) {
  const [query, setQuery] = useState('')
  const [source, setSource] = useState<'youtube' | 'spotify'>('youtube')
  const [results, setResults] = useState<StreamTrack[]>([])
  const [searching, setSearching] = useState(false)
  const [downloading, setDownloading] = useState<string | null>(null)

  const doSearch = useCallback(async (q: string, src: string) => {
    if (!q.trim()) { setResults([]); return }
    setSearching(true)
    try {
      const data = await api.streamSearch(q, src)
      setResults(data.results)
    } catch {}
    setSearching(false)
  }, [])

  const playStream = async (track: StreamTrack) => {
    try {
      await api.streamPlay(track.url, track.source, track.title, track.artist, track.cover, track.is_video)
      onPlay()
    } catch {}
  }

  const downloadTrack = async (track: StreamTrack) => {
    setDownloading(track.id)
    try {
      await api.streamDownload(track.url, track.source, track.title, track.artist, track.cover, track.is_video)
    } catch {}
    setDownloading(null)
  }

  const fmt = (s: number) => {
    if (!s) return ''
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  return (
    <div>
      <div style={styles.tabs}>
        <button
          style={{ ...styles.tab, ...(source === 'youtube' ? styles.tabActive : {}) }}
          onClick={() => { setSource('youtube'); doSearch(query, 'youtube') }}
        >
          YouTube
        </button>
        <button
          style={{ ...styles.tab, ...(source === 'spotify' ? styles.tabActive : {}) }}
          onClick={() => { setSource('spotify'); doSearch(query, 'spotify') }}
        >
          Spotify
        </button>
      </div>

      <div style={styles.searchBox}>
        <input
          style={styles.input}
          placeholder={source === 'youtube' ? 'Search YouTube...' : 'Search Spotify...'}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            doSearch(e.target.value, source)
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
          <div key={track.id} style={styles.card}>
            <div style={styles.cardCover}>
              {track.cover
                ? <img src={track.cover} alt="" style={styles.coverImg}
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
                : <div style={styles.coverPlaceholder} />
              }
            </div>
            <div style={styles.cardInfo}>
              <div style={styles.cardTitle}>{track.title}</div>
              <div style={styles.cardMeta}>
                {track.artist}{track.duration ? ` · ${fmt(track.duration)}` : ''}
              </div>
            </div>
            <div style={styles.cardActions}>
              <button style={styles.actionBtn} onClick={() => playStream(track)} title="Play">
                {'\u25B6'}
              </button>
              <button
                style={styles.actionBtn}
                onClick={() => downloadTrack(track)}
                disabled={downloading === track.id}
                title="Save to library"
              >
                {downloading === track.id ? '\u23F3' : '\u2B07'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  tabs: {
    display: 'flex',
    gap: '8px',
    marginBottom: '12px',
  },
  tab: {
    flex: 1,
    padding: '10px',
    borderRadius: '10px',
    border: '1px solid #2a2a3e',
    background: '#1a1a2e',
    color: '#888',
    fontSize: '.9rem',
    fontWeight: 600,
    cursor: 'pointer',
    textAlign: 'center',
  },
  tabActive: {
    background: '#2a2a3e',
    color: '#8b5cf6',
    borderColor: '#8b5cf6',
  },
  searchBox: {
    marginBottom: '12px',
  },
  input: {
    width: '100%',
    padding: '12px 14px',
    borderRadius: '10px',
    border: '1px solid #2a2a3e',
    background: '#1a1a2e',
    color: '#e0e0e0',
    fontSize: '.95rem',
    outline: 'none',
    boxSizing: 'border-box',
  } as React.CSSProperties,
  results: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  card: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '8px',
    background: '#1a1a2e',
    borderRadius: '10px',
    border: '1px solid #2a2a3e',
  },
  cardCover: {
    width: '40px',
    height: '40px',
    borderRadius: '6px',
    overflow: 'hidden',
    flexShrink: 0,
  },
  coverImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  coverPlaceholder: {
    width: '40px',
    height: '40px',
    background: '#2a2a3e',
    borderRadius: '6px',
  },
  cardInfo: {
    flex: 1,
    minWidth: 0,
  },
  cardTitle: {
    fontSize: '.85rem',
    fontWeight: 600,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  cardMeta: {
    fontSize: '.7rem',
    color: '#888',
  },
  cardActions: {
    display: 'flex',
    gap: '4px',
    flexShrink: 0,
  },
  actionBtn: {
    background: 'transparent',
    border: 'none',
    color: '#e0e0e0',
    fontSize: '1.1rem',
    cursor: 'pointer',
    padding: '6px 8px',
    borderRadius: '50%',
  } as React.CSSProperties,
}
