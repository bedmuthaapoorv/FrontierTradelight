import { useEffect, useRef, useState } from 'react'
import { backtestApi, statsApi, type Stats, type StrategyOption } from '../api'

const CURRENT_LIVE_OPTION = 'Current (live rules.md)'
const BENCHMARK_INITIAL_CAPITAL = 100000
const BENCHMARK_MAX_POSITIONS = 10

function formatEta(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return ''
  const s = Math.max(0, Math.round(seconds))
  const minutes = Math.floor(s / 60)
  const secs = s % 60
  return minutes === 0 ? `${secs}s` : `${minutes}m ${secs}s`
}

function formatPct(n: number | null, digits = 2) {
  if (n === null) return 'N/A'
  return `${n >= 0 ? '+' : ''}${n.toFixed(digits)}%`
}

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [options, setOptions] = useState<StrategyOption[]>([{ key: CURRENT_LIVE_OPTION, label: CURRENT_LIVE_OPTION }])
  const [selected, setSelected] = useState(CURRENT_LIVE_OPTION)

  const [running, setRunning] = useState(false)
  const [day, setDay] = useState<number | null>(null)
  const [totalDays, setTotalDays] = useState<number | null>(null)
  const [eta, setEta] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadStats = () => statsApi.get().then(setStats)

  useEffect(() => {
    loadStats()
    statsApi.strategyOptions().then((r) => setOptions(r.options))
    backtestApi.status().then((st) => {
      if (st.running) {
        setRunning(true)
        startPolling()
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!message) return
    const t = setTimeout(() => setMessage(null), 6000)
    return () => clearTimeout(t)
  }, [message])

  const startPolling = () => {
    if (pollRef.current) return
    pollRef.current = setInterval(() => {
      backtestApi.status().then((st) => {
        setDay(st.day ?? null)
        setTotalDays(st.total_days ?? null)
        setEta(st.eta_seconds ?? null)
        if (!st.running) {
          if (pollRef.current) {
            clearInterval(pollRef.current)
            pollRef.current = null
          }
          setRunning(false)
          if (st.exit_code === 0) {
            setMessage(
              st.stats_recorded
                ? 'Benchmark backtest complete. Leaderboard updated below.'
                : `Backtest complete, but stats were not recorded (${st.stats_reason ?? 'range did not match the benchmark'}).`,
            )
            loadStats()
          } else {
            setError(`backtest.py exited with code ${st.exit_code}.`)
          }
        }
      })
    }, 1500)
  }

  const handleRun = async () => {
    setError(null)
    setMessage(null)

    if (selected !== CURRENT_LIVE_OPTION) {
      const res = await statsApi.loadStrategy(selected)
      if (res.status !== 'ok') {
        setError(res.message ?? 'Failed to load selected strategy.')
        return
      }
    }

    const res = await backtestApi.run({
      start: stats?.benchmark_start ?? '2021-01-01',
      end: stats?.benchmark_end ?? '2026-01-01',
      initial_capital: BENCHMARK_INITIAL_CAPITAL,
      max_positions: BENCHMARK_MAX_POSITIONS,
    })
    if ('detail' in res) {
      setError(res.detail)
      return
    }
    setDay(null)
    setTotalDays(null)
    setRunning(true)
    startPolling()
  }

  const fraction = totalDays ? (day ?? 0) / totalDays : 0
  const progressLabel =
    day !== null && totalDays !== null
      ? `Evaluating day ${day}/${totalDays}${eta !== null ? ` - est. ${formatEta(eta)} remaining` : ''}`
      : 'Fetching/preparing data...'

  const rows = stats?.rows ?? []
  const topScore = rows.length > 0 ? Math.max(...rows.map((r) => r.composite_score ?? -Infinity)) : null

  return (
    <main className="flex-1 overflow-y-auto px-6 py-10">
      <div className="mx-auto flex max-w-[920px] flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-[22px] font-extrabold tracking-tight">Stats</h1>
          <p className="max-w-[680px] text-[13.5px] leading-relaxed text-gray-500">
            The latest CAGR, Max Drawdown, and Composite Score recorded for each strategy backtested over the
            benchmark range below. Running a benchmark updates only that strategy&apos;s row here &mdash; every other
            row is left exactly as it was.
          </p>
          {stats && (
            <p className="text-xs text-gray-400">
              This table only updates from a backtest run over the exact benchmark range &mdash;{' '}
              <span className="font-mono font-semibold text-gray-500">
                {stats.benchmark_start} to {stats.benchmark_end}
              </span>{' '}
              &mdash; so every row is a fair, apples-to-apples comparison. A backtest run over any other range (e.g.
              from the Backtest tab) will NOT update this table.
            </p>
          )}
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {message && <p className="text-sm text-green-700">{message}</p>}

        {/* Config card */}
        <div className="rounded-[14px] border border-gray-200 bg-white p-5 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
          <div className="flex items-center gap-2.5">
            <button
              onClick={handleRun}
              disabled={running}
              className="flex flex-shrink-0 items-center gap-1.5 rounded-[9px] bg-accent px-[18px] py-2.5 text-[13px] font-semibold text-white hover:brightness-95 disabled:cursor-default disabled:bg-gray-300"
            >
              {running && (
                <svg className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M12 2a10 10 0 0 1 10 10" />
                </svg>
              )}
              {running ? 'Running benchmark...' : 'Benchmark backtest'}
            </button>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              disabled={running}
              className="max-w-[420px] flex-1 rounded-lg border border-gray-200 px-3 py-2.5 text-[12.5px] font-medium text-gray-700 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10 disabled:opacity-50"
            >
              {options.map((opt) => (
                <option key={opt.key} value={opt.key}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {selected !== CURRENT_LIVE_OPTION && (
            <p className="mt-3 text-[11.5px] leading-relaxed text-gray-400">
              Selecting a strategy here and clicking Benchmark backtest makes it the LIVE strategy (rules.md) &mdash;
              whatever&apos;s live now is backed up first, same as overwriting from the Rules tab&apos;s restore
              modal.
            </p>
          )}

          {running && (
            <div className="mt-4 border-t border-gray-100 pt-4">
              <div className="mb-[7px] text-xs font-semibold text-gray-700">{progressLabel}</div>
              <div className="h-2 overflow-hidden rounded-full bg-gray-100">
                <div
                  className="h-full rounded-full bg-accent transition-[width] duration-300"
                  style={{ width: `${Math.round(fraction * 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Leaderboard */}
        <div className="flex flex-col gap-2">
          <div className="text-[15px] font-extrabold">Strategy leaderboard</div>

          {rows.length === 0 ? (
            <div className="rounded-[14px] border border-gray-200 bg-white p-10 text-center text-[13px] text-gray-400">
              No strategy stats yet. Run a Benchmark backtest above first.
            </div>
          ) : (
            <>
              <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                      <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Strategy
                      </th>
                      <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Exit Strategy
                      </th>
                      <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        CAGR
                      </th>
                      <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Max Drawdown
                      </th>
                      <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Composite Score
                      </th>
                      <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Last Updated
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => {
                      const isTop = topScore !== null && row.composite_score === topScore
                      return (
                        <tr key={row.strategy_name} className={`border-b border-gray-100 ${isTop ? 'bg-accent-soft/40' : ''}`}>
                          <td className="flex items-center gap-2 px-4 py-2.5 text-[12.5px] font-bold text-gray-900">
                            {row.strategy_name}
                            {isTop && (
                              <span className="rounded-full bg-accent-soft px-1.5 py-0.5 font-mono text-[9.5px] font-bold tracking-wide text-accent">
                                TOP SCORE
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-2.5 text-xs text-gray-600">{row.exit_strategy_name || '—'}</td>
                          <td
                            className={`px-4 py-2.5 text-right font-mono text-xs font-bold ${
                              (row.cagr_pct ?? 0) >= 0 ? 'text-green-700' : 'text-red-700'
                            }`}
                          >
                            {formatPct(row.cagr_pct)}
                          </td>
                          <td className="px-4 py-2.5 text-right font-mono text-xs font-semibold text-red-700">
                            {row.max_dd_pct === null ? 'N/A' : `${row.max_dd_pct.toFixed(1)}%`}
                          </td>
                          <td className="px-4 py-2.5 text-right font-mono text-xs font-bold text-accent">
                            {row.composite_score === null ? 'N/A' : row.composite_score.toFixed(2)}
                          </td>
                          <td className="px-4 py-2.5 text-right font-mono text-[11px] text-gray-400">{row.last_updated}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              <p className="px-0.5 text-[11px] text-gray-400">Sorted by Composite Score, highest first.</p>
            </>
          )}
        </div>
      </div>
    </main>
  )
}
