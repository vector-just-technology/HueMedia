import type { PlaybackStatus, Artist, Track, BluetoothStatus, ResourceInfo, StorageInfo } from './types'

const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`)
  return res.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`)
  return res.json()
}

export const api = {
  // Status
  status: () => get<{ status: string; playing: PlaybackStatus; library: { artists: number; tracks: number } }>('/status'),

  // Music
  artists: () => get<Artist[]>('/music/artists'),
  artist: (name: string) => get<Artist>(`/music/artists/${encodeURIComponent(name)}`),
  tracks: (params?: { artist?: string; album?: string; q?: string }) => {
    const qs = new URLSearchParams()
    if (params?.artist) qs.set('artist', params.artist)
    if (params?.album) qs.set('album', params.album)
    if (params?.q) qs.set('q', params.q)
    const q = qs.toString()
    return get<Track[]>(`/music/tracks${q ? `?${q}` : ''}`)
  },
  search: (q: string) => get<Track[]>(`/music/search?q=${encodeURIComponent(q)}`),
  rescan: () => post('/music/rescan'),

  // Playback
  playback: () => get<PlaybackStatus>('/playback/status'),
  play: (path: string) => post('/playback/play', { path }),
  playById: (id: number) => post(`/playback/play/${id}`),
  toggle: () => post<PlaybackStatus>('/playback/toggle'),
  stop: () => post('/playback/stop'),
  next: () => post('/playback/next'),
  previous: () => post('/playback/previous'),
  seek: (position: number) => post('/playback/seek', { position }),
  volume: (vol?: number) => vol !== undefined ? post<{ volume: number }>('/playback/volume', { volume: vol }) : get<{ volume: number }>('/playback/volume'),
  shuffle: () => post('/playback/shuffle'),
  repeat: () => post('/playback/repeat'),
  queue: (trackIds?: number[]) => trackIds ? post('/playback/queue', { track_ids: trackIds }) : get('/playback/queue'),
  clearQueue: () => post('/playback/queue/clear'),

  // Bluetooth
  bluetooth: () => get<BluetoothStatus>('/bluetooth/status'),
  btScan: (stop?: boolean) => post('/bluetooth/scan', { stop }),
  btPair: (mac: string) => post('/bluetooth/pair', { mac }),
  btConnect: (mac: string) => post('/bluetooth/connect', { mac }),
  btDisconnect: () => post('/bluetooth/disconnect'),
  btForget: (mac: string) => post('/bluetooth/forget', { mac }),

  // System
  info: () => get('/system/info'),
  resources: () => get<ResourceInfo>('/system/resources'),
  storage: () => get<StorageInfo>('/system/storage'),
  reboot: () => post('/system/reboot'),
  shutdown: () => post('/system/shutdown'),
  config: (cfg?: Record<string, unknown>) => cfg ? post('/system/config', cfg) : get('/system/config'),
  shell: (cmd: string) => post('/system/shell', { cmd }),
  logs: (service: string) => get(`/system/logs/${service}`),
  plugins: () => get('/system/plugins'),
}
