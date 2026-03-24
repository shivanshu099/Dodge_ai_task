import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import ForceGraph2D from 'react-force-graph-2d'

const API_URL = 'https://dodge-ai-task.onrender.com/api/graph'

const GROUP_CONFIG = {
  1: { label: 'Sales Order', color: '#3b82f6', abbr: 'SO', cssClass: 'so' },
  2: { label: 'Billing Document', color: '#10b981', abbr: 'Bill', cssClass: 'bill' },
  3: { label: 'Business Partner', color: '#f59e0b', abbr: 'BP', cssClass: 'bp' },
}

export default function App() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [limit, setLimit] = useState(100)
  const fgRef = useRef()

  // Chatbot state
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', text: 'Hi! Ask me anything about your SAP O2C data.' }
  ])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const chatEndRef = useRef(null)

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  // Send chat message
  const handleChatSend = async () => {
    const msg = chatInput.trim()
    if (!msg || chatLoading) return
    setChatInput('')
    setChatMessages(prev => [...prev, { role: 'user', text: msg }])
    setChatLoading(true)
    try {
      const res = await fetch('https://dodge-ai-task.onrender.com/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg }),
      })
      const data = await res.json()
      const reply = data.response || data.answer || data.result || data.output || JSON.stringify(data)
      setChatMessages(prev => [...prev, { role: 'assistant', text: reply }])
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'assistant', text: `⚠ Error: ${err.message}. Make sure the service on port 8969 is running.` }])
    } finally {
      setChatLoading(false)
    }
  }

  const handleChatKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleChatSend() }
  }

  // Fetch graph data
  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}?limit=${limit}`)
      if (!res.ok) throw new Error(`Server responded ${res.status}`)
      const data = await res.json()
      setGraphData(data)
    } catch (err) {
      setError(`Failed to load graph data. Make sure the backend is running on port 8000. (${err.message})`)
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => { fetchData() }, [fetchData])

  // Compute stats
  const stats = useMemo(() => {
    const counts = { 1: 0, 2: 0, 3: 0 }
    graphData.nodes.forEach(n => { counts[n.group] = (counts[n.group] || 0) + 1 })
    return { ...counts, totalNodes: graphData.nodes.length, totalLinks: graphData.links.length }
  }, [graphData])

  // Count connections for selected node
  const selectedConnections = useMemo(() => {
    if (!selectedNode) return 0
    return graphData.links.filter(
      l => (l.source?.id || l.source) === selectedNode.id || (l.target?.id || l.target) === selectedNode.id
    ).length
  }, [selectedNode, graphData])

  // Node paint function
  const paintNode = useCallback((node, ctx, globalScale) => {
    const cfg = GROUP_CONFIG[node.group] || GROUP_CONFIG[3]
    const isSelected = selectedNode && selectedNode.id === node.id
    const r = isSelected ? 7 : 5

    // Glow
    ctx.beginPath()
    ctx.arc(node.x, node.y, r + 3, 0, 2 * Math.PI)
    ctx.fillStyle = cfg.color + '22'
    ctx.fill()

    // Circle
    ctx.beginPath()
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
    ctx.fillStyle = cfg.color
    ctx.fill()

    if (isSelected) {
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 2
      ctx.stroke()
    }

    // Label (only at high zoom)
    if (globalScale > 1.8) {
      const label = cfg.abbr + ': ' + node.id.toString().slice(-4)
      ctx.font = `${Math.max(10 / globalScale, 3)}px Inter, sans-serif`
      ctx.textAlign = 'center'
      ctx.fillStyle = '#cbd5e1'
      ctx.fillText(label, node.x, node.y + r + 8 / globalScale)
    }
  }, [selectedNode])

  // Link paint
  const paintLink = useCallback((link, ctx) => {
    ctx.strokeStyle = 'rgba(255,255,255,0.06)'
    ctx.lineWidth = 0.5
    ctx.beginPath()
    ctx.moveTo(link.source.x, link.source.y)
    ctx.lineTo(link.target.x, link.target.y)
    ctx.stroke()
  }, [])

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(prev => prev && prev.id === node.id ? null : node)
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 600)
      fgRef.current.zoom(3, 600)
    }
  }, [])

  const handleZoomFit = () => {
    if (fgRef.current) fgRef.current.zoomToFit(400, 60)
  }

  return (
    <>
      {/* HEADER */}
      <header className="app-header">
        <div className="logo-section">
          <div className="logo-icon">⬡</div>
          <div>
            <h1>Dodge AI</h1>
            <div className="subtitle">Order-to-Cash Process Visualization</div>
          </div>
        </div>
        <div className="controls-bar">
          <label style={{ fontSize: 12, color: '#94a3b8' }}>Records:</label>
          <select className="limit-select" value={limit} onChange={e => setLimit(Number(e.target.value))}>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
            <option value={500}>500</option>
          </select>
          <button className="control-btn" onClick={handleZoomFit}>Fit View</button>
          <button className="control-btn" onClick={fetchData}>Refresh</button>
        </div>
      </header>

      {/* ERROR */}
      {error && <div className="error-banner">⚠ {error}</div>}

      {/* MAIN */}
      <div className="main-content">
        {/* GRAPH */}
        <div className="graph-container">
          {loading && (
            <div className="loading-overlay">
              <div className="loading-spinner" />
              <div className="loading-text">Loading graph data...</div>
            </div>
          )}
          {!loading && !error && (
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              nodeCanvasObject={paintNode}
              linkCanvasObject={paintLink}
              onNodeClick={handleNodeClick}
              nodeLabel={n => {
                const cfg = GROUP_CONFIG[n.group] || GROUP_CONFIG[3]
                return `<div class="graph-tooltip"><strong>${cfg.label}</strong><br/>${n.label || n.id}</div>`
              }}
              backgroundColor="rgba(0,0,0,0)"
              cooldownTicks={80}
              warmupTicks={30}
              d3AlphaDecay={0.02}
              d3VelocityDecay={0.3}
              linkDirectionalParticles={0}
              enableNodeDrag={true}
            />
          )}
        </div>

        {/* SIDEBAR */}
        <div className="sidebar">
          {/* LEGEND */}
          <div className="sidebar-section">
            <h3>Legend</h3>
            <div className="legend-items">
              {Object.entries(GROUP_CONFIG).map(([groupId, cfg]) => (
                <div className="legend-item" key={groupId}>
                  <span className={`legend-dot ${cfg.cssClass}`} />
                  <span className="legend-label">{cfg.label}</span>
                  <span className="legend-count">{stats[groupId] || 0}</span>
                </div>
              ))}
            </div>
          </div>

          {/* STATS */}
          <div className="sidebar-section">
            <h3>Statistics</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">{stats.totalNodes}</div>
                <div className="stat-label">Nodes</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats.totalLinks}</div>
                <div className="stat-label">Edges</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats[1] || 0}</div>
                <div className="stat-label">Sales Orders</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{stats[2] || 0}</div>
                <div className="stat-label">Billing Docs</div>
              </div>
            </div>
          </div>

          {/* SELECTED NODE */}
          {selectedNode && (
            <div className="node-detail">
              <h3 style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, color: '#94a3b8', marginBottom: 14 }}>Selected Node</h3>
              <div className="node-detail-card">
                <div className="node-detail-header">
                  <span className={`node-type-badge ${GROUP_CONFIG[selectedNode.group]?.cssClass || ''}`}>
                    {GROUP_CONFIG[selectedNode.group]?.label || 'Unknown'}
                  </span>
                </div>
                <div className="node-detail-id">{selectedNode.label || selectedNode.id}</div>
                <div className="node-detail-connections">{selectedConnections} connection{selectedConnections !== 1 ? 's' : ''}</div>
              </div>
            </div>
          )}

          {/* CHATBOT */}
          <div className="sidebar-section chat-section">
            <h3>💬 AI Assistant</h3>
            <div className="chat-messages">
              {chatMessages.map((m, i) => (
                <div key={i} className={`chat-bubble ${m.role}`}>
                  {m.role === 'assistant' && <span className="chat-avatar">🤖</span>}
                  <div className="chat-text">{m.text}</div>
                </div>
              ))}
              {chatLoading && (
                <div className="chat-bubble assistant">
                  <span className="chat-avatar">🤖</span>
                  <div className="chat-text typing-indicator"><span /><span /><span /></div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div className="chat-input-area">
              <input
                className="chat-input"
                type="text"
                placeholder="Ask about your data..."
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={handleChatKeyDown}
                disabled={chatLoading}
              />
              <button className="chat-send-btn" onClick={handleChatSend} disabled={chatLoading || !chatInput.trim()}>
                ➤
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
