import { useEffect, useState } from 'react'
import { MARKET, formatCurrency } from '../market'
import { multiStrategyApi, type MultiStrategyRun, type MultiStrategyOption, type StrategyProgress, type StrategyVerdict } from '../api'

const VERDICT_LABEL: Record<StrategyVerdict, string> = {
  buy: 'Buy signal',
  near: 'Near miss',
  none: 'No signal',
  error: 'Could not run',
}

const VERDICT_PILL: Record<StrategyVerdict, string> = {
  buy: 'border-accent-softBorder bg-accent-soft text-accent',
  near: 'border-amber-200 bg-amber-50 text-amber-800',
  none: 'border-gray-200 bg-gray-100 text-gray-600',
  error: 'border-red-200 bg-red-50 text-red-700',
}

function formatValue(value: string | number | boolean | null): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(2)
  return String(value)
}

export default function MultiStrategy() {
  const [options, setOptions] = useState<MultiStrategyOption[] | null>(null)
  const [contextDate, setContextDate] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [symbol, setSymbol] = useState('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [run, setRun] = useState<MultiStrategyRun | null>(null)
  const [progress, setProgress] = useState<Record<string, StrategyProgress>>({})
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  useEffect(() => {
    multiStrategyApi
      .strategies()
      .then((data) => {
        setOptions(data.strategies)
        setContextDate(data.context_date)
        setSelected(new Set(data.strategies.filter((s) => s.supported).map((s) => s.key)))
      })
      .catch((err) => setError(err.message))
  }, [])

  const toggle = (key: string) =>
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })

  const toggleExpanded = (key: string) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })

  const contextIsFresh = contextDate === new Date().toLocaleDateString('en-CA')
  const canRun = symbol.trim() !== '' && selected.size > 0 && !running

  const onRun = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canRun) return
    setRunning(true)
    setError(null)
    setProgress(Object.fromEntries([...selected].map((key) => [key, { key, pct: 0, stage: 'Queued' }])))
    try {
      const result = await multiStrategyApi.runStream(symbol.trim(), [...selected], (p) =>
        setProgress((prev) => ({ ...prev, [p.key]: p })),
      )
      setRun(result)
      setContextDate(result.context_date)
      setExpanded(new Set())
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setRunning(false)
    }
  }

  const resultByKey = new Map(run?.results.map((r) => [r.key, r]))
  const shown = options?.filter((o) => resultByKey.has(o.key)) ?? []
  const count = (v: StrategyVerdict) => run?.results.filter((r) => r.status === v).length ?? 0
  const ran = run ? run.results.filter((r) => r.status !== 'error').length : 0

  return (
    <main className="flex-1 overflow-y-auto px-6 py-8">
      <div className="mx-auto flex max-w-[1180px] flex-col gap-5">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div className="flex flex-col gap-1">
            <h1 className="text-[22px] font-extrabold tracking-tight">Multi-Strategy</h1>
            <p className="max-w-[560px] text-[13.5px] leading-relaxed text-gray-500">
              Run one stock through several saved strategies at once and compare what each says.
            </p>
          </div>
          <form onSubmit={onRun} className="flex items-end gap-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="ms-symbol" className="text-[11px] font-bold uppercase tracking-wide text-gray-500">
                {MARKET.symbolLabel}
              </label>
              <input
                id="ms-symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder={MARKET.symbolPlaceholder}
                autoComplete="off"
                className="h-[42px] w-[220px] rounded-lg border border-gray-200 bg-white px-3 font-mono text-[15px] font-medium uppercase text-gray-900 placeholder:normal-case placeholder:text-gray-300 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent-softBorder"
              />
            </div>
            <button
              type="submit"
              disabled={!canRun}
              className="h-[42px] min-w-[190px] rounded-lg bg-accent px-5 text-sm font-semibold text-white hover:bg-accent-hover disabled:cursor-not-allowed disabled:bg-gray-300"
            >
              {running ? `Running ${selected.size}…` : `Run ${selected.size} ${selected.size === 1 ? 'strategy' : 'strategies'}`}
            </button>
          </form>
        </div>

        {error && (
          <div role="alert" className="rounded-[10px] border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-700">
            {error}
          </div>
        )}

        <div className="flex items-start gap-5">
          <aside className="flex w-[320px] flex-shrink-0 flex-col gap-2.5 rounded-[14px] border border-gray-200 bg-white p-5 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
            <div className="mb-1 flex items-baseline justify-between">
              <h2 className="text-[11px] font-bold uppercase tracking-wide text-gray-500">Strategies to run</h2>
              {options && (
                <span className="font-mono text-xs text-gray-500">
                  {selected.size} of {options.length}
                </span>
              )}
            </div>
            {!options && !error && <p className="text-[13px] text-gray-400">Loading strategies…</p>}
            {options?.length === 0 && (
              <p className="text-[13px] text-gray-400">No saved strategies yet. Save one from the Rules tab first.</p>
            )}
            {options?.map((o) => {
              const on = selected.has(o.key)
              return (
                <button
                  key={o.key}
                  type="button"
                  role="switch"
                  aria-checked={on}
                  disabled={!o.supported}
                  onClick={() => toggle(o.key)}
                  className={`flex items-start gap-3 rounded-[10px] border px-3.5 py-3 text-left disabled:cursor-not-allowed disabled:opacity-60 ${
                    on ? 'border-accent-softBorder bg-accent-soft' : 'border-gray-200 bg-white hover:bg-gray-50'
                  }`}
                >
                  <span
                    className={`mt-px flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-[5px] border-[1.5px] ${
                      on ? 'border-accent bg-accent' : 'border-gray-400 bg-white'
                    }`}
                  >
                    {on && (
                      <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="#FFFFFF" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M2.5 7.5l3 3 6-7" />
                      </svg>
                    )}
                  </span>
                  <span className="flex flex-col gap-0.5">
                    <span className="text-[13.5px] font-bold leading-snug text-gray-900">{o.name}</span>
                    <span className="font-mono text-[11px] text-gray-500">
                      {o.unsupported_reason ?? `${o.versions} saved ${o.versions === 1 ? 'version' : 'versions'} · runs newest`}
                    </span>
                  </span>
                </button>
              )
            })}
            <p className="mt-2 border-t border-gray-100 pt-3.5 text-xs leading-relaxed text-gray-500">
              Each strategy runs with its newest saved rules. Nothing is bought or sold from this tab.
              {!contextIsFresh && (
                <>
                  {' '}
                  The first run each day also builds today&apos;s market context (sector ranks and breadth) across the
                  whole universe, which can take a few minutes.
                </>
              )}
            </p>
          </aside>

          <section className="flex min-w-0 flex-1 flex-col gap-4">
            {running && (
              <div className="flex flex-col gap-3 rounded-[14px] border border-gray-200 bg-white p-5 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
                <h2 className="text-[11px] font-bold uppercase tracking-wide text-gray-500">
                  Running {symbol.trim().toUpperCase()}
                </h2>
                {!contextIsFresh && (
                  <p className="text-xs text-gray-500">
                    Today&apos;s market context is being built first, so the early part of each bar is slow.
                  </p>
                )}
                {options
                  ?.filter((o) => selected.has(o.key))
                  .map((o) => {
                    const p = progress[o.key] ?? { pct: 0, stage: 'Queued' }
                    return (
                      <div key={o.key} className="flex flex-col gap-1.5">
                        <div className="flex items-baseline justify-between gap-4">
                          <span className="text-[13.5px] font-bold text-gray-900">{o.name}</span>
                          <span className="font-mono text-xs text-gray-500">{Math.round(p.pct)}%</span>
                        </div>
                        <div
                          role="progressbar"
                          aria-label={`${o.name} progress`}
                          aria-valuemin={0}
                          aria-valuemax={100}
                          aria-valuenow={Math.round(p.pct)}
                          aria-valuetext={p.stage}
                          className="h-2 overflow-hidden rounded-full bg-gray-100"
                        >
                          <div className="h-full rounded-full bg-accent transition-[width] duration-300" style={{ width: `${p.pct}%` }} />
                        </div>
                        <span className="text-xs text-gray-500">{p.stage}</span>
                      </div>
                    )
                  })}
              </div>
            )}

            {!running && !run && (
              <div className="rounded-[14px] border border-gray-200 bg-white p-10 text-center text-[13px] text-gray-400 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
                Enter a symbol and run it to see each strategy&apos;s verdict here.
              </div>
            )}

            {!running && run && (
              <>
                <div className="flex flex-wrap items-center gap-6 rounded-[14px] border border-gray-200 bg-white px-5 py-4 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
                  <div className="flex flex-col gap-0.5">
                    <span className="font-mono text-[22px] font-semibold">{run.symbol}</span>
                    <span className="text-xs text-gray-500">
                      Close {formatCurrency(run.last_close)} · {run.last_date}
                    </span>
                  </div>
                  <div className="h-10 w-px bg-gray-200" />
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[11px] font-bold uppercase tracking-wide text-gray-500">Agreement</span>
                    <span className="text-lg font-extrabold tracking-tight text-accent">
                      {count('buy')} of {ran} strategies signal
                    </span>
                  </div>
                  <div className="ml-auto flex flex-wrap gap-2 text-[12.5px] font-bold">
                    <span className={`rounded-full border px-3 py-1.5 ${VERDICT_PILL.buy}`}>{count('buy')} signal</span>
                    <span className={`rounded-full border px-3 py-1.5 ${VERDICT_PILL.near}`}>{count('near')} near miss</span>
                    <span className={`rounded-full border px-3 py-1.5 ${VERDICT_PILL.none}`}>{count('none')} no signal</span>
                  </div>
                </div>

                {!run.in_universe && (
                  <p className="rounded-[10px] border border-amber-200 bg-amber-50 px-4 py-2.5 text-[12.5px] text-amber-800">
                    {run.symbol} is not in the stock universe, so its sector rank is unknown (treated as rank 99) and any
                    sector rule will fail.
                  </p>
                )}

                <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                  {shown.map((o) => {
                    const r = resultByKey.get(o.key)!
                    const entryLow = r.details['Ideal Entry Price Low']
                    const entryHigh = r.details['Ideal Entry Price High']
                    const isOpen = expanded.has(o.key)
                    const detailEntries = Object.entries(r.details)
                    return (
                      <article key={o.key} className="flex flex-col gap-3.5 rounded-[14px] border border-gray-200 bg-white p-5 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
                        <div className="flex items-start justify-between gap-4">
                          <h3 className="text-[15px] font-bold leading-snug">{o.name}</h3>
                          <span className={`flex-shrink-0 rounded-full border px-2.5 py-1 text-xs font-bold ${VERDICT_PILL[r.status]}`}>
                            {VERDICT_LABEL[r.status]}
                          </span>
                        </div>

                        {r.status === 'error' && <p className="text-[13px] text-red-700">{r.error}</p>}

                        {r.status !== 'error' && (
                          <>
                            {r.failed_rules.length === 0 ? (
                              <p className="text-[13px] text-gray-700">Every rule passed.</p>
                            ) : (
                              <div className="flex flex-col gap-2">
                                <span className="text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                                  Failed {r.failed_rules.length === 1 ? 'rule' : 'rules'}
                                </span>
                                {r.failed_rules.map((rule) => (
                                  <div key={rule} className="flex items-start gap-2.5 text-[13px] leading-snug text-red-700">
                                    <span className="mt-px flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full bg-red-600">
                                      <svg width="9" height="9" viewBox="0 0 10 10" fill="none" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round">
                                        <path d="M2.5 2.5l5 5M7.5 2.5l-5 5" />
                                      </svg>
                                    </span>
                                    {rule}
                                  </div>
                                ))}
                              </div>
                            )}

                            <div className="grid grid-cols-2 gap-3 border-t border-gray-100 pt-3.5">
                              <div className="flex flex-col gap-0.5">
                                <span className="text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Closeness score</span>
                                <span className="font-mono text-[13px] font-medium">{r.closeness_score === null ? '—' : r.closeness_score.toFixed(1)}</span>
                              </div>
                              <div className="flex flex-col gap-0.5">
                                <span className="text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Ideal entry</span>
                                <span className="font-mono text-[13px] font-medium">
                                  {typeof entryLow === 'number' && typeof entryHigh === 'number'
                                    ? `${formatCurrency(entryLow)} – ${formatCurrency(entryHigh)}`
                                    : '—'}
                                </span>
                              </div>
                            </div>

                            {detailEntries.length > 0 && (
                              <div>
                                <button
                                  type="button"
                                  onClick={() => toggleExpanded(o.key)}
                                  aria-expanded={isOpen}
                                  className="text-xs font-semibold text-accent hover:text-accent-hover"
                                >
                                  {isOpen ? 'Hide calculated metrics' : `Show calculated metrics (${detailEntries.length})`}
                                </button>
                                {isOpen && (
                                  <dl className="mt-2.5 grid grid-cols-[1fr_auto] gap-x-4 gap-y-1.5 text-xs">
                                    {detailEntries.map(([k, v]) => (
                                      <div key={k} className="contents">
                                        <dt className="text-gray-500">{k}</dt>
                                        <dd className="text-right font-mono text-gray-900">{formatValue(v)}</dd>
                                      </div>
                                    ))}
                                  </dl>
                                )}
                              </div>
                            )}
                          </>
                        )}
                      </article>
                    )
                  })}
                </div>
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  )
}
