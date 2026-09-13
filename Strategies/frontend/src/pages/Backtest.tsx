import { useEffect, useRef, useState } from 'react'
import { backtestApi, fetchReport, type BacktestChart, type BacktestResult, type ReportResponse, type YearlyRow } from '../api'

function formatEta(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return ''
  const s = Math.max(0, Math.round(seconds))
  const minutes = Math.floor(s / 60)
  const secs = s % 60
  return minutes === 0 ? `${secs}s` : `${minutes}m ${secs}s`
}

function formatMoney(n: number | undefined) {
  if (n === undefined) return '—'
  return n.toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

function formatPct(n: number | null | undefined, digits = 2) {
  if (n === null || n === undefined) return 'N/A'
  return `${n >= 0 ? '+' : ''}${n.toFixed(digits)}%`
}

/** Normalizes a set of equal-length series into an SVG polyline `points`
 * string inside a 0..840 x 20..220 viewBox, sharing one scale across all
 * series so they stay comparable on the same chart. */
function toPolyline(values: number[], min: number, max: number): string {
  const w = 800
  const x0 = 40
  const y0 = 20
  const y1 = 220
  const range = max - min || 1
  return values
    .map((v, i) => {
      const x = x0 + (i / Math.max(1, values.length - 1)) * w
      const y = y1 - ((v - min) / range) * (y1 - y0)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

export default function Backtest() {
  const [start, setStart] = useState('2021-01-01')
  const [end, setEnd] = useState('2026-01-01')
  const [capital, setCapital] = useState(100000)
  const [maxPositions, setMaxPositions] = useState(10)

  const [running, setRunning] = useState(false)
  const [day, setDay] = useState<number | null>(null)
  const [totalDays, setTotalDays] = useState<number | null>(null)
  const [eta, setEta] = useState<number | null>(null)
  const [logTail, setLogTail] = useState('')
  const [logOpen, setLogOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const [result, setResult] = useState<BacktestResult | null>(null)
  const [yearly, setYearly] = useState<YearlyRow[]>([])
  const [yearlyOpen, setYearlyOpen] = useState(true)
  const [trades, setTrades] = useState<ReportResponse | null>(null)
  const [tradesOpen, setTradesOpen] = useState(false)
  const [chart, setChart] = useState<BacktestChart | null>(null)
  const [showInflation, setShowInflation] = useState(false)
  const [showNifty, setShowNifty] = useState(false)
  const [chartLoading, setChartLoading] = useState(false)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadResults = () => {
    backtestApi.result().then((res) => {
      setResult(res)
      if (res.available) {
        backtestApi.yearly().then((r) => setYearly(r.rows))
        fetchReport('/backtest-trades').then(setTrades).catch(() => {})
      }
    })
  }

  const loadChart = (inflation: boolean, nifty: boolean) => {
    setChartLoading(true)
    backtestApi
      .chart(inflation, nifty)
      .then(setChart)
      .finally(() => setChartLoading(false))
  }

  // On mount: pick up an already-running backtest (e.g. after a page
  // reload), and show any results already on disk from a previous run.
  useEffect(() => {
    backtestApi.status().then((st) => {
      if (st.running) {
        setRunning(true)
        startPolling()
      }
    })
    loadResults()
  }, [])

  useEffect(() => {
    if (result?.available) loadChart(showInflation, showNifty)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result?.available, showInflation, showNifty])

  useEffect(() => {
    if (!message) return
    const t = setTimeout(() => setMessage(null), 5000)
    return () => clearTimeout(t)
  }, [message])

  const startPolling = () => {
    if (pollRef.current) return
    pollRef.current = setInterval(() => {
      backtestApi.status().then((st) => {
        setDay(st.day ?? null)
        setTotalDays(st.total_days ?? null)
        setEta(st.eta_seconds ?? null)
        setLogTail(st.log_tail ?? '')
        if (!st.running) {
          if (pollRef.current) {
            clearInterval(pollRef.current)
            pollRef.current = null
          }
          setRunning(false)
          if (st.exit_code === 0) {
            setMessage(
              st.stats_recorded
                ? 'Backtest complete. Stats tab updated (this run matched the benchmark range).'
                : 'Backtest complete. See results below.',
            )
            loadResults()
          } else {
            setError(`backtest.py exited with code ${st.exit_code}.`)
          }
        }
      })
    }, 1500)
  }

  const handleRun = () => {
    if (start >= end) {
      setError('Start date must be before end date.')
      return
    }
    setError(null)
    setMessage(null)
    setDay(null)
    setTotalDays(null)
    setLogTail('')
    backtestApi
      .run({ start, end, initial_capital: capital, max_positions: maxPositions })
      .then((res) => {
        if ('detail' in res) {
          setError(res.detail)
          return
        }
        setRunning(true)
        startPolling()
      })
      .catch((err) => setError(err.message))
  }

  const handleStop = () => {
    backtestApi.stop().then(() => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
      setRunning(false)
      setMessage('Backtest stopped.')
    })
  }

  const fraction = totalDays ? (day ?? 0) / totalDays : 0
  const progressLabel =
    day !== null && totalDays !== null
      ? `Evaluating day ${day}/${totalDays}${eta !== null ? ` - est. ${formatEta(eta)} remaining` : ''}`
      : 'Fetching/preparing data...'

  let chartMin = 0
  let chartMax = 1
  if (chart) {
    const all = [...chart.nominal, ...(chart.inflation_adjusted ?? []), ...(chart.nifty ?? [])]
    chartMin = Math.min(...all)
    chartMax = Math.max(...all)
  }

  return (
    <main className="flex-1 overflow-y-auto px-6 py-10">
      <div className="mx-auto flex max-w-[920px] flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-[22px] font-extrabold tracking-tight">Backtest</h1>
          <p className="max-w-[680px] text-[13.5px] leading-relaxed text-gray-500">
            Simulates generated_rules.py over a historical date range using the exit logic in
            generated_exit_strategy.py. On each signal, opens a flat position sized as an equal share of current
            equity.
          </p>
          <p className="text-xs text-gray-400">
            Edit exit_rules.md from the Sell tab &mdash; it drives both this backtest and the live holdings check.
          </p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {message && <p className="text-sm text-green-700">{message}</p>}

        {/* Config card */}
        <div className="rounded-[14px] border border-gray-200 bg-white p-5 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="mb-1.5 block text-[11.5px] font-semibold text-gray-500">Start date</label>
              <input
                type="date"
                value={start}
                onChange={(e) => setStart(e.target.value)}
                disabled={running}
                className="w-full rounded-lg border border-gray-200 px-2.5 py-2 font-mono text-[12.5px] text-gray-900 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-[11.5px] font-semibold text-gray-500">End date</label>
              <input
                type="date"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
                disabled={running}
                className="w-full rounded-lg border border-gray-200 px-2.5 py-2 font-mono text-[12.5px] text-gray-900 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-[11.5px] font-semibold text-gray-500">Starting capital (Rs.)</label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                disabled={running}
                className="w-full rounded-lg border border-gray-200 px-2.5 py-2 font-mono text-[12.5px] text-gray-900 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-[11.5px] font-semibold text-gray-500">Max concurrent positions</label>
              <input
                type="number"
                value={maxPositions}
                onChange={(e) => setMaxPositions(Number(e.target.value))}
                disabled={running}
                className="w-full rounded-lg border border-gray-200 px-2.5 py-2 font-mono text-[12.5px] text-gray-900 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10 disabled:opacity-50"
              />
            </div>
          </div>

          <p className="mt-3.5 text-[11.5px] leading-relaxed text-gray-400">
            Signals compete for a fixed number of position slots, sized as an equal share of current total equity.
            First run for a given range fetches history from NSE and caches it; later runs over the same range reuse
            that cache.
          </p>

          <div className="mt-4 flex items-center gap-2.5">
            <button
              onClick={handleRun}
              disabled={running}
              className="flex items-center gap-1.5 rounded-[9px] bg-accent px-[18px] py-2.5 text-[13px] font-semibold text-white hover:brightness-95 disabled:cursor-default disabled:bg-gray-300"
            >
              {running && (
                <svg className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M12 2a10 10 0 0 1 10 10" />
                </svg>
              )}
              {running ? 'Running backtest...' : 'Run backtest'}
            </button>
            {running && (
              <button
                onClick={handleStop}
                className="rounded-[9px] border border-red-200 bg-white px-4 py-2.5 text-[13px] font-semibold text-red-600 hover:bg-red-50"
              >
                Stop backtest
              </button>
            )}
          </div>

          {running && (
            <div className="mt-[18px] border-t border-gray-100 pt-4">
              <div className="mb-[7px] text-xs font-semibold text-gray-700">{progressLabel}</div>
              <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                <div
                  className="h-full rounded-full bg-accent transition-[width] duration-300"
                  style={{ width: `${Math.round(fraction * 100)}%` }}
                />
              </div>
              <button
                onClick={() => setLogOpen((v) => !v)}
                className="mt-2.5 flex items-center gap-1.5 bg-transparent py-1 text-xs font-semibold text-gray-500 hover:text-gray-700"
              >
                <svg
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  style={{ transform: logOpen ? 'rotate(0deg)' : 'rotate(-90deg)' }}
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
                Raw log
              </button>
              {logOpen && (
                <pre className="mt-1.5 max-h-36 overflow-y-auto whitespace-pre-wrap rounded-lg border border-gray-100 bg-[#FCFCFD] p-3 font-mono text-[11px] leading-relaxed text-gray-500">
                  {logTail || 'Starting...'}
                </pre>
              )}
            </div>
          )}
        </div>

        {/* Portfolio result */}
        {result?.available && (
          <>
            <hr className="border-gray-200" />
            <div className="text-[15px] font-extrabold">Portfolio result</div>

            <div className="grid grid-cols-6 gap-3">
              <div className="rounded-xl border border-gray-200 bg-white p-3.5">
                <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Final Equity</div>
                <div className="font-mono text-base font-bold">Rs.{formatMoney(result.final_equity)}</div>
                <div className="mt-0.5 text-[11px] text-green-600">{formatPct(result.total_return_pct)} total</div>
              </div>
              <div className="rounded-xl border border-gray-200 bg-white p-3.5">
                <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">CAGR</div>
                <div className={`font-mono text-base font-bold ${(result.cagr_pct ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {result.cagr_pct === null || result.cagr_pct === undefined ? 'N/A' : `${formatPct(result.cagr_pct)}/yr`}
                </div>
              </div>
              <div className="rounded-xl border border-gray-200 bg-white p-3.5">
                <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Max Drawdown</div>
                <div className="font-mono text-base font-bold text-red-600">{result.max_dd_pct?.toFixed(1)}%</div>
              </div>
              <div className="rounded-xl border border-gray-200 bg-white p-3.5">
                <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Funded Trades</div>
                <div className="font-mono text-base font-bold">{result.funded_count}</div>
              </div>
              <div className="rounded-xl border border-gray-200 bg-white p-3.5">
                <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Skipped</div>
                <div className="font-mono text-base font-bold text-gray-400">{result.skipped_count}</div>
              </div>
              <div className="rounded-xl border border-gray-200 bg-white p-3.5">
                <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Composite Score</div>
                <div className="font-mono text-base font-bold text-accent">
                  {result.composite_score === null || result.composite_score === undefined ? 'N/A' : result.composite_score.toFixed(2)}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-5">
              <label className="flex cursor-pointer items-center gap-1.5 text-[12.5px] font-medium text-gray-600">
                <input type="checkbox" checked={showInflation} onChange={(e) => setShowInflation(e.target.checked)} />
                Show inflation-adjusted results
              </label>
              <label className="flex cursor-pointer items-center gap-1.5 text-[12.5px] font-medium text-gray-600">
                <input type="checkbox" checked={showNifty} onChange={(e) => setShowNifty(e.target.checked)} />
                Compare with Nifty 50
              </label>
              {chartLoading && <span className="text-xs text-gray-400">Loading...</span>}
            </div>

            <div className="rounded-[14px] border border-gray-200 bg-white p-5 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
              {chart && chart.nominal.length > 0 ? (
                <>
                  <svg viewBox="0 0 860 260" width="100%" height="260" style={{ display: 'block' }}>
                    <line x1="40" y1="20" x2="40" y2="220" stroke="#EEEEF0" strokeWidth="1" />
                    <line x1="40" y1="220" x2="840" y2="220" stroke="#EEEEF0" strokeWidth="1" />
                    {chart.nifty && (
                      <polyline points={toPolyline(chart.nifty, chartMin, chartMax)} fill="none" stroke="#9AA0AC" strokeWidth="1.75" strokeDasharray="4 3" />
                    )}
                    {chart.inflation_adjusted && (
                      <polyline points={toPolyline(chart.inflation_adjusted, chartMin, chartMax)} fill="none" stroke="#D97706" strokeWidth="1.75" />
                    )}
                    <polyline points={toPolyline(chart.nominal, chartMin, chartMax)} fill="none" stroke="#3D5944" strokeWidth="2.25" />
                    <text x="40" y="238" fontSize="10" fontFamily="JetBrains Mono, monospace" fill="#9AA0AC">
                      {chart.dates[0]}
                    </text>
                    <text x="740" y="238" fontSize="10" fontFamily="JetBrains Mono, monospace" fill="#9AA0AC">
                      {chart.dates[chart.dates.length - 1]}
                    </text>
                  </svg>
                  <div className="mt-2.5 flex items-center gap-4 pl-10">
                    <div className="flex items-center gap-1.5">
                      <span className="inline-block h-[2.5px] w-3.5 bg-accent" />
                      <span className="text-[11px] text-gray-500">Nominal</span>
                    </div>
                    {chart.inflation_adjusted && (
                      <div className="flex items-center gap-1.5">
                        <span className="inline-block h-[2.5px] w-3.5 bg-amber-600" />
                        <span className="text-[11px] text-gray-500">Inflation-adjusted</span>
                      </div>
                    )}
                    {chart.nifty && (
                      <div className="flex items-center gap-1.5">
                        <span className="inline-block h-0 w-3.5 border-t-2 border-dashed border-gray-400" />
                        <span className="text-[11px] text-gray-500">Nifty 50</span>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <p className="py-8 text-center text-sm text-gray-400">No chart data.</p>
              )}
            </div>

            {yearly.length > 0 && (
              <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
                <button
                  onClick={() => setYearlyOpen((v) => !v)}
                  className="flex w-full items-center justify-between px-[18px] py-3.5 hover:bg-gray-50"
                >
                  <span className="text-[13.5px] font-bold">Year-by-year breakdown</span>
                  <svg
                    width="13"
                    height="13"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#9AA0AC"
                    strokeWidth="2.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ transform: yearlyOpen ? 'rotate(0deg)' : 'rotate(-90deg)' }}
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>
                {yearlyOpen && (
                  <table className="w-full border-collapse border-t border-gray-100">
                    <thead>
                      <tr className="bg-[#FAFAFB]">
                        <th className="px-[18px] py-2 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Year</th>
                        <th className="px-[18px] py-2 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Start Equity</th>
                        <th className="px-[18px] py-2 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">End Equity</th>
                        <th className="px-[18px] py-2 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Return %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {yearly.map((row) => (
                        <tr key={row.year} className="border-t border-gray-100">
                          <td className="px-[18px] py-2 font-mono text-xs font-bold">{row.year}</td>
                          <td className="px-[18px] py-2 text-right font-mono text-xs text-gray-700">Rs.{formatMoney(row.start_equity)}</td>
                          <td className="px-[18px] py-2 text-right font-mono text-xs text-gray-700">Rs.{formatMoney(row.end_equity)}</td>
                          <td className={`px-[18px] py-2 text-right font-mono text-xs font-semibold ${row.return_pct >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                            {formatPct(row.return_pct, 1)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {trades && trades.rows.length > 0 && (
              <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
                <button
                  onClick={() => setTradesOpen((v) => !v)}
                  className="flex w-full items-center justify-between px-[18px] py-3.5 hover:bg-gray-50"
                >
                  <span className="text-[13.5px] font-bold">Individual trades</span>
                  <svg
                    width="13"
                    height="13"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#9AA0AC"
                    strokeWidth="2.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ transform: tradesOpen ? 'rotate(0deg)' : 'rotate(-90deg)' }}
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>
                {tradesOpen && (
                  <div className="overflow-x-auto border-t border-gray-100">
                    <table className="w-full border-collapse" style={{ minWidth: `${Math.max(700, trades.columns.length * 120)}px` }}>
                      <thead>
                        <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                          {trades.columns.map((col) => (
                            <th
                              key={col}
                              className={`whitespace-nowrap px-3 py-2 text-[10.5px] font-bold uppercase tracking-wide text-gray-400 ${
                                col === 'Symbol' ? 'sticky left-0 bg-[#FAFAFB] text-left' : typeof trades.rows[0]?.[col] === 'number' ? 'text-right' : 'text-left'
                              }`}
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {trades.rows.map((row, i) => (
                          <tr key={i} className="border-b border-gray-100 hover:bg-[#FAFAFB]">
                            {trades.columns.map((col) => {
                              if (col === 'Symbol') {
                                return (
                                  <td key={col} className="sticky left-0 whitespace-nowrap bg-white px-3 py-2 font-mono text-xs font-bold text-gray-900">
                                    {String(row[col] ?? '')}
                                  </td>
                                )
                              }
                              if (col === 'Funded') {
                                const funded = row[col] === true
                                return (
                                  <td key={col} className="whitespace-nowrap px-3 py-2">
                                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${funded ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                      {funded ? 'Funded' : 'Skipped'}
                                    </span>
                                  </td>
                                )
                              }
                              if (col === 'ProfitRs') {
                                const v = row[col]
                                const num = typeof v === 'number' ? v : null
                                return (
                                  <td key={col} className={`whitespace-nowrap px-3 py-2 text-right font-mono text-xs font-semibold ${num === null ? 'text-gray-400' : num >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                                    {num === null ? '—' : `${num >= 0 ? '+' : ''}${num.toFixed(2)}`}
                                  </td>
                                )
                              }
                              const isNumeric = typeof row[col] === 'number'
                              return (
                                <td key={col} className={`whitespace-nowrap px-3 py-2 text-xs text-gray-700 ${isNumeric ? 'text-right font-mono' : ''}`}>
                                  {row[col] === null || row[col] === '' ? '—' : String(row[col])}
                                </td>
                              )
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  )
}
