import { useState } from 'react'
import { api } from '../api'
import type { PlaybackStatus } from '../types'

interface PlayerBarProps {
  status: PlaybackStatus | null
  onUpdate: () => void
}

export default function PlayerBar({ status, onUpdate }: PlayerBarProps) {
  const [vol, setVol] = useState<number>(80)

  const track = status?.current
  const isPlaying = status?.state === 'playing'
  const pos = status?.position ?? 0
  const dur = status?.duration ?? 0
  const prog = dur > 0 ? (pos / dur) * 100 : 0

  const fmt = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  const handleToggle = async () => {
    await api.toggle()
    onUpdate()
  }

  const handleNext = async () => {
    await api.next()
    onUpdate()
  }

  const handlePrev = async () => {
    await api.previous()
    onUpdate()
  }

  const handleSeek = async (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const pct = (e.clientX - rect.left) / rect.width
    await api.seek(pct * dur)
    onUpdate()
  }

  const handleVolume = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = parseInt(e.target.value)
    setVol(v)
    await api.volume(v)
  }

  if (!track) {
    return (
      <div style={styles.bar}>
        <span style={{ color: '#666', fontSize: '.9rem' }}>No track playing</span>
      </div>
    )
  }

  return (
    <div style={styles.bar}>
      <div style={styles.row}>
        <div style={styles.cover}>
          {track.cover
            ? <img src={`/api/music/cover?path=${encodeURIComponent(track.cover)}`} alt="" style={styles.coverImg} />
            : <div style={styles.coverPlaceholder} />
          }
        </div>
        <div style={styles.info}>
          <div style={styles.title}>{track.title}</div>
          <div style={styles.artist}>{track.artist}</div>
        </div>
        <div style={styles.controls}>
          <button style={styles.btn} onClick={handlePrev}>&#x23EE;</button>
          <button style={{ ...styles.btn, ...styles.playBtn }} onClick={handleToggle}>
            {isPlaying ? '\u23F8' : '\u25B6'}
          </button>
          <button style={styles.btn} onClick={handleNext}>&#x23ED;</button>
        </div>
        <div style={styles.volumeWrap}>
          <input
            type="range"
            min="0"
            max="100"
            value={vol}
            onChange={handleVolume}
            style={styles.volumeSlider}
          />
        </div>
      </div>
      <div style={styles.progress} onClick={handleSeek}>
        <div style={{ ...styles.progressFill, width: `${prog}%` }} />
        <div style={styles.time}>
          <span>{fmt(pos)}</span>
          <span>-{fmt(dur - pos)}</span>
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  bar: {
    position: 'fixed',
    bottom: '56px',
    left: 0,
    right: 0,
    background: '#1a1a2e',
    borderTop: '1px solid #2a2a3e',
    padding: '8px 16px',
    paddingBottom: 'calc(8px + env(safe-area-inset-bottom, 0px))',
  },
  row: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  cover: {
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
    width: '100%',
    height: '100%',
    background: '#2a2a3e',
    borderRadius: '6px',
  },
  info: {
    flex: 1,
    minWidth: 0,
  },
  title: {
    fontSize: '.85rem',
    fontWeight: 600,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  artist: {
    fontSize: '.75rem',
    color: '#888',
  },
  controls: {
    display: 'flex',
    gap: '4px',
    flexShrink: 0,
  },
  btn: {
    background: 'transparent',
    border: 'none',
    color: '#e0e0e0',
    fontSize: '1.2rem',
    cursor: 'pointer',
    padding: '6px 8px',
    borderRadius: '50%',
    transition: 'background .2s',
  } as React.CSSProperties,
  playBtn: {
    fontSize: '1.4rem',
    color: '#8b5cf6',
  },
  volumeWrap: {
    display: 'flex',
    alignItems: 'center',
    flexShrink: 0,
  },
  volumeSlider: {
    width: '60px',
    accentColor: '#8b5cf6',
  },
  progress: {
    height: '4px',
    background: '#2a2a3e',
    borderRadius: '2px',
    marginTop: '8px',
    cursor: 'pointer',
    position: 'relative',
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #8b5cf6, #3b82f6)',
    borderRadius: '2px',
    transition: 'width .3s',
  },
  time: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '.65rem',
    color: '#666',
    marginTop: '2px',
  },
}
