import { useState, useEffect } from 'react'
import { api } from '../api'
import type { StreamTrack } from '../types'

interface DownloadsProps {
  onPlay: () => void
}

export default function Downloads({ onPlay }: DownloadsProps) {
  const [tracks, setTracks] = useState<StreamTrack[]>([])
  const [loading, setLoading] = useState(true)

  const loadTracks = async () => {
    setLoading(true)
    try {
      const data = await api.streamDownloads()
      setTracks(data.tracks)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { loadTracks() }, [])

  const playSaved = async (track: StreamTrack) => {
    if (!track.path) return
    try {
      await api.play(track.path)
      onPlay()
    } catch {}
  }

  const removeTrack = async (track: StreamTrack) => {
    try {
      await api.streamRemoveDownload(track.id)
      setTracks(tracks.filter(t => t.id !== track.id))
    } catch {}
  }

  if (loading) {
    return <p style={{ color: '#888', textAlign: 'center' }}>Loading...</p>
  }

  return (
    <div>
      <div style={styles.header}>
        <h2 style={styles.title}>Saved Streams</h2>
        {tracks.length > 0 && (
          <span style={styles.count}>{tracks.length} track{tracks.length !== 1 ? 's' : ''}</span>
        )}
      </div>

      {tracks.length === 0 && (
        <p style={{ color: '#666', textAlign: 'center', marginTop: '40px' }}>
          No saved tracks yet. Search and save from the Stream page.
        </p>
      )}

      <div style={styles.list}>
        {tracks.map((track) => (
          <div key={track.id} style={styles.card}>
            <div style={styles.cardCover}>
              {track.cover
                ? <img src={`/api/music/cover?path=${encodeURIComponent(track.cover)}`} alt="" style={styles.coverImg} />
                : <div style={styles.coverPlaceholder} />
              }
            </div>
            <div style={styles.cardInfo}>
              <div style={styles.cardTitle}>{track.title}</div>
              <div style={styles.cardMeta}>{track.artist}</div>
            </div>
            <div style={styles.cardActions}>
              <button style={styles.actionBtn} onClick={() => playSaved(track)} title="Play">
                {'\u25B6'}
              </button>
              <button style={{ ...styles.actionBtn, color: '#ef4444' }} onClick={() => removeTrack(track)} title="Remove">
                {'\u2716'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '16px',
  },
  title: {
    margin: 0,
    fontSize: '1.1rem',
  },
  count: {
    color: '#888',
    fontSize: '.8rem',
  },
  list: {
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
