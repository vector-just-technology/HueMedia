import { useEffect, useState } from 'react'
import { api } from '../api'
import type { BluetoothStatus } from '../types'

export default function Bluetooth() {
  const [status, setStatus] = useState<BluetoothStatus | null>(null)

  const refresh = async () => {
    try {
      const s = await api.bluetooth()
      setStatus(s)
    } catch {}
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleScan = async () => {
    await api.btScan(status?.scanning)
    refresh()
  }

  const handlePair = async (mac: string) => {
    await api.btPair(mac)
    setTimeout(refresh, 3000)
  }

  const handleDisconnect = async () => {
    await api.btDisconnect()
    refresh()
  }

  return (
    <div>
      <div style={styles.header}>
        <h2 style={styles.title}>Bluetooth</h2>
        <button style={{ ...styles.scanBtn, ...(status?.scanning ? styles.scanning : {}) }} onClick={handleScan}>
          {status?.scanning ? 'Scanning...' : 'Scan'}
        </button>
      </div>

      {status?.connected ? (
        <div style={styles.connectedCard}>
          <div style={styles.connectedIcon}>&#x1F50A;</div>
          <div style={styles.connectedInfo}>
            <div style={styles.connectedName}>{status.connected.name}</div>
            <div style={styles.connectedMac}>{status.connected.mac}</div>
          </div>
          <button style={styles.disconnectBtn} onClick={handleDisconnect}>Disconnect</button>
        </div>
      ) : (
        <p style={{ color: '#666', fontSize: '.9rem', marginBottom: '16px' }}>
          No device connected
        </p>
      )}

      <h3 style={styles.sectionTitle}>Available Devices</h3>
      <div style={styles.deviceList}>
        {(!status?.available || status.available.length === 0) ? (
          <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            No devices found. Tap Scan to discover.
          </p>
        ) : (
          status.available.map((dev) => (
            <div key={dev.mac} style={styles.deviceCard}>
              <div style={styles.deviceIcon}>&#x1F4F1;</div>
              <div style={styles.deviceInfo}>
                <div style={styles.deviceName}>{dev.name || 'Unknown'}</div>
                <div style={styles.deviceMac}>{dev.mac}</div>
              </div>
              <button style={styles.pairBtn} onClick={() => handlePair(dev.mac)}>
                {status.connected?.mac === dev.mac ? 'Connected' : 'Connect'}
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  title: {
    fontSize: '1.4rem',
    fontWeight: 700,
  },
  scanBtn: {
    background: '#8b5cf6',
    border: 'none',
    color: '#fff',
    padding: '8px 20px',
    borderRadius: '20px',
    cursor: 'pointer',
    fontWeight: 600,
  },
  scanning: {
    background: '#22c55e',
  },
  connectedCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    background: '#1a3a1a',
    borderRadius: '12px',
    padding: '16px',
    marginBottom: '20px',
    border: '1px solid #22c55e33',
  },
  connectedIcon: {
    fontSize: '2rem',
  },
  connectedInfo: {
    flex: 1,
  },
  connectedName: {
    fontWeight: 600,
  },
  connectedMac: {
    color: '#888',
    fontSize: '.8rem',
  },
  disconnectBtn: {
    background: '#ef4444',
    border: 'none',
    color: '#fff',
    padding: '6px 14px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '.8rem',
    fontWeight: 600,
  },
  sectionTitle: {
    fontSize: '1rem',
    color: '#888',
    marginBottom: '12px',
    textTransform: 'uppercase',
    letterSpacing: '1px',
  },
  deviceList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  deviceCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    background: '#1a1a2e',
    borderRadius: '10px',
    padding: '12px',
    border: '1px solid #2a2a3e',
  },
  deviceIcon: {
    fontSize: '1.5rem',
  },
  deviceInfo: {
    flex: 1,
  },
  deviceName: {
    fontWeight: 600,
    fontSize: '.9rem',
  },
  deviceMac: {
    color: '#888',
    fontSize: '.75rem',
  },
  pairBtn: {
    background: '#3b82f6',
    border: 'none',
    color: '#fff',
    padding: '6px 14px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '.8rem',
    fontWeight: 600,
  },
}
