import { useState, useEffect, useCallback } from 'react'
import { api } from '../api'
import type { PlaybackStatus, BluetoothStatus, ResourceInfo, Artist } from '../types'

export function usePlayback(interval = 2000) {
  const [status, setStatus] = useState<PlaybackStatus | null>(null)

  const refresh = useCallback(async () => {
    try {
      const s = await api.playback()
      setStatus(s)
    } catch {}
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, interval)
    return () => clearInterval(id)
  }, [refresh, interval])

  return { status, refresh }
}

export function useBluetooth(interval = 5000) {
  const [status, setStatus] = useState<BluetoothStatus | null>(null)

  const refresh = useCallback(async () => {
    try {
      const s = await api.bluetooth()
      setStatus(s)
    } catch {}
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, interval)
    return () => clearInterval(id)
  }, [refresh, interval])

  return { status, refresh }
}

export function useLibrary() {
  const [artists, setArtists] = useState<Artist[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.artists()
      setArtists(data)
    } catch {}
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  return { artists, loading, refresh: load }
}

export function useResources(interval = 10000) {
  const [resources, setResources] = useState<ResourceInfo | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const r = await api.resources()
        setResources(r)
      } catch {}
    }
    load()
    const id = setInterval(load, interval)
    return () => clearInterval(id)
  }, [interval])

  return resources
}
