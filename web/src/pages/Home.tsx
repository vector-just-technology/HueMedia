import { useEffect, useState } from 'react'
import { api } from '../api'
import type { PlaybackStatus, Artist, ResourceInfo } from '../types'
import CoverArt from '../components/CoverArt'

interface HomeProps {
  status: PlaybackStatus | null
  onPlay: () => void
}

export default function Home({ status, onPlay }: HomeProps) {
  const [artists, setArtists] = useState<Artist[]>([])
  const [resources, setResources] = useState<ResourceInfo | null>(null)

  useEffect(() => {
    api.artists().then(setArtists).catch(() => {})
    api.resources().then(setResources).catch(() => {})
  }, [])

  const track = status?.current
  const isPlaying = status?.state === 'playing'
  const prog = status?.duration && status.duration > 0
    ? ((status.position ?? 0) / status.duration) * 100
    : 0

  return (
    <div>
      {track ? (
        <div style={styles.nowPlaying}>
          <CoverArt path={track.cover} size={200} />
          <h2 style={styles.songTitle}>{track.title}</h2>
          <p style={styles.songArtist}>{track.artist}</p>
          <p style={styles.songAlbum}>{track.album}</p>

          <div style={styles.progressBar}>
            <div style={{ ...styles.progressFill, width: `${prog}%` }} />
          </div>
          <div style={styles.timeRow}>
            <span>{fmtTime(status?.position ?? 0)}</span>
            <span>-{fmtTime((status?.duration ?? 0) - (status?.position ?? 0))}</span>
          </div>

          <div style={styles.controls}>
            <button style={styles.ctrlBtn} onClick={async () => { await api.previous(); onPlay() }}>&#x23EE;</button>
            <button style={{ ...styles.ctrlBtn, ...styles.playBtn }} onClick={async () => { await api.toggle(); onPlay() }}>
              {isPlaying ? '\u23F8' : '\u25B6'}
            </button>
            <button style={styles.ctrlBtn} onClick={async () => { await api.next(); onPlay() }}>&#x23ED;</button>
          </div>
        </div>
      ) : (
        <div style={styles.welcome}>
          <h1 style={styles.welcomeTitle}>HueMedia</h1>
          <p style={styles.welcomeText}>
            Your music, beautifully simple.
            Browse your library or drop files via SAMBA at <code>\\10.0.0.174\MUSIC</code>
          </p>
          <div style={styles.stats}>
            <div style={styles.stat}>
              <span style={styles.statNum}>{artists.length}</span>
              <span style={styles.statLabel}>Artists</span>
            </div>
            <div style={styles.stat}>
              <span style={styles.statNum}>
                {artists.reduce((a, b) => a + (b.count || 0), 0)}
              </span>
              <span style={styles.statLabel}>Tracks</span>
            </div>
            {resources && (
              <div style={{ ...styles.stat, opacity: 0.6 }}>
                <span style={styles.statNum}>{resources.cpu}%</span>
                <span style={styles.statLabel}>CPU</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function fmtTime(s: number) {
  const m = Math.floor(Math.max(0, s) / 60)
  const sec = Math.floor(Math.max(0, s) % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

const styles: Record<string, React.CSSProperties> = {
  nowPlaying: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '20px 0',
  },
  songTitle: {
    fontSize: '1.2rem',
    fontWeight: 700,
    marginTop: '16px',
    textAlign: 'center',
  },
  songArtist: {
    color: '#888',
    marginTop: '4px',
    fontSize: '.95rem',
  },
  songAlbum: {
    color: '#666',
    fontSize: '.8rem',
    marginTop: '2px',
  },
  progressBar: {
    width: '100%',
    maxWidth: '400px',
    height: '6px',
    background: '#2a2a3e',
    borderRadius: '3px',
    marginTop: '20px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #8b5cf6, #3b82f6)',
    borderRadius: '3px',
    transition: 'width .3s',
  },
  timeRow: {
    display: 'flex',
    justifyContent: 'space-between',
    width: '100%',
    maxWidth: '400px',
    fontSize: '.75rem',
    color: '#666',
    marginTop: '4px',
  },
  controls: {
    display: 'flex',
    gap: '16px',
    marginTop: '20px',
    alignItems: 'center',
  },
  ctrlBtn: {
    background: '#2a2a3e',
    border: 'none',
    color: '#e0e0e0',
    fontSize: '1.3rem',
    padding: '12px 16px',
    borderRadius: '50%',
    cursor: 'pointer',
    transition: 'background .2s',
  } as React.CSSProperties,
  playBtn: {
    background: '#8b5cf6',
    padding: '16px 20px',
    fontSize: '1.5rem',
  },
  welcome: {
    textAlign: 'center',
    paddingTop: '60px',
  },
  welcomeTitle: {
    fontSize: '2.5rem',
    background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  welcomeText: {
    color: '#888',
    marginTop: '12px',
    lineHeight: 1.5,
    maxWidth: '400px',
    margin: '12px auto 0',
  },
  stats: {
    display: 'flex',
    justifyContent: 'center',
    gap: '40px',
    marginTop: '40px',
  },
  stat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  statNum: {
    fontSize: '2rem',
    fontWeight: 700,
    color: '#8b5cf6',
  },
  statLabel: {
    fontSize: '.75rem',
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: '1px',
  },
}
