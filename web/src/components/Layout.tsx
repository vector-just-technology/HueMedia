import type { ReactNode } from 'react'

const navItems: { id: string; label: string; icon: string }[] = [
  { id: 'home', label: 'Home', icon: '\u2302' },
  { id: 'library', label: 'Library', icon: '\u266B' },
  { id: 'search', label: 'Search', icon: '\u2315' },
  { id: 'stream', label: 'Stream', icon: '\u25CF' },
  { id: 'downloads', label: 'Saved', icon: '\u2B07' },
  { id: 'bluetooth', label: 'Bluetooth', icon: '\u2248' },
  { id: 'settings', label: 'Settings', icon: '\u2699' },
  { id: 'terminal', label: 'Terminal', icon: '\u276F' },
]

interface LayoutProps {
  currentPage: string
  onNavigate: (page: string) => void
  children: ReactNode
}

export default function Layout({ currentPage, onNavigate, children }: LayoutProps) {
  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <span style={styles.logo}>HueMedia</span>
        <span style={styles.version}>v1.0</span>
      </header>
      <main style={styles.main}>
        {children}
      </main>
      <nav style={styles.nav}>
        {navItems.map(item => (
          <button
            key={item.id}
            style={{
              ...styles.navBtn,
              ...(currentPage === item.id ? styles.navBtnActive : {}),
            }}
            onClick={() => onNavigate(item.id)}
          >
            <span style={styles.navIcon}>{item.icon}</span>
            <span style={styles.navLabel}>{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: '#0f0f1a',
    color: '#e0e0e0',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 20px',
    background: '#1a1a2e',
    borderBottom: '1px solid #2a2a3e',
  },
  logo: {
    fontSize: '1.3rem',
    fontWeight: 700,
    background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  version: {
    fontSize: '.8rem',
    color: '#666',
  },
  main: {
    flex: 1,
    overflow: 'auto',
    padding: '16px',
    paddingBottom: '100px',
  },
  nav: {
    display: 'flex',
    background: '#1a1a2e',
    borderTop: '1px solid #2a2a3e',
    padding: '4px 0',
    paddingBottom: 'env(safe-area-inset-bottom, 4px)',
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
  },
  navBtn: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '2px',
    padding: '8px 4px',
    border: 'none',
    background: 'transparent',
    color: '#888',
    cursor: 'pointer',
    fontSize: '.75rem',
    transition: 'color .2s',
  },
  navBtnActive: {
    color: '#8b5cf6',
  },
  navIcon: {
    fontSize: '1.2rem',
  },
  navLabel: {
    fontSize: '.65rem',
    textTransform: 'uppercase',
    letterSpacing: '.5px',
  },
}
