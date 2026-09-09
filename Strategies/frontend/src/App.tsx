import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import Placeholder from './pages/Placeholder'

const API_BASE_URL = 'http://localhost:8000'

const TABS = [
  { path: '/rules', label: 'Rules' },
  { path: '/run', label: 'Run' },
  { path: '/results', label: 'Results' },
  { path: '/sell', label: 'Sell' },
  { path: '/backtest', label: 'Backtest' },
  { path: '/deep-dive', label: 'Deep Dive' },
  { path: '/missed-opportunities', label: 'Missed Opportunities' },
  { path: '/stats', label: 'Stats' },
]

function NavBar() {
  const location = useLocation()
  return (
    <nav className="flex gap-1 border-b border-gray-200 px-4">
      {TABS.map((tab) => (
        <Link
          key={tab.path}
          to={tab.path}
          className={`px-3 py-2 text-sm ${
            location.pathname === tab.path
              ? 'border-b-2 border-blue-600 font-medium text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  )
}

function BackendStatus() {
  const [health, setHealth] = useState<{ status: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then((res) => {
        if (!res.ok) throw new Error(`Backend responded with ${res.status}`)
        return res.json() as Promise<{ status: string }>
      })
      .then(setHealth)
      .catch((err) => setError(err.message))
  }, [])

  if (error) return <span className="text-xs text-red-600">Backend error: {error}</span>
  if (health) return <span className="text-xs text-green-600">Backend: {health.status}</span>
  return <span className="text-xs text-gray-400">Connecting to backend...</span>
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-white text-gray-900">
        <header className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-semibold">Frontier TradeLight</h1>
          <BackendStatus />
        </header>
        <NavBar />
        <main>
          <Routes>
            <Route path="/rules" element={<Placeholder title="Rules" />} />
            <Route path="/run" element={<Placeholder title="Run" />} />
            <Route path="/results" element={<Placeholder title="Results" />} />
            <Route path="/sell" element={<Placeholder title="Sell" />} />
            <Route path="/backtest" element={<Placeholder title="Backtest" />} />
            <Route path="/deep-dive" element={<Placeholder title="Deep Dive" />} />
            <Route path="/missed-opportunities" element={<Placeholder title="Missed Opportunities" />} />
            <Route path="/stats" element={<Placeholder title="Stats" />} />
            <Route path="*" element={<Placeholder title="Rules" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
