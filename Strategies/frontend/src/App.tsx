import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import Placeholder from './pages/Placeholder'
import Rules from './pages/Rules'
import Run from './pages/Run'
import Results from './pages/Results'
import Sell from './pages/Sell'
import Backtest from './pages/Backtest'
import DeepDive from './pages/DeepDive'

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
    <nav className="flex flex-shrink-0 items-center gap-1 border-b border-gray-200 bg-white px-6">
      {TABS.map((tab) => {
        const active = location.pathname === tab.path
        return (
          <Link
            key={tab.path}
            to={tab.path}
            className={`relative px-3.5 py-3 text-[13.5px] font-medium ${
              active ? 'text-accent font-semibold' : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            {tab.label}
            {active && (
              <span className="absolute inset-x-3.5 -bottom-px h-0.5 rounded-t bg-accent" />
            )}
          </Link>
        )
      })}
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

  if (error) {
    return (
      <div className="flex items-center gap-2 text-xs text-red-600">
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
        Backend error: {error}
      </div>
    )
  }
  if (health) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span className="h-1.5 w-1.5 rounded-full bg-green-600" />
        Backend connected
      </div>
    )
  }
  return (
    <div className="flex items-center gap-2 text-xs text-gray-400">
      <span className="h-1.5 w-1.5 rounded-full bg-gray-300" />
      Connecting to backend...
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen flex-col overflow-hidden bg-[#F7F7F8] text-gray-900">
        <header className="flex flex-shrink-0 items-center justify-between border-b border-gray-200 bg-white px-7 py-3.5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-[26px] w-[26px] flex-shrink-0 items-center justify-center rounded-[7px] bg-accent">
              <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path
                  transform="translate(3,5.55) scale(0.1041) translate(-65,-33)"
                  d="M229.592 92.2116C232.959 93.5674 232.925 98.3461 229.538 99.6536L99.6326 149.815C95.9576 151.234 92.6606 147.046 94.903 143.807L110.942 120.639C112.374 118.57 111.564 115.709 109.26 114.699L74.1763 99.3083C71.0127 97.9205 70.9777 93.4449 74.1193 92.0078L109.156 75.9805C111.392 74.9577 112.185 72.1788 110.825 70.1305L94.6287 45.7365C92.4555 42.4633 95.8105 38.346 99.4551 39.8135L229.592 92.2116Z"
                  fill="#FFFFFF"
                />
              </svg>
            </div>
            <h1 className="text-[15px] font-extrabold tracking-tight">Frontier TradeLight</h1>
          </div>
          <BackendStatus />
        </header>

        <NavBar />

        <Routes>
          <Route path="/rules" element={<Rules />} />
          <Route path="/run" element={<Run />} />
          <Route path="/results" element={<Results />} />
          <Route path="/sell" element={<Sell />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/deep-dive" element={<DeepDive />} />
          <Route path="/missed-opportunities" element={<Placeholder title="Missed Opportunities" />} />
          <Route path="/stats" element={<Placeholder title="Stats" />} />
          <Route path="*" element={<Rules />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
