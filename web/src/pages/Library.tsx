import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Artist, Track } from '../types'
import CoverArt from '../components/CoverArt'

interface LibraryProps {
  onPlay: () => void
}

export default function Library({ onPlay }: LibraryProps) {
  const [artists, setArtists] = useState<Artist[]>([])
  const [selectedArtist, setSelectedArtist] = useState<Artist | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadArtists()
  }, [])

  const loadArtists = async () => {
    setLoading(true)
    try {
      const data = await api.artists()
      setArtists(data)
    } catch {}
    setLoading(false)
  }

  const selectArtist = async (name: string) => {
    try {
      const a = await api.artist(name)
      setSelectedArtist(a)
    } catch {}
  }

  const playTrack = async (track: Track) => {
    try {
      await api.playById(track.id)
      onPlay()
    } catch {}
  }

  if (loading) {
    return <div style={{ color: '#888', textAlign: 'center', paddingTop: '40px' }}>Scanning library...</div>
  }

  if (selectedArtist) {
    return (
      <div>
        <button style={styles.backBtn} onClick={() => setSelectedArtist(null)}>
          &#x2190; Back
        </button>
        <h2 style={styles.artistTitle}>{selectedArtist.name}</h2>
        <div style={styles.songList}>
          {selectedArtist.songs.map((song) => (
            <div key={song.id} style={styles.songItem} onClick={() => playTrack(song)}>
              <CoverArt path={song.cover} size={36} />
              <div style={styles.songInfo}>
                <div style={styles.songName}>{song.title}</div>
                <div style={styles.songAlbum}>{song.album}</div>
              </div>
              {song.is_video && <span style={styles.videoBadge}>VIDEO</span>}
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={styles.headerRow}>
        <h2 style={styles.pageTitle}>Library</h2>
        <button style={styles.rescanBtn} onClick={async () => { await api.rescan(); loadArtists() }}>
          Rescan
        </button>
      </div>
      {artists.length === 0 ? (
        <p style={{ color: '#666', textAlign: 'center', marginTop: '40px' }}>
          No music found. Add files via SAMBA at <code>\\10.0.0.174\MUSIC</code>
        </p>
      ) : (
        <div style={styles.artistList}>
          {artists.map((a) => (
            <div key={a.name} style={styles.artistCard} onClick={() => selectArtist(a.name)}>
              <div style={styles.artistName}>{a.name}</div>
              <div style={styles.artistCount}>{a.count} track{a.count !== 1 ? 's' : ''}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  headerRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  pageTitle: {
    fontSize: '1.4rem',
    fontWeight: 700,
  },
  rescanBtn: {
    background: '#8b5cf6',
    border: 'none',
    color: '#fff',
    padding: '8px 16px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: '.8rem',
  },
  backBtn: {
    background: 'transparent',
    border: 'none',
    color: '#8b5cf6',
    fontSize: '1rem',
    cursor: 'pointer',
    marginBottom: '12px',
    padding: 0,
  },
  artistTitle: {
    fontSize: '1.3rem',
    fontWeight: 700,
    marginBottom: '16px',
  },
  artistList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  artistCard: {
    background: '#1a1a2e',
    borderRadius: '12px',
    padding: '16px',
    cursor: 'pointer',
    transition: 'background .2s',
    border: '1px solid #2a2a3e',
  },
  artistName: {
    fontWeight: 600,
    fontSize: '1rem',
  },
  artistCount: {
    color: '#888',
    fontSize: '.8rem',
    marginTop: '4px',
  },
  songList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  songItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    background: '#1a1a2e',
    borderRadius: '10px',
    padding: '10px',
    cursor: 'pointer',
    border: '1px solid #2a2a3e',
  },
  songInfo: {
    flex: 1,
    minWidth: 0,
  },
  songName: {
    fontWeight: 600,
    fontSize: '.9rem',
  },
  songAlbum: {
    color: '#888',
    fontSize: '.75rem',
    marginTop: '2px',
  },
  videoBadge: {
    background: '#3b82f622',
    color: '#3b82f6',
    fontSize: '.65rem',
    fontWeight: 700,
    padding: '2px 6px',
    borderRadius: '4px',
  },
}
