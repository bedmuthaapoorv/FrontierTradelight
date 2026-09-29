import { useEffect, useState } from 'react'
import { eventWatcherApi, type EventWatcherState, type InvestorMeetsState, type ScannedReleaseRow } from '../api'
import KeywordDrawer from '../components/KeywordDrawer'

function formatDate(iso: string) {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function defaultHistoricalDate() {
  // date input wants "YYYY-MM-DD".
  return new Date().toISOString().slice(0, 10)
}

export default function EventWatcher() {
  const [data, setData] = useState<EventWatcherState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null)
  const [historicalDate, setHistoricalDate] = useState(defaultHistoricalDate())
  const [fetchingHistorical, setFetchingHistorical] = useState(false)
  const [historicalMessage, setHistoricalMessage] = useState<string | null>(null)
  const [keywordDrawerOpen, setKeywordDrawerOpen] = useState(false)
  const [scanned, setScanned] = useState<ScannedReleaseRow[] | null>(null)
  const [scannedOpen, setScannedOpen] = useState(false)
  const [investorMeets, setInvestorMeets] = useState<InvestorMeetsState | null>(null)
  const [investorMeetsError, setInvestorMeetsError] = useState<string | null>(null)
  const [refreshingMeets, setRefreshingMeets] = useState(false)
  const [meetsRefreshMessage, setMeetsRefreshMessage] = useState<string | null>(null)

  const load = () => {
    eventWatcherApi
      .get()
      .then(setData)
      .catch((err) => setError(err.message))
    eventWatcherApi
      .getScanned()
      .then((r) => setScanned(r.scanned))
      .catch(() => setScanned([]))
    eventWatcherApi
      .getInvestorMeets()
      .then(setInvestorMeets)
      .catch((err) => setInvestorMeetsError(err.message))
  }

  useEffect(load, [])

  const onRefreshInvestorMeets = async () => {
    setRefreshingMeets(true)
    setMeetsRefreshMessage(null)
    try {
      const result = await eventWatcherApi.refreshInvestorMeets()
      if (result.status === 'ok') {
        setMeetsRefreshMessage(`Scanned ${result.scanned ?? 0} filing(s), found ${result.new_filings ?? 0} new.`)
      } else {
        setMeetsRefreshMessage(`Refresh failed: ${result.message}`)
      }
      load()
    } catch (err) {
      setMeetsRefreshMessage(err instanceof Error ? err.message : String(err))
    } finally {
      setRefreshingMeets(false)
    }
  }

  const onRefresh = async () => {
    setRefreshing(true)
    setRefreshMessage(null)
    try {
      const result = await eventWatcherApi.refresh()
      if (result.status === 'ok') {
        setRefreshMessage(`Scanned ${result.scanned ?? 0} releases, found ${result.new_matches ?? 0} new match(es).`)
      } else {
        setRefreshMessage(`Refresh failed: ${result.message}`)
      }
      load()
    } catch (err) {
      setRefreshMessage(err instanceof Error ? err.message : String(err))
    } finally {
      setRefreshing(false)
    }
  }

  const onFetchHistorical = async () => {
    setFetchingHistorical(true)
    setHistoricalMessage(null)
    try {
      const result = await eventWatcherApi.fetchHistorical(historicalDate)
      if (result.status === 'ok') {
        setHistoricalMessage(
          `${result.defence_releases_that_day ?? 0} real Defence release(s) on ${historicalDate}, ${
            result.new_matches ?? 0
          } matched.`,
        )
      } else {
        setHistoricalMessage(`Lookup failed: ${result.message}`)
      }
      load()
    } catch (err) {
      setHistoricalMessage(err instanceof Error ? err.message : String(err))
    } finally {
      setFetchingHistorical(false)
    }
  }

  const onClearHistorical = async () => {
    try {
      const result = await eventWatcherApi.clearHistorical()
      setHistoricalMessage(`Cleared ${result.removed} historical row(s).`)
      load()
    } catch (err) {
      setHistoricalMessage(err instanceof Error ? err.message : String(err))
    }
  }

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

  const watchlistEntries = Object.entries(data.watchlist)
  const eventTypeStats = Object.entries(data.event_type_stats ?? {})

  const formatEventType = (t: string) => t.replace(/_/g, ' ')
  const fmtPct = (v: number | null) => (v === null ? '—' : `${v > 0 ? '+' : ''}${v.toFixed(1)}%`)

  return (
    <main className="flex-1 overflow-y-auto px-6 py-10">
      <div className="mx-auto flex max-w-[1280px] items-start gap-6">
      <div className="flex min-w-0 flex-1 flex-col gap-7">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h1 className="text-[22px] font-extrabold tracking-tight">Event Watcher</h1>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setScannedOpen((v) => !v)}
                className="rounded-[8px] border border-gray-300 bg-white px-3.5 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              >
                {scannedOpen ? 'Hide all releases' : `All releases scanned${scanned ? ` (${scanned.length})` : ''}`}
              </button>
              <button
                onClick={() => setKeywordDrawerOpen(true)}
                className="rounded-[8px] border border-gray-300 bg-white px-3.5 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              >
                Edit keywords
              </button>
              <button
                onClick={onRefresh}
                disabled={refreshing}
                className="rounded-[8px] bg-accent px-3.5 py-2 text-xs font-semibold text-white hover:bg-accent-hover disabled:opacity-50"
              >
                {refreshing ? 'Checking PIB...' : 'Check PIB now'}
              </button>
            </div>
          </div>
          <p className="max-w-[700px] text-[13.5px] leading-relaxed text-gray-500">
            Scans the Ministry of Defence's PIB press releases for naval commissioning/induction announcements that
            name a listed shipbuilder &mdash; the same kind of event (INS Malvan's commissioning) that lined up with
            Cochin Shipyard's Jul&ndash;Aug 2026 rally. This is a news signal, entirely separate from the backtest
            engine: it never feeds rules.md or the backtester, it only surfaces a manual candidate here.
          </p>
          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-400">
            <span>
              Last checked:{' '}
              <span className="font-mono text-gray-600">{data.last_checked ? formatDate(data.last_checked) : 'never'}</span>
            </span>
            {data.last_error && <span className="text-red-600">Last check failed: {data.last_error}</span>}
          </div>
          {refreshMessage && <p className="text-xs text-gray-500">{refreshMessage}</p>}
        </div>

        <div className="flex flex-col gap-2 rounded-[14px] border border-gray-200 bg-white p-4">
          <div className="mb-0.5 text-[15px] font-extrabold">Look up a past date</div>
          <p className="max-w-[660px] text-[12.5px] leading-relaxed text-gray-400">
            The live feed only covers roughly the last 8 days. For anything older, this pulls a real historical
            snapshot of the same feed from its source repo's own commit history on GitHub &mdash; real PIB releases,
            real dates, real links, not synthetic data &mdash; and runs the same Ministry-of-Defence + keyword/symbol
            match against whatever was actually published that day. Rows land tagged{' '}
            <span className="font-mono font-semibold text-gray-600">HISTORICAL</span>, distinct from live{' '}
            <span className="font-mono font-semibold text-gray-600">LIVE</span> matches but equally real.
          </p>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <input
              type="date"
              value={historicalDate}
              onChange={(e) => setHistoricalDate(e.target.value)}
              className="rounded-[8px] border border-gray-300 px-2.5 py-1.5 text-xs text-gray-700"
            />
            <button
              onClick={onFetchHistorical}
              disabled={fetchingHistorical}
              className="rounded-[8px] border border-gray-300 bg-white px-3.5 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              {fetchingHistorical ? 'Fetching...' : 'Fetch that date'}
            </button>
            <button
              onClick={onClearHistorical}
              className="rounded-[8px] px-3 py-2 text-xs font-semibold text-gray-400 hover:text-red-600"
            >
              Clear historical rows
            </button>
          </div>
          {historicalMessage && <p className="text-xs text-gray-500">{historicalMessage}</p>}
        </div>

        <div className="flex flex-col gap-2">
          <div className="mb-0.5 text-[15px] font-extrabold">Watchlist</div>
          <div className="flex flex-wrap gap-1.5">
            {watchlistEntries.map(([symbol, name]) => (
              <span
                key={symbol}
                className="rounded-full border border-gray-200 bg-gray-100 px-2.5 py-[3px] font-mono text-[11.5px] font-semibold text-gray-500"
                title={name}
              >
                {symbol}
              </span>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <div>
            <div className="mb-0.5 text-[15px] font-extrabold">Event-type calibration</div>
            <p className="max-w-[660px] text-[12.5px] leading-relaxed text-gray-400">
              What each event type's Signal number is actually based on. Median CAR shows &ldquo;insufficient
              data&rdquo; until enough matched instances exist &mdash; a median of one or two points isn&rsquo;t a
              calibrated estimate yet, so it&rsquo;s withheld rather than shown as one. The Ceiling column on the
              table below isn&rsquo;t estimated from this local history either &mdash; it's the announcement day&rsquo;s
              own close versus the close right before it, an already-observed number rather than a projection.
            </p>
          </div>
          {eventTypeStats.length === 0 ? (
            <div className="rounded-[14px] border border-gray-200 bg-white p-6 text-center text-[13px] text-gray-400">
              No matched events yet.
            </div>
          ) : (
            <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] border-collapse">
                  <thead>
                    <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                      {['Event type', 'n', 'Median CAR'].map(
                        (h) => (
                          <th
                            key={h}
                            className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400"
                          >
                            {h}
                          </th>
                        ),
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {eventTypeStats.map(([eventType, s]) => (
                      <tr key={eventType} className="border-b border-gray-100">
                        <td className="px-4 py-2.5 text-xs font-semibold capitalize text-gray-700">
                          {formatEventType(eventType)}
                        </td>
                        <td className="px-4 py-2.5 font-mono text-xs text-gray-500">{s.n}</td>
                        <td className="px-4 py-2.5 font-mono text-xs text-gray-500">
                          {s.median_car_pct === null ? (
                            <span className="text-gray-300">insufficient data</span>
                          ) : (
                            fmtPct(s.median_car_pct)
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <div>
            <div className="mb-0.5 text-[15px] font-extrabold">Matched announcements</div>
            <p className="max-w-[660px] text-[12.5px] leading-relaxed text-gray-400">
              Only releases mentioning both a commissioning/induction-type keyword and a watchlisted shipbuilder are
              kept &mdash; sorted newest first.
            </p>
          </div>

          {data.events.length === 0 ? (
            <div className="rounded-[14px] border border-gray-200 bg-white p-10 text-center text-[13px] text-gray-400">
              No matches yet. Click &ldquo;Check PIB now&rdquo; to scan the current feed.
            </div>
          ) : (
            <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[700px] border-collapse">
                  <thead>
                    <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                      <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Date
                      </th>
                      <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Symbols
                      </th>
                      <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Release
                      </th>
                      <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Source
                      </th>
                      <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Signal
                      </th>
                      <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">
                        Ceiling
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.events.map((row, i) => {
                      const signalDetail = row.SignalDetail ?? {
                        SignalLabel: 'N/A' as const,
                        SignalScore: null,
                        MoveSoFarPct: null,
                        MoveZScore: null,
                        PriorEventTypeCAR: null,
                        PriorSampleSize: 0,
                        SignalConfidence: 'Low' as const,
                      }
                      const durationDetail = row.DurationDetail ?? {
                        DaysHeld: null,
                        PeakReturnPct: null,
                        DaysToPeak: null,
                        CurrentReturnPct: null,
                        ReversionFromPeakPct: null,
                        PriorClose: null,
                        TargetCeiling: null,
                        TargetCeilingPct: null,
                      }
                      return (
                      <tr key={i} className="border-b border-gray-100 hover:bg-[#FAFAFB]">
                        <td className="px-4 py-2.5 font-mono text-[11.5px] text-gray-500">{formatDate(row.Date)}</td>
                        <td className="px-4 py-2.5">
                          <div className="flex flex-wrap gap-1">
                            {row.MatchedSymbols.split(',').map((s) => (
                              <span
                                key={s}
                                className="rounded-full bg-accent-soft px-1.5 py-0.5 font-mono text-[10.5px] font-bold text-accent"
                              >
                                {s}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-2.5 text-xs text-gray-700">
                          {row.Link ? (
                            <a
                              href={row.Link}
                              target="_blank"
                              rel="noreferrer"
                              className="text-accent hover:underline"
                            >
                              {row.Title}
                            </a>
                          ) : (
                            row.Title
                          )}
                        </td>
                        <td className="px-4 py-2.5">
                          <span
                            className={`rounded-full px-1.5 py-0.5 font-mono text-[10.5px] font-bold ${
                              row.Source === 'HISTORICAL'
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-gray-100 text-gray-500'
                            }`}
                          >
                            {row.Source}
                          </span>
                        </td>
                        <td className="px-4 py-2.5">
                          <span
                            className={`rounded-full px-1.5 py-0.5 font-mono text-[10.5px] font-bold ${
                              row.Signal === 'BUY'
                                ? 'bg-accent-soft text-accent'
                                : row.Signal === 'SELL'
                                  ? 'bg-red-100 text-red-700'
                                  : row.Signal === 'HOLD'
                                    ? 'bg-amber-100 text-amber-700'
                                    : 'bg-gray-100 text-gray-400'
                            }`}
                            title="Heuristic only, based on price move since the event date, sized against the stock's own ATR - not backtested."
                          >
                            {row.Signal}
                          </span>
                          <div className="mt-1 font-mono text-[10px] leading-tight text-gray-400">
                            {signalDetail.MoveZScore !== null
                              ? `${signalDetail.MoveZScore.toFixed(2)} ATR`
                              : signalDetail.MoveSoFarPct !== null
                                ? fmtPct(signalDetail.MoveSoFarPct)
                                : '—'}
                            {' · '}
                            {signalDetail.SignalConfidence.toLowerCase()} conf
                            {signalDetail.PriorEventTypeCAR !== null && (
                              <> (prior {fmtPct(signalDetail.PriorEventTypeCAR)})</>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-2.5">
                          <div className="font-mono text-[11.5px] text-gray-700">
                            {durationDetail.TargetCeiling === null
                              ? '—'
                              : `Rs.${durationDetail.TargetCeiling.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`}
                          </div>
                          <div className="mt-1 font-mono text-[10px] leading-tight text-gray-400">
                            {durationDetail.PriorClose !== null && (
                              <>vs Rs.{durationDetail.PriorClose.toLocaleString('en-IN', { maximumFractionDigits: 2 })} prior close</>
                            )}
                            {durationDetail.TargetCeilingPct !== null && (
                              <> ({fmtPct(durationDetail.TargetCeilingPct)})</>
                            )}
                          </div>
                        </td>
                      </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="mb-0.5 text-[15px] font-extrabold">Meesho investor/analyst meets</div>
              <p className="max-w-[660px] text-[12.5px] leading-relaxed text-gray-400">
                Scheduled and past investor/analyst meets from MEESHO&rsquo;s NSE corporate-announcement filings.
                Informational only &mdash; a 9-event backtest found no reliable directional edge, so there&rsquo;s no
                Signal/Ceiling attached here, unlike the PIB table above.
              </p>
            </div>
            <button
              onClick={onRefreshInvestorMeets}
              disabled={refreshingMeets}
              className="rounded-[8px] bg-accent px-3.5 py-2 text-xs font-semibold text-white hover:bg-accent-hover disabled:opacity-50"
            >
              {refreshingMeets ? 'Checking NSE...' : 'Check NSE now'}
            </button>
          </div>
          {meetsRefreshMessage && <p className="text-[12.5px] text-gray-500">{meetsRefreshMessage}</p>}
          {investorMeetsError ? (
            <p className="text-sm text-red-600">{investorMeetsError}</p>
          ) : !investorMeets ? (
            <p className="text-sm text-gray-500">Loading...</p>
          ) : investorMeets.meets.length === 0 ? (
            <div className="rounded-[14px] border border-gray-200 bg-white p-10 text-center text-[13px] text-gray-400">
              No investor meets found yet &mdash; click &ldquo;Check NSE now&rdquo;.
            </div>
          ) : (
            <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] border-collapse">
                  <thead>
                    <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                      {['Meeting date', 'Status', 'Filed on', 'Event'].map((h) => (
                        <th
                          key={h}
                          className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {investorMeets.meets.map((m, i) => (
                      <tr key={i} className="border-b border-gray-100 hover:bg-[#FAFAFB]">
                        <td className="px-4 py-2.5 font-mono text-[11.5px] text-gray-700">
                          {m.MeetingDate ?? '—'}
                        </td>
                        <td className="px-4 py-2.5">
                          <span
                            className={`rounded-full px-1.5 py-0.5 font-mono text-[10.5px] font-bold ${
                              m.Status === 'scheduled'
                                ? 'bg-accent-soft text-accent'
                                : m.Status === 'past'
                                  ? 'bg-gray-100 text-gray-500'
                                  : 'bg-amber-100 text-amber-700'
                            }`}
                          >
                            {m.Status.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 font-mono text-[11px] text-gray-500">{formatDate(m.FilingDate)}</td>
                        <td className="px-4 py-2.5 text-xs text-gray-700">
                          {m.PdfUrl ? (
                            <a href={m.PdfUrl} target="_blank" rel="noreferrer" className="text-accent hover:underline">
                              {m.EventName || 'Filing PDF'}
                            </a>
                          ) : (
                            m.EventName
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {scannedOpen && (
        <aside className="sticky top-10 flex w-[360px] flex-shrink-0 flex-col gap-2 rounded-[14px] border border-gray-200 bg-white p-4 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
          <div className="flex items-center justify-between">
            <div className="text-[15px] font-extrabold">All releases scanned</div>
            <button
              onClick={() => setScannedOpen(false)}
              className="text-xs font-semibold text-gray-400 hover:text-gray-700"
            >
              Close
            </button>
          </div>
          <p className="text-[12px] leading-relaxed text-gray-400">
            Every Ministry of Defence release the last refresh/historical fetch saw &mdash; matched (kept in the
            table) and unmatched (filtered out), so you can see what got discarded and why.
          </p>
          <div className="flex max-h-[70vh] flex-col gap-2 overflow-y-auto pt-1">
            {scanned === null ? (
              <p className="text-xs text-gray-400">Loading...</p>
            ) : scanned.length === 0 ? (
              <p className="text-xs text-gray-400">
                Nothing scanned yet &mdash; click &ldquo;Check PIB now&rdquo; or fetch a past date.
              </p>
            ) : (
              scanned.map((row, i) => (
                <div key={i} className="rounded-[10px] border border-gray-100 p-2.5">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="font-mono text-[10.5px] text-gray-400">{formatDate(row.Date)}</span>
                    <span
                      className={`rounded-full px-1.5 py-0.5 font-mono text-[10px] font-bold ${
                        row.Matched ? 'bg-accent-soft text-accent' : 'bg-gray-100 text-gray-400'
                      }`}
                    >
                      {row.Matched ? 'MATCHED' : 'FILTERED OUT'}
                    </span>
                  </div>
                  <div className="text-[12px] leading-snug text-gray-700">
                    {row.Link ? (
                      <a href={row.Link} target="_blank" rel="noreferrer" className="hover:underline">
                        {row.Title}
                      </a>
                    ) : (
                      row.Title
                    )}
                  </div>
                  {row.Matched && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {row.MatchedSymbols.split(',').map((s) => (
                        <span
                          key={s}
                          className="rounded-full bg-accent-soft px-1.5 py-0.5 font-mono text-[10px] font-bold text-accent"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </aside>
      )}
      </div>
      <KeywordDrawer open={keywordDrawerOpen} onClose={() => setKeywordDrawerOpen(false)} />
    </main>
  )
}
