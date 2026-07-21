export interface Track {
  id: number
  path: string
  title: string
  artist: string
  album: string
  cover: string | null
  duration: number
  is_video?: boolean
  source?: string
}

export interface Artist {
  name: string
  count: number
  songs: Track[]
}

export interface PlaybackStatus {
  state: string
  position: number
  duration: number
  volume: number
  shuffle: boolean
  repeat: string
  current: Track | null
  queue: string[]
}

export interface BluetoothDevice {
  mac: string
  name: string
}

export interface BluetoothStatus {
  available: BluetoothDevice[]
  connected: BluetoothDevice | null
  scanning: boolean
}

export interface ResourceInfo {
  cpu: number
  memory: { percent: number; total: number; available: number }
  disk: { total: number; used: number; free: number }
  temperature: number | null
}

export interface StorageInfo {
  drives: { name: string; path: string; total: number; free: number; mounted: boolean }[]
  pool: { total: number; free: number; mounted: boolean }
}

export interface StreamTrack {
  id: string
  title: string
  artist: string
  channel?: string
  album?: string
  duration: number
  url: string
  source: 'youtube' | 'spotify' | 'radio' | 'saved'
  youtube_id?: string
  cover: string
  is_video?: boolean
  path?: string
}
