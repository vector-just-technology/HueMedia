interface CoverArtProps {
  path: string | null
  size?: number
}

export default function CoverArt({ path, size = 48 }: CoverArtProps) {
  if (path) {
    const url = `/api/music/cover?path=${encodeURIComponent(path)}`
    return (
      <img
        src={url}
        alt="cover"
        style={{
          width: size,
          height: size,
          borderRadius: '6px',
          objectFit: 'cover',
          background: '#2a2a3e',
          flexShrink: 0,
        }}
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = 'none'
        }}
      />
    )
  }

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '6px',
        background: '#2a2a3e',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: size > 48 ? '2rem' : '1rem',
        color: '#555',
        flexShrink: 0,
      }}
    >
      &#x266B;
    </div>
  )
}
