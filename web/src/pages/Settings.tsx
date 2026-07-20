import { useState, useEffect } from 'react'
import { api } from '../api'
import type { ResourceInfo } from '../types'

export default function Settings() {
  const [info, setInfo] = useState<Record<string, unknown>>({})
  const [resources, setResources] = useState<ResourceInfo | null>(null)
  const [storage, setStorage] = useState<{ drives: unknown[]; pool: Record<string, unknown> } | null>(null)
  const [logs, setLogs] = useState<string>('')
  const [logService, setLogService] = useState('hue-player')

  useEffect(() => {
    api.info().then(setInfo).catch(() => {})
    api.resources().then(setResources).catch(() => {})
    api.storage().then(setStorage).catch(() => {})
  }, [])

  const loadLogs = async (service: string) => {
    setLogService(service)
    try {
      const data = await api.logs(service)
      setLogs(data.logs || 'No logs')
    } catch {
      setLogs('Failed to load logs')
    }
  }

  const fmtBytes = (b: number) => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let i = 0
    let size = b
    while (size >= 1024 && i < units.length - 1) {
      size /= 1024
      i++
    }
    return `${size.toFixed(1)} ${units[i]}`
  }

  return (
    <div>
      <h2 style={styles.pageTitle}>Settings</h2>

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>System</h3>
        <div style={styles.grid}>
          <div style={styles.gridItem}>
            <span style={styles.label}>Hostname</span>
            <span>{info.hostname as string || '-'}</span>
          </div>
          <div style={styles.gridItem}>
            <span style={styles.label}>Platform</span>
            <span>{info.platform as string || '-'}</span>
          </div>
          {resources && (
            <>
              <div style={styles.gridItem}>
                <span style={styles.label}>CPU</span>
                <span>{resources.cpu}%</span>
              </div>
              <div style={styles.gridItem}>
                <span style={styles.label}>Memory</span>
                <span>{resources.memory.percent}%</span>
              </div>
              {resources.temperature !== null && (
                <div style={styles.gridItem}>
                  <span style={styles.label}>Temp</span>
                  <span>{resources.temperature}&deg;C</span>
                </div>
              )}
            </>
          )}
        </div>
      </section>

      {storage && (
        <section style={styles.section}>
          <h3 style={styles.sectionTitle}>Storage</h3>
          {(storage.drives as Array<{ name: string; total: number; free: number; mounted: boolean }>).map((d) => (
            <div key={d.name} style={styles.storageRow}>
              <span>{d.name}</span>
              <span style={{ color: '#888', fontSize: '.8rem' }}>
                {fmtBytes(d.free)} free / {fmtBytes(d.total)}
              </span>
            </div>
          ))}
        </section>
      )}

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Logs</h3>
        <div style={styles.logServiceRow}>
          {['hue-player', 'hue-api', 'hue-bluetooth'].map((s) => (
            <button
              key={s}
              style={{
                ...styles.logServiceBtn,
                ...(logService === s ? styles.logServiceBtnActive : {}),
              }}
              onClick={() => loadLogs(s)}
            >
              {s.replace('hue-', '')}
            </button>
          ))}
        </div>
        <pre style={styles.logOutput}>{logs || 'Select a service'}</pre>
      </section>

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Power</h3>
        <div style={styles.powerRow}>
          <button style={{ ...styles.powerBtn, background: '#ef4444' }} onClick={async () => { await api.reboot() }}>
            Reboot
          </button>
          <button style={{ ...styles.powerBtn, background: '#dc2626' }} onClick={async () => { await api.shutdown() }}>
            Shutdown
          </button>
        </div>
      </section>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  pageTitle: {
    fontSize: '1.4rem',
    fontWeight: 700,
    marginBottom: '20px',
  },
  section: {
    marginBottom: '24px',
  },
  sectionTitle: {
    fontSize: '.85rem',
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    marginBottom: '12px',
  },
  grid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    background: '#1a1a2e',
    borderRadius: '10px',
    padding: '12px 16px',
    border: '1px solid #2a2a3e',
  },
  gridItem: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '.85rem',
    padding: '6px 0',
    borderBottom: '1px solid #2a2a3e',
  } as React.CSSProperties,
  label: {
    color: '#888',
  },
  storageRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 16px',
    background: '#1a1a2e',
    border: '1px solid #2a2a3e',
    marginBottom: '4px',
    fontSize: '.85rem',
  },
  logServiceRow: {
    display: 'flex',
    gap: '4px',
    marginBottom: '8px',
  },
  logServiceBtn: {
    background: '#1a1a2e',
    border: '1px solid #2a2a3e',
    color: '#888',
    padding: '6px 14px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '.8rem',
  },
  logServiceBtnActive: {
    background: '#8b5cf6',
    color: '#fff',
    borderColor: '#8b5cf6',
  },
  logOutput: {
    background: '#0a0a14',
    borderRadius: '8px',
    padding: '12px',
    fontFamily: 'monospace',
    fontSize: '.75rem',
    lineHeight: 1.5,
    maxHeight: '200px',
    overflow: 'auto',
    whiteSpace: 'pre-wrap',
    color: '#ccc',
  },
  powerRow: {
    display: 'flex',
    gap: '12px',
  },
  powerBtn: {
    flex: 1,
    border: 'none',
    color: '#fff',
    padding: '12px',
    borderRadius: '10px',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: '.9rem',
  },
}
