import { useState, useEffect, useCallback } from 'react'
import { api } from './api'
import type { PlaybackStatus } from './types'
import Layout from './components/Layout'
import PlayerBar from './components/PlayerBar'
import Home from './pages/Home'
import Library from './pages/Library'
import Search from './pages/Search'
import Bluetooth from './pages/Bluetooth'
import Settings from './pages/Settings'
import Terminal from './pages/Terminal'

type Page = 'home' | 'library' | 'search' | 'bluetooth' | 'settings' | 'terminal'

export default function App() {
  const [page, setPage] = useState<Page>('home')
  const [status, setStatus] = useState<PlaybackStatus | null>(null)

  const refreshStatus = useCallback(async () => {
    try {
      const s = await api.playback()
      setStatus(s)
    } catch {
      // server not ready yet
    }
  }, [])

  useEffect(() => {
    refreshStatus()
    const interval = setInterval(refreshStatus, 2000)
    return () => clearInterval(interval)
  }, [refreshStatus])

  const pages: Record<Page, React.ReactNode> = {
    home: <Home status={status} onPlay={refreshStatus} />,
    library: <Library onPlay={refreshStatus} />,
    search: <Search onPlay={refreshStatus} />,
    bluetooth: <Bluetooth />,
    settings: <Settings />,
    terminal: <Terminal />,
  }

  return (
    <Layout currentPage={page} onNavigate={setPage}>
      {pages[page]}
      <PlayerBar status={status} onUpdate={refreshStatus} />
    </Layout>
  )
}
