import { useEffect, useState } from 'react'
import { missedOpportunitiesApi, type MissedOpportunities } from '../api'

function formatPct(n: number, digits = 2) {
  return `${n >= 0 ? '+' : ''}${n.toFixed(digits)}%`
}

export default function MissedOpportunitiesPage() {
  const [data, setData] = useState<MissedOpportunities | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    missedOpportunitiesApi
      .get()
      .then(setData)
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

  if (!data.available) {
    return (
      <main className="flex-1 overflow-y-auto px-6 py-10">
        <div className="mx-auto max-w-[920px]">
          <h1 className="mb-4 text-[22px] font-extrabold tracking-tight">Missed Opportunities</h1>
          <div className="rounded-[14px] border border-gray-200 bg-white p-10 text-center text-[13px] text-gray-400">
            No near-miss data yet. Run a backtest from the Backtest tab first &mdash; near_misses.csv is written
            alongside the trade results.
          </div>
        </div>
      </main>
    )
  }

  const ruleRows = data.rule_rows ?? []
  const topRows = data.top_rows ?? []
  const realizedAvg = data.realized_avg_profit ?? null

  return (
    <main className="flex-1 overflow-y-auto px-6 py-10">
      <div className="mx-auto flex max-w-[920px] flex-col gap-7">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-[22px] font-extrabold tracking-tight">Missed Opportunities</h1>
            {(data.strategy_name || data.exit_strategy_name) && (
              <div className="flex flex-wrap items-center gap-1.5">
                {data.strategy_name && (
                  <span className="rounded-full border border-accent-softBorder bg-accent-soft px-2.5 py-[3px] font-mono text-[11.5px] font-semibold text-accent-hover">
                    {data.strategy_name}
                  </span>
                )}
                {data.strategy_name && data.exit_strategy_name && <span className="text-[11px] text-gray-300">+</span>}
                {data.exit_strategy_name && (
                  <span className="rounded-full border border-gray-200 bg-gray-100 px-2.5 py-[3px] font-mono text-[11.5px] font-semibold text-gray-500">
                    {data.exit_strategy_name}
                  </span>
                )}
              </div>
            )}
          </div>
          <p className="max-w-[700px] text-[13.5px] leading-relaxed text-gray-500">
            Every day the backtest evaluates a stock, a stock that fails exactly one rule is logged as a near-miss
            along with what a simple 20-trading-day hold from the next day's open would have returned. This is not a
            trade the strategy took &mdash; it's what the rule that blocked it cost you, so you can see which filters
            are worth loosening instead of guessing.
          </p>
        </div>

        {/* By blocking rule */}
        <div className="flex flex-col gap-2">
          <div>
            <div className="mb-0.5 text-[15px] font-extrabold">By blocking rule</div>
            <p className="max-w-[660px] text-[12.5px] leading-relaxed text-gray-400">
              Sorted by average forward return, highest first. A rule near the top with a return and win rate clearly
              better than your realized trades is likely too tight.
            </p>
          </div>

          {realizedAvg !== null && (
            <div className="rounded-[9px] border border-accent-softBorder bg-accent-soft px-3.5 py-2.5 text-xs text-accent-hover">
              Your realized trades averaged{' '}
              <span className="font-mono font-bold">{formatPct(realizedAvg)}</span> profit with a{' '}
              <span className="font-mono font-bold">{data.realized_win_rate?.toFixed(0)}%</span> win rate &mdash;
              highlighted rows below outperformed what you actually captured.
            </div>
          )}

          <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                  <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                    Rule that blocked it
                  </th>
                  <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                    Near-misses
                  </th>
                  <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                    Avg 20-day forward return
                  </th>
                  <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                    Win rate
                  </th>
                </tr>
              </thead>
              <tbody>
                {ruleRows.map((row) => {
                  const beatsBenchmark = realizedAvg !== null && row.avg_forward_return_pct > realizedAvg
                  return (
                    <tr key={row.rule} className={`border-b border-gray-100 ${beatsBenchmark ? 'bg-accent-soft/40' : ''}`}>
                      <td className="flex items-center gap-2 px-4 py-2.5 text-[12.5px] text-gray-700">
                        {row.rule}
                        {beatsBenchmark && (
                          <span className="rounded-full bg-accent-soft px-1.5 py-0.5 font-mono text-[9.5px] font-bold tracking-wide text-accent">
                            BEATS REALIZED
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono text-xs text-gray-700">
                        {row.count.toLocaleString()}
                      </td>
                      <td
                        className={`px-4 py-2.5 text-right font-mono text-xs font-semibold ${
                          row.avg_forward_return_pct >= 0 ? 'text-green-700' : 'text-red-700'
                        }`}
                      >
                        {formatPct(row.avg_forward_return_pct)}
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono text-xs text-gray-700">
                        {row.win_rate_pct.toFixed(0)}%
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Biggest individual near-misses */}
        <div className="flex flex-col gap-2">
          <div>
            <div className="mb-0.5 text-[15px] font-extrabold">Biggest individual near-misses</div>
            <p className="max-w-[660px] text-[12.5px] leading-relaxed text-gray-400">
              The single biggest near-misses across all rules &mdash; concrete examples of what got away, not just
              the aggregate stats above.
            </p>
          </div>

          <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[700px] border-collapse">
                <thead>
                  <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                    <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                      Date
                    </th>
                    <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                      Symbol
                    </th>
                    <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                      Why it was rejected
                    </th>
                    <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                      Closeness
                    </th>
                    <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                      20-day forward return
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {topRows.map((row, i) => (
                    <tr key={i} className="border-b border-gray-100 hover:bg-[#FAFAFB]">
                      <td className="px-4 py-2.5 font-mono text-[11.5px] text-gray-500">{row.date}</td>
                      <td className="px-4 py-2.5 font-mono text-xs font-bold text-gray-900">{row.symbol}</td>
                      <td className="px-4 py-2.5 text-xs text-gray-600">{row.reason}</td>
                      <td className="px-4 py-2.5 text-right font-mono text-xs text-gray-400">
                        {row.closeness_score.toFixed(1)}
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono text-xs font-bold text-green-700">
                        {formatPct(row.forward_return_pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
