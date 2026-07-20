import { useState, useRef, useEffect } from 'react'
import { api } from '../api'

export default function Terminal() {
  const [history, setHistory] = useState<{ cmd: string; output: string }[]>([])
  const [cmd, setCmd] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!cmd.trim()) return

    setLoading(true)
    setHistory(h => [...h, { cmd, output: '' }])

    try {
      const result = await api.shell(cmd)
      setHistory(h => {
        const updated = [...h]
        updated[updated.length - 1].output = result.output
        return updated
      })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Command failed'
      setHistory(h => {
        const updated = [...h]
        updated[updated.length - 1].output = msg
        return updated
      })
    }

    setLoading(false)
    setCmd('')
  }

  const handleClear = () => {
    setHistory([])
  }

  return (
    <div style={styles.container}>
      <div style={styles.toolbar}>
        <span style={styles.toolbarTitle}>SSH Terminal</span>
        <div style={styles.toolbarActions}>
          <span style={styles.toolbarInfo}>hue@10.0.0.174</span>
          {history.length > 0 && (
            <button style={styles.clearBtn} onClick={handleClear}>Clear</button>
          )}
        </div>
      </div>

      <div style={styles.output}>
        {history.map((h, i) => (
          <div key={i}>
            <div style={styles.promptLine}>
              <span style={styles.prompt}>hue@HueMedia:~$ </span>
              <span>{h.cmd}</span>
            </div>
            {h.output && (
              <pre style={styles.outputText}>{h.output}</pre>
            )}
          </div>
        ))}
        {loading && <div style={styles.loading}>Running...</div>}
        <div ref={endRef} />
      </div>

      <form style={styles.inputRow} onSubmit={handleSubmit}>
        <span style={styles.prompt}>$ </span>
        <input
          style={styles.input}
          value={cmd}
          onChange={(e) => setCmd(e.target.value)}
          placeholder="Type a command..."
          disabled={loading}
          autoFocus
        />
      </form>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: 'calc(100vh - 180px)',
    background: '#0a0a14',
    borderRadius: '12px',
    overflow: 'hidden',
    border: '1px solid #2a2a3e',
  },
  toolbar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 16px',
    background: '#1a1a2e',
    borderBottom: '1px solid #2a2a3e',
  },
  toolbarTitle: {
    fontWeight: 600,
    fontSize: '.85rem',
  },
  toolbarActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  toolbarInfo: {
    color: '#666',
    fontSize: '.75rem',
  },
  clearBtn: {
    background: 'transparent',
    border: '1px solid #2a2a3e',
    color: '#888',
    padding: '4px 10px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '.75rem',
  },
  output: {
    flex: 1,
    overflow: 'auto',
    padding: '12px 16px',
    fontFamily: 'monospace',
    fontSize: '.8rem',
    lineHeight: 1.5,
  },
  promptLine: {
    display: 'flex',
  },
  prompt: {
    color: '#22c55e',
    whiteSpace: 'pre',
  },
  outputText: {
    margin: '0 0 8px 0',
    whiteSpace: 'pre-wrap',
    color: '#ccc',
    fontFamily: 'monospace',
    fontSize: '.8rem',
  },
  loading: {
    color: '#888',
    fontStyle: 'italic',
  },
  inputRow: {
    display: 'flex',
    alignItems: 'center',
    padding: '8px 16px',
    background: '#1a1a2e',
    borderTop: '1px solid #2a2a3e',
  },
  input: {
    flex: 1,
    background: 'transparent',
    border: 'none',
    color: '#e0e0e0',
    fontFamily: 'monospace',
    fontSize: '.85rem',
    outline: 'none',
  } as React.CSSProperties,
}
