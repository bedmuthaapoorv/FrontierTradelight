import { useEffect, useState } from 'react'
import { backtestApi, type BacktestResult, type PortfolioByYear, type PortfolioYear } from '../api'

function formatPct(n: number, digits = 2) {
  return `${n >= 0 ? '+' : ''}${n.toFixed(digits)}%`
}

/** Actual elapsed time represented by the given years, in years - clips
 * each year to calendar-year boundaries further clipped by the overall
 * backtest's start/end date, mirroring tabs/deep_dive.py's elapsed_years
 * exactly (not just a count of selected years). */
function elapsedYears(overallMin: Date, overallMax: Date, years: number[]): number {
  let totalDays = 0
  for (const year of years) {
    const yearStart = new Date(Math.max(new Date(year, 0, 1).getTime(), overallMin.getTime()))
    const yearEnd = new Date(Math.min(new Date(year, 11, 31).getTime(), overallMax.getTime()))
    if (yearEnd < yearStart) continue
    totalDays += Math.round((yearEnd.getTime() - yearStart.getTime()) / 86400000) + 1
  }
  return totalDays / 365.25
}

/** Concatenates each selected year's actual daily equity path, rescaled so
 * each year picks up where the previous selected year left off -
 * mirrors tabs/deep_dive.py's stitch_equity exactly, using the real daily
 * series (not a start/end approximation). */
function stitchEquity(portfolioYears: PortfolioYear[], selectedYears: Set<number>): number[] {
  const sorted = portfolioYears.filter((y) => selectedYears.has(y.year)).sort((a, b) => a.year - b.year)
  const out: number[] = []
  let running = 100
  for (const y of sorted) {
    if (y.equity.length === 0) continue
    const first = y.equity[0]
    const rescaled = y.equity.map((v) => (v / first) * running)
    out.push(...rescaled)
    running = rescaled[rescaled.length - 1]
  }
  return out
}

interface Stats {
  totalReturnPct: number
  cagrPct: number
  yearsElapsed: number
  maxDdPct: number
  returnToPain: number | null
  stitched: number[]
}

function computeStats(
  portfolioYears: PortfolioYear[],
  selectedYears: Set<number>,
  overallMin: Date,
  overallMax: Date,
  fullRange: boolean,
  fullRangeResult: BacktestResult | null,
): Stats | null {
  if (selectedYears.size === 0) return null

  const stitched = stitchEquity(portfolioYears, selectedYears)

  let totalReturnPct: number
  let cagrPct: number
  let yearsElapsed: number

  if (fullRange && fullRangeResult?.available) {
    // Full range uses the exact continuous first-to-last equity change
    // (the real /backtest/result numbers), not a per-year-bucket
    // compounding approximation - mirrors compute_stats' full_range branch.
    totalReturnPct = fullRangeResult.total_return_pct ?? 0
    cagrPct = fullRangeResult.cagr_pct ?? 0
    yearsElapsed = (overallMax.getTime() - overallMin.getTime()) / 86400000 / 365.25
  } else {
    const years = [...selectedYears].sort((a, b) => a - b)
    let compounded = 1
    for (const year of years) {
      const y = portfolioYears.find((p) => p.year === year)
      if (y) compounded *= 1 + y.return_pct / 100
    }
    totalReturnPct = (compounded - 1) * 100
    yearsElapsed = elapsedYears(overallMin, overallMax, years)
    cagrPct = yearsElapsed > 0 ? (Math.pow(compounded, 1 / yearsElapsed) - 1) * 100 : 0
  }

  let runningMax = stitched[0] ?? 100
  let maxDdPct = 0
  for (const v of stitched) {
    runningMax = Math.max(runningMax, v)
    maxDdPct = Math.min(maxDdPct, ((v - runningMax) / runningMax) * 100)
  }

  const returnToPain = maxDdPct < 0 ? cagrPct / Math.abs(maxDdPct) : null

  return { totalReturnPct, cagrPct, yearsElapsed, maxDdPct, returnToPain, stitched }
}

function StatBlock({ stats, highlighted }: { stats: Stats; highlighted?: boolean }) {
  const isPartialYear = stats.yearsElapsed < 1
  const cagrLabel = isPartialYear ? 'CAGR (extrapolated!)' : 'CAGR'
  const borderClass = highlighted ? 'border-accent' : 'border-gray-200'

  return (
    <div className="flex flex-col gap-2.5">
      <div className={`rounded-xl border ${borderClass} bg-white p-3.5`}>
        <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Total Return</div>
        <div className={`font-mono text-[17px] font-bold ${stats.totalReturnPct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {formatPct(stats.totalReturnPct)}
        </div>
      </div>
      <div className={`rounded-xl border ${borderClass} bg-white p-3.5`}>
        <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">{cagrLabel}</div>
        <div className={`font-mono text-[17px] font-bold ${stats.cagrPct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {formatPct(stats.cagrPct)}/yr
        </div>
        {isPartialYear && (
          <p className="mt-1 text-[11px] leading-snug text-gray-400">
            This covers only ~{(stats.yearsElapsed * 12).toFixed(1)} months of data &mdash; extrapolated, not a real
            measured annual rate.
          </p>
        )}
      </div>
      <div className={`rounded-xl border ${borderClass} bg-white p-3.5`}>
        <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Worst Drawdown</div>
        <div className="font-mono text-[17px] font-bold text-red-600">{stats.maxDdPct.toFixed(1)}%</div>
      </div>
      <div className={`rounded-xl border ${borderClass} bg-white p-3.5`}>
        <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Return-to-Pain Ratio</div>
        <div className="font-mono text-[17px] font-bold">{stats.returnToPain === null ? 'N/A' : stats.returnToPain.toFixed(2)}</div>
      </div>
    </div>
  )
}

function toPolyline(values: number[]): string {
  if (values.length === 0) return ''
  const w = 800
  const x0 = 40
  const y0 = 16
  const y1 = 190
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  return values
    .map((v, i) => {
      const x = x0 + (i / Math.max(1, values.length - 1)) * w
      const y = y1 - ((v - min) / range) * (y1 - y0)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

export default function DeepDive() {
  const [data, setData] = useState<PortfolioByYear | null>(null)
  const [fullResult, setFullResult] = useState<BacktestResult | null>(null)
  const [selectedYears, setSelectedYears] = useState<Set<number>>(new Set())
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([backtestApi.portfolioByYear(), backtestApi.result()])
      .then(([byYear, result]) => {
        setData(byYear)
        setFullResult(result)
        setSelectedYears(new Set(byYear.years.map((y) => y.year)))
      })
      .catch((err) => setError(err.message))
  }, [])

  if (error) {
    return (
      <main className="flex-1 overflow-y-auto px-6 py-10">
        <p className="text-sm text-red-600">{error}</p>
      </main>
    )
  }

  if (!data) {
    return (
      <main className="flex-1 overflow-y-auto px-6 py-10">
        <p className="text-sm text-gray-500">Loading...</p>
      </main>
    )
  }

  if (data.years.length === 0) {
    return (
      <main className="flex-1 overflow-y-auto px-6 py-10">
        <div className="mx-auto max-w-[860px]">
          <h1 className="mb-4 text-[22px] font-extrabold tracking-tight">Deep Dive</h1>
          <div className="rounded-[14px] border border-gray-200 bg-white p-10 text-center text-[13px] text-gray-400">
            No backtest data yet. Run a backtest from the Backtest tab first.
          </div>
        </div>
      </main>
    )
  }

  if (data.years.length < 2) {
    return (
      <main className="flex-1 overflow-y-auto px-6 py-10">
        <div className="mx-auto max-w-[860px]">
          <h1 className="mb-4 text-[22px] font-extrabold tracking-tight">Deep Dive</h1>
          <div className="rounded-[14px] border border-gray-200 bg-white p-10 text-center text-[13px] text-gray-400">
            This backtest only spans one calendar year &mdash; there's nothing to compare yet. Run a longer backtest
            to use this page.
          </div>
        </div>
      </main>
    )
  }

  const overallMin = new Date(data.overall_min!)
  const overallMax = new Date(data.overall_max!)
  const allYears = data.years.map((y) => y.year)
  const allSelected = selectedYears.size === allYears.length

  const toggleYear = (year: number) => {
    setSelectedYears((prev) => {
      const next = new Set(prev)
      if (next.has(year)) next.delete(year)
      else next.add(year)
      return next
    })
  }

  const allStats = computeStats(data.years, new Set(allYears), overallMin, overallMax, true, fullResult)
  const selectedStats = computeStats(data.years, selectedYears, overallMin, overallMax, allSelected, fullResult)

  return (
    <main className="flex-1 overflow-y-auto px-6 py-10">
      <div className="mx-auto flex max-w-[860px] flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-[22px] font-extrabold tracking-tight">Deep Dive</h1>
          <p className="max-w-[680px] text-[13.5px] leading-relaxed text-gray-500">
            A single CAGR over a multi-year backtest can be carried almost entirely by one unusually strong (or weak)
            year. Uncheck a year below to see how much of the headline return it's really responsible for.
          </p>
        </div>

        {/* Year picker */}
        <div className="rounded-[14px] border border-gray-200 bg-white p-5 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
          <div className="mb-3 text-[12.5px] font-bold text-gray-700">Include which years?</div>
          <div className="flex flex-wrap gap-2">
            {data.years.map((y) => {
              const isSelected = selectedYears.has(y.year)
              return (
                <button
                  key={y.year}
                  onClick={() => toggleYear(y.year)}
                  className={`flex min-w-[76px] flex-col items-center gap-0.5 rounded-[10px] border px-4 py-2 ${
                    isSelected ? 'border-accent bg-accent text-white' : 'border-gray-200 bg-white text-gray-400'
                  }`}
                >
                  <span className="font-mono text-[13px] font-bold">{y.year}</span>
                  <span
                    className={`font-mono text-[10.5px] font-semibold ${
                      isSelected
                        ? y.return_pct >= 0
                          ? 'text-green-100'
                          : 'text-red-100'
                        : y.return_pct >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                    }`}
                  >
                    {formatPct(y.return_pct, 1)}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {allSelected && (
          <p className="text-xs text-gray-400">
            All years are currently selected, so both columns match. Uncheck a year above to see the difference.
          </p>
        )}

        {/* Comparison */}
        <div className="grid grid-cols-2 gap-5">
          <div className="flex flex-col gap-2.5">
            <div className="text-[13.5px] font-bold">All years</div>
            {allStats && <StatBlock stats={allStats} />}
          </div>
          <div className="flex flex-col gap-2.5">
            <div className="text-[13.5px] font-bold">
              Selected ({selectedYears.size} of {allYears.length} years)
            </div>
            {selectedStats ? (
              <StatBlock stats={selectedStats} highlighted />
            ) : (
              <div className="flex min-h-[140px] items-center justify-center rounded-xl border border-dashed border-gray-200">
                <span className="text-[12.5px] text-gray-400">Select at least one year to see its stats.</span>
              </div>
            )}
          </div>
        </div>

        {/* Stitched chart */}
        {selectedStats && (
          <div className="flex flex-col gap-2.5">
            <div>
              <div className="mb-0.5 text-[13.5px] font-bold">Stitched equity curve</div>
              <p className="max-w-[620px] text-xs leading-relaxed text-gray-400">
                The equity curve for just the years you selected, stitched together in order (each year picks up
                where the last one left off) &mdash; not calendar time, so gaps between selected years don't appear.
              </p>
            </div>
            <div className="rounded-[14px] border border-gray-200 bg-white p-5 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
              <svg viewBox="0 0 860 220" width="100%" height="220" style={{ display: 'block' }}>
                <line x1="40" y1="16" x2="40" y2="190" stroke="#EEEEF0" strokeWidth="1" />
                <line x1="40" y1="190" x2="840" y2="190" stroke="#EEEEF0" strokeWidth="1" />
                <polyline points={toPolyline(selectedStats.stitched)} fill="none" stroke="#3D5944" strokeWidth="2.25" />
              </svg>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
