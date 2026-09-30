import { useEffect, useState } from 'react'
import { fetchReport, holdingsApi, makeMarkdownFileApi, streamJob, type CellValue, type Holding, type ReportResponse } from '../api'
import MarkdownEditor from '../components/MarkdownEditor'
import VersionDrawer from '../components/VersionDrawer'

const exitRulesApi = makeMarkdownFileApi('/exit-rules')

function declaredExitStrategyName(content: string) {
  const match = content.match(/Exit Strategy Name:\s*(.+)/)
  return match ? match[1].trim() : null
}

function formatCell(value: CellValue): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(2)
  return String(value)
}

let nextRowId = 0
type HoldingRow = Holding & { rowId: number }

export default function Sell() {
  const [exitOpen, setExitOpen] = useState(false)
  const [exitContent, setExitContent] = useState('')
  const [exitLoaded, setExitLoaded] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [exitVersions, setExitVersions] = useState<string[]>([])
  const [holdings, setHoldings] = useState<HoldingRow[]>([])
  const [holdingsLoaded, setHoldingsLoaded] = useState(false)
  const [checking, setChecking] = useState(false)

  const [report, setReport] = useState<ReportResponse | null>(null)

  const refreshExitVersions = () =>
    exitRulesApi
      .listBackups()
      .then((groups) => setExitVersions(Object.values(groups).flat().sort()))
      .catch(() => {})

  useEffect(() => {
    refreshExitVersions()

    exitRulesApi
      .get()
      .then((res) => {
        setExitContent(res.content)
        setExitLoaded(true)
      })
      .catch((err) => setError(err.message))

    holdingsApi
      .get()
      .then((res) => {
        setHoldings(res.holdings.map((h) => ({ ...h, rowId: nextRowId++ })))
        setHoldingsLoaded(true)
      })
      .catch((err) => setError(err.message))

    fetchReport('/sell-report')
      .then((res) => setReport(res.rows.length > 0 ? res : null))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!message) return
    const timeout = setTimeout(() => setMessage(null), 4000)
    return () => clearTimeout(timeout)
  }, [message])

  useEffect(() => {
    if (!holdingsLoaded) return
    const ready = holdings.filter((h) => h.Symbol && h.EntryPrice !== '' && h.EntryDate)
    const timeout = setTimeout(() => {
      holdingsApi.save(ready.map(({ rowId: _rowId, ...h }) => h)).catch((err) => setError(err.message))
    }, 500)
    return () => clearTimeout(timeout)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [holdings])

  const runGenerate = () => {
    setGenerating(true)
    streamJob('/jobs/generate-exit-strategy', () => {})
      .then((code) => {
        setMessage(code === 0 ? 'generated_exit_strategy.py updated.' : `generate_exit_strategy.py exited with code ${code}.`)
      })
      .catch((err) => setError(err.message))
      .finally(() => setGenerating(false))
  }

  const handleSaveExit = () => {
    setSaving(true)
    exitRulesApi
      .save(exitContent)
      .then((res) => {
        setMessage(res.backed_up_as ? `Saved exit_rules.md (previous version backed up as ${res.backed_up_as})` : 'Saved exit_rules.md')
        refreshExitVersions()
      })
      .catch((err) => setError(err.message))
      .finally(() => setSaving(false))
  }

  const updateHolding = (rowId: number, field: keyof Holding, value: string) => {
    setHoldings((prev) =>
      prev.map((h) => {
        if (h.rowId !== rowId) return h
        if (field === 'EntryPrice' || field === 'CurrentPrice') {
          return { ...h, [field]: value === '' ? '' : Number(value) }
        }
        return { ...h, [field]: value }
      }),
    )
  }

  const addHolding = () => {
    setHoldings((prev) => [...prev, { rowId: nextRowId++, Symbol: '', EntryPrice: '', EntryDate: '', CurrentPrice: '', ExitRule: '' }])
  }

  const removeHolding = (rowId: number) => {
    setHoldings((prev) => prev.filter((h) => h.rowId !== rowId))
  }

  const holdingsReady = holdings.filter((h) => h.Symbol && h.EntryPrice !== '' && h.EntryDate)

  const checkExitSignals = () => {
    if (holdingsReady.length === 0) return
    setChecking(true)
    streamJob('/jobs/check-exit-signals', () => {})
      .then((code) => {
        if (code === 0) {
          setMessage('Sell check complete.')
          return fetchReport('/sell-report').then((res) => setReport(res.rows.length > 0 ? res : null))
        }
        setError(`sell_screener.py exited with code ${code}.`)
      })
      .catch((err) => setError(err.message))
      .finally(() => setChecking(false))
  }

  const exitStrategyName = declaredExitStrategyName(exitContent)

  return (
    <div className="flex min-h-0 flex-1">
      <main className="flex-1 overflow-y-auto px-6 py-10">
        <div className="mx-auto flex max-w-[860px] flex-col gap-7">
          <div className="flex flex-col gap-2">
            <h1 className="text-[22px] font-extrabold tracking-tight">Sell</h1>
            <p className="max-w-[660px] text-[13.5px] leading-relaxed text-gray-500">
              Runs the exit logic in generated_exit_strategy.py against the stocks you currently hold. For each
              holding, checks whether your exit strategy would already have fired between your entry date and today.
            </p>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
          {message && <p className="text-sm text-green-700">{message}</p>}

          {/* Exit strategy (collapsible) */}
          <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
            <button
              onClick={() => setExitOpen((v) => !v)}
              className="flex w-full items-center justify-between px-[18px] py-4 hover:bg-gray-50"
            >
              <div className="flex items-center gap-2.5">
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#9AA0AC"
                  strokeWidth="2.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  style={{ transform: exitOpen ? 'rotate(0deg)' : 'rotate(-90deg)' }}
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
                <div className="text-left">
                  <div className="text-[14px] font-bold">Exit strategy rules</div>
                  <div className="mt-0.5 font-mono text-[11px] text-gray-400">exit_rules.md</div>
                </div>
              </div>
              {exitStrategyName && (
                <span className="rounded-full border border-accent-softBorder bg-accent-soft px-2.5 py-[3px] font-mono text-[11.5px] font-semibold text-accent-hover">
                  {exitStrategyName}
                </span>
              )}
            </button>

            {exitOpen && (
              <div className="border-t border-gray-100">
                {!exitLoaded ? (
                  <p className="p-[18px] text-sm text-gray-500">Loading...</p>
                ) : (
                  <MarkdownEditor
                    value={exitContent}
                    onChange={setExitContent}
                    height={300}
                    toolbarExtra={
                      <div className="flex items-center gap-2">
                        <button
                          onClick={runGenerate}
                          disabled={generating}
                          className="flex items-center gap-1.5 rounded-[9px] border border-gray-200 bg-white px-3.5 py-2 text-[12.5px] font-semibold text-gray-900 hover:bg-gray-50 disabled:opacity-50"
                        >
                          {generating ? 'Generating...' : 'Generate exit strategy'}
                        </button>
                        <button
                          onClick={handleSaveExit}
                          disabled={saving}
                          className="rounded-[9px] bg-accent px-4 py-2 text-[12.5px] font-semibold text-white hover:brightness-95 disabled:opacity-50"
                        >
                          {saving ? 'Saving...' : 'Save exit_rules.md'}
                        </button>
                      </div>
                    }
                    footer={
                      <div className="flex items-center justify-between border-t border-gray-100 px-4 py-2.5">
                        <span className="text-[11.5px] text-gray-400">{exitContent.split('\n').length} lines</span>
                        <span className="text-[11.5px] text-gray-400">exit_rules.md</span>
                      </div>
                    }
                  />
                )}
              </div>
            )}
          </div>

          <div className="flex items-start justify-between gap-5">
            <div className="flex flex-col gap-1">
              <div className="text-[13px] font-bold">Exit strategy version history</div>
              <p className="max-w-[480px] text-[12.5px] leading-relaxed text-gray-500">
                Backups are created automatically whenever you save a changed exit_rules.md.
              </p>
            </div>
            <button
              onClick={() => setDrawerOpen(true)}
              className="flex flex-shrink-0 items-center gap-2 whitespace-nowrap rounded-[9px] border border-gray-200 bg-white px-3.5 py-2 text-[13px] font-semibold text-gray-900 hover:bg-gray-50"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="9" />
                <polyline points="12 7 12 12 15 15" />
              </svg>
              Browse exit strategy versions
            </button>
          </div>

          <hr className="border-gray-200" />

          {/* Holdings */}
          <div className="flex flex-col gap-1.5">
            <div className="text-[15px] font-extrabold">Your holdings</div>
            <p className="max-w-[640px] text-[12.5px] leading-relaxed text-gray-500">
              Add each open position below and optionally pick a saved exit rule version for it (default: the current exit_rules.md). Holdings are saved to data/holdings.csv as you edit.
            </p>
          </div>

          <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                  <th className="px-3 py-2 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Symbol</th>
                  <th className="px-3 py-2 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Entry Price</th>
                  <th className="px-3 py-2 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Entry Date</th>
                  <th className="px-3 py-2 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Current Price</th>
                  <th className="px-3 py-2 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Exit Rule</th>
                  <th className="w-10" />
                </tr>
              </thead>
              <tbody>
                {holdings.map((h) => (
                  <tr key={h.rowId} className="border-b border-gray-100">
                    <td className="p-[3px] px-2">
                      <input
                        className="w-full rounded-md border border-transparent px-1.5 py-1 font-mono text-[12.5px] hover:border-gray-200 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10"
                        type="text"
                        placeholder="SYMBOL"
                        value={h.Symbol}
                        onChange={(e) => updateHolding(h.rowId, 'Symbol', e.target.value.toUpperCase())}
                      />
                    </td>
                    <td className="p-[3px] px-2">
                      <input
                        className="w-full rounded-md border border-transparent px-1.5 py-1 text-right font-mono text-[12.5px] hover:border-gray-200 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10"
                        type="number"
                        placeholder="0.00"
                        value={h.EntryPrice}
                        onChange={(e) => updateHolding(h.rowId, 'EntryPrice', e.target.value)}
                      />
                    </td>
                    <td className="p-[3px] px-2">
                      <input
                        className="w-full rounded-md border border-transparent px-1.5 py-1 font-mono text-[12.5px] hover:border-gray-200 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10"
                        type="date"
                        value={h.EntryDate}
                        onChange={(e) => updateHolding(h.rowId, 'EntryDate', e.target.value)}
                      />
                    </td>
                    <td className="p-[3px] px-2">
                      <input
                        className="w-full rounded-md border border-transparent px-1.5 py-1 text-right font-mono text-[12.5px] hover:border-gray-200 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10"
                        type="number"
                        placeholder="optional"
                        value={h.CurrentPrice ?? ''}
                        onChange={(e) => updateHolding(h.rowId, 'CurrentPrice', e.target.value)}
                      />
                    </td>
                    <td className="p-[3px] px-2">
                      <select
                        className="w-full max-w-[220px] rounded-md border border-transparent bg-transparent px-1 py-1 font-mono text-[12px] hover:border-gray-200 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10"
                        value={h.ExitRule ?? ''}
                        onChange={(e) => updateHolding(h.rowId, 'ExitRule', e.target.value)}
                      >
                        <option value="">Current exit_rules.md</option>
                        {h.ExitRule && !exitVersions.includes(h.ExitRule) && (
                          <option value={h.ExitRule}>{h.ExitRule} (missing)</option>
                        )}
                        {exitVersions.map((v) => (
                          <option key={v} value={v}>
                            {v.replace(/.md$/, '')}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-2 text-center">
                      <button
                        onClick={() => removeHolding(h.rowId)}
                        className="flex h-[26px] w-[26px] items-center justify-center rounded-md hover:bg-gray-100"
                      >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#9AA0AC" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="18" y1="6" x2="6" y2="18" />
                          <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button
              onClick={addHolding}
              className="flex items-center gap-1.5 border-t border-gray-100 px-3.5 py-2.5 text-gray-500 hover:bg-gray-50"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              <span className="text-[12.5px] font-semibold">Add holding</span>
            </button>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={checkExitSignals}
              disabled={holdingsReady.length === 0 || checking}
              className="rounded-[9px] bg-accent px-4 py-2.5 text-[13px] font-semibold text-white hover:brightness-95 disabled:cursor-default disabled:bg-gray-200 disabled:text-gray-400"
            >
              {checking ? 'Checking exit signals...' : 'Check exit signals'}
            </button>
            {holdingsReady.length === 0 && (
              <span className="text-xs text-gray-400">Add at least one holding above before checking exit signals.</span>
            )}
          </div>

          {/* Recommendations */}
          {report && (
            <>
              <hr className="border-gray-200" />
              <div className="text-[15px] font-extrabold">Recommendations</div>
              <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                        {report.columns.map((col) => (
                          <th
                            key={col}
                            className={`whitespace-nowrap px-3 py-2 text-[10.5px] font-bold uppercase tracking-wide text-gray-400 ${
                              col === 'Symbol' || col === 'Recommendation' || col === 'Reason' ? 'text-left' : 'text-right'
                            }`}
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {report.rows.map((row, i) => (
                        <tr key={i} className="border-b border-gray-100 hover:bg-[#FAFAFB]">
                          {report.columns.map((col) => {
                            if (col === 'Symbol') {
                              return (
                                <td key={col} className="whitespace-nowrap px-3 py-2.5 font-mono text-xs font-bold text-gray-900">
                                  {row[col]}
                                </td>
                              )
                            }
                            if (col === 'Recommendation') {
                              const isSell = row[col] === 'SELL'
                              const isHold = row[col] === 'HOLD'
                              return (
                                <td key={col} className="whitespace-nowrap px-3 py-2.5">
                                  <span
                                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                                      isSell ? 'bg-red-100 text-red-700' : isHold ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                                    }`}
                                  >
                                    {formatCell(row[col])}
                                  </span>
                                </td>
                              )
                            }
                            if (col === 'ReturnPct') {
                              const value = row[col]
                              const numeric = typeof value === 'number' ? value : null
                              return (
                                <td
                                  key={col}
                                  className={`whitespace-nowrap px-3 py-2.5 text-right font-mono text-xs font-semibold ${
                                    numeric === null ? 'text-gray-400' : numeric >= 0 ? 'text-green-700' : 'text-red-700'
                                  }`}
                                >
                                  {numeric === null ? '—' : `${numeric >= 0 ? '+' : ''}${numeric.toFixed(2)}%`}
                                </td>
                              )
                            }
                            const isNumeric = typeof row[col] === 'number'
                            return (
                              <td
                                key={col}
                                className={`whitespace-nowrap px-3 py-2.5 text-xs text-gray-700 ${
                                  isNumeric ? 'text-right font-mono' : col === 'Reason' ? 'max-w-[280px] overflow-hidden text-ellipsis text-gray-500' : ''
                                }`}
                              >
                                {formatCell(row[col])}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      </main>

      <VersionDrawer
        api={exitRulesApi}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        onRestored={(restoredContent) => setExitContent(restoredContent)}
        onMessage={setMessage}
      />
    </div>
  )
}
