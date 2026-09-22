import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fundManagerApi, type FundDocumentRow, type FundHoldingRow, type FundOverview } from '../api'

function formatMoney(n: number) {
  return `Rs.${n.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
}

function formatPct(n: number | null) {
  if (n === null) return 'N/A'
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const CATEGORY_COLORS: Record<string, { bg: string; text: string }> = {
  Agreement: { bg: '#EAF0EB', text: '#3D5944' },
  Statement: { bg: '#DBEAFE', text: '#1D4ED8' },
  Compliance: { bg: '#FEF3C7', text: '#92400E' },
  Tax: { bg: '#F3E8FF', text: '#7E22CE' },
  Other: { bg: '#F3F4F6', text: '#6B7280' },
}

const EXT_BADGE: Record<string, { bg: string; text: string; label: string }> = {
  pdf: { bg: '#FEE2E2', text: '#B91C1C', label: 'PDF' },
  doc: { bg: '#DBEAFE', text: '#1D4ED8', label: 'DOC' },
  docx: { bg: '#DBEAFE', text: '#1D4ED8', label: 'DOC' },
  xls: { bg: '#DCFCE7', text: '#15803D', label: 'XLS' },
  xlsx: { bg: '#DCFCE7', text: '#15803D', label: 'XLS' },
  csv: { bg: '#DCFCE7', text: '#15803D', label: 'CSV' },
  png: { bg: '#F3E8FF', text: '#7E22CE', label: 'IMG' },
  jpg: { bg: '#F3E8FF', text: '#7E22CE', label: 'IMG' },
  jpeg: { bg: '#F3E8FF', text: '#7E22CE', label: 'IMG' },
}

function extBadge(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  return EXT_BADGE[ext] ?? { bg: '#F3F4F6', text: '#6B7280', label: ext.slice(0, 3).toUpperCase() || 'FILE' }
}

/** Composes a Gmail compose-in-browser URL with a portfolio update for one
 * investor, mirroring the structure of the original portfolio-update email
 * template (update-for/date greeting, holdings summary, recent activity,
 * investor-since line) - adapted to units/NAV since the fund is now
 * unitized rather than each investor owning specific instruments directly.
 * Opens gmail.com instead of a mailto: link so it doesn't hand off to
 * whatever desktop client (e.g. Outlook) owns the mailto: protocol. */
function buildUpdateGmailUrl(inv: FundOverview['investors'][number], data: FundOverview, notes: string) {
  const today = new Date()
  const joinDate = new Date(inv.join_date)
  const days = Math.max(0, Math.round((today.getTime() - joinDate.getTime()) / 86400000))
  const joinDateStr = joinDate.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

  const firstName = inv.name.split(' ')[0]
  const events = data.recent_capital_events.filter((ev) => ev.investor_id === inv.investor_id)

  const divider = '─'.repeat(40)
  const row = (label: string, value: string) => `${label.padEnd(16)}${value}`

  const lines = [
    `Hi ${firstName},`,
    '',
    "Here's your portfolio update. Please review the details below.",
    '',
    divider,
    'YOUR STAKE',
    divider,
    row('Units held', inv.units_held.toFixed(2)),
    row('Current NAV', data.nav.toFixed(4)),
    row('Current value', formatMoney(inv.current_value)),
    row('Return', formatPct(inv.return_pct)),
    '',
    divider,
    'RECENT TRANSACTIONS',
    divider,
    ...(events.length === 0
      ? ['No deposits or withdrawals recorded yet.']
      : events.map((ev) => row(ev.date, `${ev.type}  ${formatMoney(ev.amount)}`))),
    '',
    `Investor since ${joinDateStr} (${days} days)`,
    '',
    ...(notes.trim()
      ? [
          divider,
          'NOTES & DEVELOPMENTS',
          divider,
          ...notes
            .split('\n')
            .map((line) => line.trim())
            .filter(Boolean)
            .map((line) => `• ${line}`),
          '',
        ]
      : []),
    'Thanks for the trust and THE MONEY!',
    '',
    "Please let me know if you have any questions or if you'd like to discuss any of these positions.",
    '',
    'Best regards,',
    '',
    'Apoorv Bedmutha, FTL',
    'bedmuthaapoorv@gmail.com',
    '+91 95612 95237',
  ]

  const subject = 'Frontier TradeLight: Portfolio Update'
  const body = lines.join('\n')
  const params = new URLSearchParams({ view: 'cm', fs: '1', to: inv.email, su: subject, body })
  return `https://mail.google.com/mail/?${params.toString()}`
}

/** Normalizes a NAV series into an SVG polyline inside a 0..480 x 10..130
 * viewBox - same technique as Backtest.tsx's toPolyline, just local since
 * this view is intentionally standalone from the tabbed app's pages. */
function toPolyline(values: number[], min: number, max: number): string {
  const w = 430
  const x0 = 30
  const y0 = 10
  const y1 = 130
  const range = max - min || 1
  return values
    .map((v, i) => {
      const x = x0 + (i / Math.max(1, values.length - 1)) * w
      const y = y1 - ((v - min) / range) * (y1 - y0)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

function AddCapitalEventForm({ investors, onAdded, onCancel }: { investors: FundOverview['investors']; onAdded: () => void; onCancel: () => void }) {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [investorId, setInvestorId] = useState(investors[0]?.investor_id ?? '')
  const [type, setType] = useState<'DEPOSIT' | 'WITHDRAWAL'>('DEPOSIT')
  const [amount, setAmount] = useState('')
  const [backdating, setBackdating] = useState(false)
  const [navOverride, setNavOverride] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = () => {
    if (!investorId || !amount || Number(amount) <= 0) {
      setError('Pick an investor and enter an amount.')
      return
    }
    if (backdating && (!navOverride || Number(navOverride) <= 0)) {
      setError('Enter the NAV this event actually transacted at.')
      return
    }
    setSaving(true)
    setError(null)
    fundManagerApi
      .addCapitalEvent(date, investorId, type, Number(amount), backdating ? Number(navOverride) : undefined)
      .then((res) => {
        if (res.status === 'ok') {
          onAdded()
        } else {
          setError(res.message ?? 'Failed to add capital event.')
        }
      })
      .finally(() => setSaving(false))
  }

  return (
    <div className="flex flex-col gap-2.5 border-t border-gray-100 bg-[#FAFAFB] px-5 py-3.5">
      <div className="grid grid-cols-2 gap-2">
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-lg border border-gray-200 px-2.5 py-1.5 font-mono text-xs"
        />
        <select
          value={type}
          onChange={(e) => setType(e.target.value as 'DEPOSIT' | 'WITHDRAWAL')}
          className="rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs font-medium"
        >
          <option value="DEPOSIT">Deposit</option>
          <option value="WITHDRAWAL">Withdrawal</option>
        </select>
        <select
          value={investorId}
          onChange={(e) => setInvestorId(e.target.value)}
          className="rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs font-medium"
        >
          {investors.length === 0 && <option value="">No investors yet</option>}
          {investors.map((inv) => (
            <option key={inv.investor_id} value={inv.investor_id}>
              {inv.name}
            </option>
          ))}
        </select>
        <input
          type="number"
          placeholder="Amount (Rs.)"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="rounded-lg border border-gray-200 px-2.5 py-1.5 font-mono text-xs"
        />
      </div>
      <label className="flex cursor-pointer items-center gap-1.5 text-[11.5px] font-medium text-gray-600">
        <input type="checkbox" checked={backdating} onChange={(e) => setBackdating(e.target.checked)} />
        Backfilling history &mdash; this event transacted at a specific past NAV, not today's live NAV
      </label>
      {backdating && (
        <input
          type="number"
          step="0.0001"
          placeholder="NAV at the time (e.g. 102.0982)"
          value={navOverride}
          onChange={(e) => setNavOverride(e.target.value)}
          className="w-full rounded-lg border border-gray-200 px-2.5 py-1.5 font-mono text-xs"
        />
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex items-center gap-2">
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="rounded-lg bg-accent px-3 py-1.5 text-xs font-semibold text-white hover:brightness-95 disabled:bg-gray-300"
        >
          {saving ? 'Saving...' : 'Add event'}
        </button>
        <button onClick={onCancel} className="rounded-lg px-3 py-1.5 text-xs font-semibold text-gray-500 hover:text-gray-700">
          Cancel
        </button>
      </div>
    </div>
  )
}

function AddInvestorForm({ onAdded, onCancel }: { onAdded: () => void; onCancel: () => void }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [joinDate, setJoinDate] = useState(new Date().toISOString().slice(0, 10))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = () => {
    if (!name.trim()) {
      setError('Enter a name.')
      return
    }
    const investorId = name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
    setSaving(true)
    setError(null)
    fundManagerApi
      .addInvestor(investorId, name.trim(), email.trim(), joinDate)
      .then(() => onAdded())
      .finally(() => setSaving(false))
  }

  return (
    <div className="flex flex-col gap-2.5 border-t border-gray-100 bg-[#FAFAFB] px-5 py-3.5">
      <div className="grid grid-cols-3 gap-2">
        <input
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs font-medium"
        />
        <input
          placeholder="Email (optional)"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs font-medium"
        />
        <input
          type="date"
          value={joinDate}
          onChange={(e) => setJoinDate(e.target.value)}
          className="rounded-lg border border-gray-200 px-2.5 py-1.5 font-mono text-xs"
        />
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex items-center gap-2">
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="rounded-lg bg-accent px-3 py-1.5 text-xs font-semibold text-white hover:brightness-95 disabled:bg-gray-300"
        >
          {saving ? 'Saving...' : 'Add investor'}
        </button>
        <button onClick={onCancel} className="rounded-lg px-3 py-1.5 text-xs font-semibold text-gray-500 hover:text-gray-700">
          Cancel
        </button>
      </div>
    </div>
  )
}

function OverviewTab({ data, onNavCalculated }: { data: FundOverview; onNavCalculated: () => void }) {
  const [calculating, setCalculating] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [addingEvent, setAddingEvent] = useState(false)
  const [addingInvestor, setAddingInvestor] = useState(false)
  const [removeError, setRemoveError] = useState<string | null>(null)
  const [notes, setNotes] = useState('')

  const onRemoveInvestor = (investorId: string) => {
    setRemoveError(null)
    fundManagerApi.removeInvestor(investorId).then((res) => {
      if (res.status === 'ok') {
        onNavCalculated()
      } else {
        setRemoveError(res.message ?? 'Failed to remove investor.')
      }
    })
  }

  const onRemoveCapitalEvent = (rowIndex: number) => {
    setRemoveError(null)
    fundManagerApi.removeCapitalEvent(rowIndex).then((res) => {
      if (res.status === 'ok') {
        onNavCalculated()
      } else {
        setRemoveError(res.message ?? 'Failed to remove capital event.')
      }
    })
  }

  const handleCalculate = () => {
    setCalculating(true)
    setError(null)
    setMessage(null)
    fundManagerApi
      .calculateNav()
      .then((res) => {
        if (res.status === 'ok') {
          setMessage(`Recorded NAV ${res.nav?.toFixed(4)} for ${res.date}.`)
          onNavCalculated()
        } else {
          setError(res.message ?? 'Failed to calculate NAV.')
        }
      })
      .finally(() => setCalculating(false))
  }

  const navValues = data.nav_history.map((p) => p.nav)
  const navMin = navValues.length ? Math.min(...navValues) : 99
  const navMax = navValues.length ? Math.max(...navValues) : 101

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
      {/* Fund overview */}
      <div className="grid grid-cols-4 gap-3">
        <div className="rounded-[14px] border border-gray-200 bg-white p-4">
          <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Fund AUM</div>
          <div className="font-mono text-[19px] font-extrabold">{formatMoney(data.aum)}</div>
        </div>
        <div className="rounded-[14px] border border-gray-200 bg-white p-4">
          <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Current NAV</div>
          <div className="font-mono text-[19px] font-extrabold text-accent">{data.nav.toFixed(4)}</div>
          <div className="mt-0.5 text-[11px] text-gray-400">per unit, base 100.00</div>
        </div>
        <div className="rounded-[14px] border border-gray-200 bg-white p-4">
          <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Total Units</div>
          <div className="font-mono text-[19px] font-extrabold">{data.total_units.toFixed(2)}</div>
          <div className="mt-0.5 text-[11px] text-gray-400">outstanding</div>
        </div>
        <div className="rounded-[14px] border border-gray-200 bg-white p-4">
          <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Investors</div>
          <div className="font-mono text-[19px] font-extrabold">{data.investor_count}</div>
          <div className="mt-0.5 text-[11px] text-gray-400">active</div>
        </div>
      </div>

      {/* NAV calculator */}
      <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
        <div className="border-b border-gray-100 px-5 py-[14px]">
          <div className="text-[15px] font-extrabold">NAV calculator</div>
          <p className="mt-1 max-w-[620px] text-[12.5px] leading-relaxed text-gray-500">
            Computes today's NAV from the fund's live portfolio value (Holdings tab) and total units outstanding,
            then records it to nav_history.csv. Any deposits or withdrawals dated today are applied AFTER this NAV
            is struck &mdash; new money never inflates the NAV it buys into.
          </p>
        </div>
        <div className="grid grid-cols-3">
          <div className="border-r border-gray-100 px-5 py-[18px]">
            <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Fund AUM (now)</div>
            <div className="font-mono text-base font-bold">{formatMoney(data.aum)}</div>
            <div className="mt-0.5 text-[10.5px] text-gray-400">from Holdings tab</div>
          </div>
          <div className="border-r border-gray-100 px-5 py-[18px]">
            <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Total units (now)</div>
            <div className="font-mono text-base font-bold">{data.total_units.toFixed(2)}</div>
            <div className="mt-0.5 text-[10.5px] text-gray-400">before today's capital events</div>
          </div>
          <div className="bg-accent-soft px-5 py-[18px]">
            <div className="mb-1.5 text-[10.5px] font-bold uppercase tracking-wide text-accent">Current NAV</div>
            <div className="font-mono text-base font-extrabold text-accent">{data.nav.toFixed(4)}</div>
            <div className="mt-0.5 text-[10.5px] text-accent-hover">value &divide; units</div>
          </div>
        </div>
        <div className="flex items-center gap-2.5 border-t border-gray-100 px-5 py-4">
          <button
            onClick={handleCalculate}
            disabled={calculating}
            className="rounded-[9px] bg-accent px-[18px] py-2.5 text-[13px] font-semibold text-white hover:brightness-95 disabled:cursor-default disabled:bg-gray-300"
          >
            {calculating ? 'Calculating...' : "Record today's NAV"}
          </button>
          {message && <span className="text-xs text-green-700">{message}</span>}
          {error && <span className="text-xs text-red-600">{error}</span>}
        </div>
      </div>

      {/* NAV history + capital events */}
      <div className="grid grid-cols-[1.3fr_1fr] items-start gap-4">
        <div className="rounded-[14px] border border-gray-200 bg-white p-5 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
          <div className="mb-3 text-[15px] font-extrabold">NAV history</div>
          {navValues.length > 1 ? (
            <>
              <svg viewBox="0 0 480 140" width="100%" height="140" style={{ display: 'block' }}>
                <line x1="30" y1="10" x2="30" y2="130" stroke="#EEEEF0" strokeWidth="1" />
                <line x1="30" y1="130" x2="460" y2="130" stroke="#EEEEF0" strokeWidth="1" />
                <polyline points={toPolyline(navValues, navMin, navMax)} fill="none" stroke="#3D5944" strokeWidth="2.25" />
              </svg>
              <div className="mt-1.5 flex justify-between px-0.5">
                <span className="text-[11px] text-gray-400">{data.nav_history[0]?.date}</span>
                <span className="font-mono text-[11px] font-bold text-accent">
                  {data.nav_history[data.nav_history.length - 1]?.nav.toFixed(4)} today
                </span>
              </div>
            </>
          ) : (
            <p className="py-8 text-center text-sm text-gray-400">No NAV recorded yet.</p>
          )}
        </div>

        <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
          <div className="flex items-center justify-between px-5 py-4 pb-3">
            <span className="text-[15px] font-extrabold">Recent capital events</span>
            <button
              onClick={() => setAddingEvent((v) => !v)}
              className="rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-[11.5px] font-semibold text-gray-700 hover:bg-gray-50"
            >
              + Add
            </button>
          </div>
          {removeError && <p className="px-5 pb-2 text-xs text-red-600">{removeError}</p>}
          {addingEvent && (
            <AddCapitalEventForm
              investors={data.investors}
              onCancel={() => setAddingEvent(false)}
              onAdded={() => {
                setAddingEvent(false)
                onNavCalculated()
              }}
            />
          )}
          {data.recent_capital_events.length === 0 ? (
            <p className="px-5 pb-4 text-sm text-gray-400">No capital events yet.</p>
          ) : (
            <div className="flex flex-col">
              {data.recent_capital_events.map((ev) => (
                <div key={ev.index} className="flex items-center justify-between border-t border-gray-100 px-5 py-2.5">
                  <div>
                    <div className="text-[12.5px] font-bold">{ev.investor_id}</div>
                    <div className="font-mono text-[10.5px] text-gray-400">
                      {ev.date} &middot; {ev.type}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className={`font-mono text-[12.5px] font-bold ${ev.type === 'DEPOSIT' ? 'text-green-700' : 'text-red-700'}`}>
                        {ev.type === 'DEPOSIT' ? '+' : '-'}
                        {formatMoney(ev.amount)}
                      </div>
                      <div className="font-mono text-[10.5px] text-gray-400">{Math.abs(ev.units).toFixed(2)} units</div>
                    </div>
                    <button
                      onClick={() => onRemoveCapitalEvent(ev.index)}
                      className="text-[11.5px] font-semibold text-gray-400 hover:text-red-600"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Notes for the next email */}
      <div className="flex flex-col gap-2">
        <div>
          <div className="text-[15px] font-extrabold">Notes &amp; developments</div>
          <p className="mt-[3px] max-w-[620px] text-[12.5px] leading-relaxed text-gray-500">
            Optional - one point per line, included as bullets in every "Send update" email below.
          </p>
        </div>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={'e.g.\nAdded a benchmark dashboard comparing strategy performance over 2021-2026\nTrendline liquidity filter now adapts dynamically to market conditions'}
          rows={4}
          className="w-full resize-y rounded-[14px] border border-gray-200 bg-white p-3.5 text-[12.5px] leading-relaxed text-gray-700 shadow-[0_1px_2px_rgba(16,24,40,0.03)] focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10"
        />
      </div>

      {/* Investors */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <span className="text-[15px] font-extrabold">Investors</span>
          <button
            onClick={() => setAddingInvestor((v) => !v)}
            className="rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-[11.5px] font-semibold text-gray-700 hover:bg-gray-50"
          >
            + Add investor
          </button>
        </div>
        {removeError && <p className="text-xs text-red-600">{removeError}</p>}
        {addingInvestor && (
          <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
            <AddInvestorForm
              onCancel={() => setAddingInvestor(false)}
              onAdded={() => {
                setAddingInvestor(false)
                onNavCalculated()
              }}
            />
          </div>
        )}
        {data.investors.length === 0 ? (
          <div className="rounded-[14px] border border-gray-200 bg-white p-10 text-center text-[13px] text-gray-400">
            No investors yet.
          </div>
        ) : (
          <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                  <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Investor</th>
                  <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Investor since</th>
                  <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Units held</th>
                  <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Current value</th>
                  <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Return</th>
                  <th className="px-4 py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                {data.investors.map((inv) => (
                  <tr key={inv.investor_id} className="border-b border-gray-100 last:border-b-0">
                    <td className="px-4 py-2.5 text-[12.5px] font-bold text-gray-900">{inv.name}</td>
                    <td className="px-4 py-2.5 font-mono text-[11.5px] text-gray-500">{inv.join_date}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-xs text-gray-700">{inv.units_held.toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-xs font-bold text-gray-900">{formatMoney(inv.current_value)}</td>
                    <td
                      className={`px-4 py-2.5 text-right font-mono text-xs font-bold ${
                        (inv.return_pct ?? 0) >= 0 ? 'text-green-700' : 'text-red-700'
                      }`}
                    >
                      {formatPct(inv.return_pct)}
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <div className="flex items-center justify-end gap-3">
                        {inv.email && (
                          <a
                            href={buildUpdateGmailUrl(inv, data, notes)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[11.5px] font-semibold text-accent no-underline hover:text-accent-hover"
                          >
                            Send update &rarr;
                          </a>
                        )}
                        <button
                          onClick={() => onRemoveInvestor(inv.investor_id)}
                          className="text-[11.5px] font-semibold text-gray-400 hover:text-red-600"
                        >
                          Remove
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function HoldingsTab({ onSaved }: { onSaved: () => void }) {
  const [holdings, setHoldings] = useState<FundHoldingRow[]>([])
  const [cash, setCash] = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  const load = () => {
    fundManagerApi.holdings().then((res) => {
      setHoldings(res.holdings)
      setCash(res.cash)
      setLoading(false)
    })
  }

  useEffect(() => {
    load()
  }, [])

  const totalAum = holdings.reduce((sum, h) => sum + h.Qty * h.CurrentPrice, 0) + cash

  const updateRow = (i: number, field: keyof FundHoldingRow, value: string) => {
    setHoldings((rows) => rows.map((r, idx) => (idx === i ? { ...r, [field]: field === 'Symbol' ? value : Number(value) } : r)))
  }

  const addRow = () => setHoldings((rows) => [...rows, { Symbol: '', Qty: 0, AvgCost: 0, CurrentPrice: 0 }])
  const removeRow = (i: number) => setHoldings((rows) => rows.filter((_, idx) => idx !== i))

  const handleSave = () => {
    setSaving(true)
    setMessage(null)
    fundManagerApi
      .saveHoldings(
        holdings.filter((h) => h.Symbol.trim() !== ''),
        cash,
      )
      .then(() => {
        setMessage('Saved.')
        onSaved()
      })
      .finally(() => setSaving(false))
  }

  if (loading) return <p className="text-sm text-gray-500">Loading...</p>

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[15px] font-extrabold">Fund holdings</div>
          <p className="mt-[3px] max-w-[620px] text-[12.5px] leading-relaxed text-gray-500">
            The fund's actual positions and cash &mdash; kept separately from your personal Holdings tab. This is a
            record only: no sell/hold signals are shown here, it exists purely to compute the fund's AUM.
          </p>
        </div>
        <div className="flex flex-shrink-0 items-center gap-2.5">
          {message && <span className="text-xs text-green-700">{message}</span>}
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-[9px] bg-accent px-4 py-2.5 text-[12.5px] font-semibold text-white hover:brightness-95 disabled:bg-gray-300"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-gray-100 bg-[#FAFAFB]">
              <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Instrument</th>
              <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Qty</th>
              <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Avg Cost</th>
              <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Current Price</th>
              <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Current Value</th>
              <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Unrealised P&amp;L</th>
              <th className="px-4 py-2.5"></th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((h, i) => {
              const value = h.Qty * h.CurrentPrice
              const pl = (h.CurrentPrice - h.AvgCost) * h.Qty
              return (
                <tr key={i} className="border-b border-gray-100">
                  <td className="px-4 py-1.5">
                    <input
                      value={h.Symbol}
                      onChange={(e) => updateRow(i, 'Symbol', e.target.value)}
                      className="w-24 rounded border border-gray-200 px-2 py-1 font-mono text-xs font-bold uppercase"
                    />
                  </td>
                  <td className="px-4 py-1.5 text-right">
                    <input
                      type="number"
                      value={h.Qty}
                      onChange={(e) => updateRow(i, 'Qty', e.target.value)}
                      className="w-20 rounded border border-gray-200 px-2 py-1 text-right font-mono text-xs"
                    />
                  </td>
                  <td className="px-4 py-1.5 text-right">
                    <input
                      type="number"
                      value={h.AvgCost}
                      onChange={(e) => updateRow(i, 'AvgCost', e.target.value)}
                      className="w-24 rounded border border-gray-200 px-2 py-1 text-right font-mono text-xs"
                    />
                  </td>
                  <td className="px-4 py-1.5 text-right">
                    <input
                      type="number"
                      value={h.CurrentPrice}
                      onChange={(e) => updateRow(i, 'CurrentPrice', e.target.value)}
                      className="w-24 rounded border border-gray-200 px-2 py-1 text-right font-mono text-xs"
                    />
                  </td>
                  <td className="px-4 py-1.5 text-right font-mono text-xs font-bold text-gray-900">{formatMoney(value)}</td>
                  <td className={`px-4 py-1.5 text-right font-mono text-xs font-bold ${pl >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    {pl >= 0 ? '+' : ''}
                    {formatMoney(pl)}
                  </td>
                  <td className="px-4 py-1.5 text-right">
                    <button onClick={() => removeRow(i)} className="text-xs font-semibold text-red-600 hover:text-red-700">
                      Remove
                    </button>
                  </td>
                </tr>
              )
            })}
            <tr className="border-b border-gray-100">
              <td className="px-4 py-1.5 font-mono text-xs font-bold text-gray-900">CASH</td>
              <td className="px-4 py-1.5 text-right text-gray-300">&mdash;</td>
              <td className="px-4 py-1.5 text-right text-gray-300">&mdash;</td>
              <td className="px-4 py-1.5 text-right text-gray-300">&mdash;</td>
              <td className="px-4 py-1.5 text-right">
                <input
                  type="number"
                  value={cash}
                  onChange={(e) => setCash(Number(e.target.value))}
                  className="w-24 rounded border border-gray-200 px-2 py-1 text-right font-mono text-xs font-bold"
                />
              </td>
              <td className="px-4 py-1.5 text-right text-gray-300">&mdash;</td>
              <td></td>
            </tr>
          </tbody>
          <tfoot>
            <tr className="border-t border-gray-200 bg-accent-soft">
              <td colSpan={4} className="px-4 py-2.5 text-xs font-bold text-accent-hover">
                Total fund AUM
              </td>
              <td className="px-4 py-2.5 text-right font-mono text-[13px] font-extrabold text-accent-hover">{formatMoney(totalAum)}</td>
              <td colSpan={2}></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <button
        onClick={addRow}
        className="self-start rounded-[9px] border border-gray-200 bg-white px-4 py-2 text-[12.5px] font-semibold text-gray-700 hover:bg-gray-50"
      >
        + Add holding
      </button>
    </div>
  )
}

function AddDocumentForm({ categories, onAdded, onCancel }: { categories: string[]; onAdded: () => void; onCancel: () => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [category, setCategory] = useState(categories[0] ?? 'Other')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = () => {
    if (!file) {
      setError('Choose a file to upload.')
      return
    }
    setSaving(true)
    setError(null)
    fundManagerApi
      .uploadDocument(file, category, date, notes)
      .then((res) => {
        if (res.status === 'ok') {
          onAdded()
        } else {
          setError(res.message ?? 'Failed to upload document.')
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setSaving(false))
  }

  return (
    <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
      <div className="border-b border-gray-100 px-5 py-3.5 text-[13.5px] font-bold">New document</div>
      <div className="flex flex-col gap-3 bg-[#FAFAFB] px-5 py-4">
        <label className="flex flex-col items-center justify-center gap-2 rounded-xl border-[1.5px] border-dashed border-gray-300 bg-white px-6 py-6 text-center cursor-pointer hover:border-accent">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <span className="text-[12.5px] font-semibold text-gray-700">
            {file ? file.name : 'Drop a file here, or click to browse'}
          </span>
          <span className="text-[11px] text-gray-400">PDF, DOCX, XLSX, image or CSV up to 25 MB</span>
          <input
            type="file"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg"
          />
        </label>

        <div className="grid grid-cols-2 gap-2.5">
          <div className="flex flex-col gap-1">
            <label className="text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-medium"
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 font-mono text-xs"
            />
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Notes (optional)</label>
          <input
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Shared with investors on the September update email"
            className="rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs"
          />
        </div>

        {error && <p className="text-xs text-red-600">{error}</p>}

        <div className="flex items-center gap-2 pt-1">
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="rounded-[9px] bg-accent px-4 py-2 text-xs font-semibold text-white hover:brightness-95 disabled:bg-gray-300"
          >
            {saving ? 'Uploading...' : 'Save document'}
          </button>
          <button onClick={onCancel} className="rounded-lg px-3 py-2 text-xs font-semibold text-gray-500 hover:text-gray-700">
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

function DocumentsTab() {
  const [documents, setDocuments] = useState<FundDocumentRow[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [activeCategory, setActiveCategory] = useState<string>('All')
  const [search, setSearch] = useState('')
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    fundManagerApi
      .listDocuments()
      .then((res) => {
        setDocuments(res.documents)
        setCategories(res.categories)
        setLoading(false)
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
  }

  useEffect(load, [])

  const onRemove = (docId: string) => {
    fundManagerApi.removeDocument(docId).then((res) => {
      if (res.status === 'ok') {
        load()
      } else {
        setError(res.message ?? 'Failed to remove document.')
      }
    })
  }

  const filtered = useMemo(() => {
    return documents.filter((d) => {
      if (activeCategory !== 'All' && d.category !== activeCategory) return false
      if (search.trim() && !d.name.toLowerCase().includes(search.trim().toLowerCase())) return false
      return true
    })
  }, [documents, activeCategory, search])

  if (loading) return <p className="text-sm text-gray-500">Loading...</p>

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-[15px] font-extrabold">Fund documents</div>
          <p className="mt-[3px] max-w-[620px] text-[12.5px] leading-relaxed text-gray-500">
            Every fund-related paper you create &mdash; agreements, statements, compliance filings, tax records
            &mdash; kept in one place, separate from the personal Holdings tab. Files live here, not in strategy
            backups.
          </p>
        </div>
        {!adding && (
          <button
            onClick={() => setAdding(true)}
            className="flex-shrink-0 rounded-[9px] bg-accent px-4 py-2.5 text-[12.5px] font-semibold text-white hover:brightness-95"
          >
            + New document
          </button>
        )}
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}

      {adding && (
        <AddDocumentForm
          categories={categories}
          onCancel={() => setAdding(false)}
          onAdded={() => {
            setAdding(false)
            load()
          }}
        />
      )}

      <div className="flex items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setActiveCategory('All')}
            className={`rounded-full px-3 py-1.5 text-[11.5px] font-bold ${
              activeCategory === 'All' ? 'bg-accent-soft text-accent' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            }`}
          >
            All ({documents.length})
          </button>
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setActiveCategory(c)}
              className={`rounded-full px-3 py-1.5 text-[11.5px] font-semibold ${
                activeCategory === c ? 'bg-accent-soft text-accent' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search documents..."
          className="w-56 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-[11.5px] text-gray-700"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-[14px] border border-gray-200 bg-white p-10 text-center text-[13px] text-gray-400">
          {documents.length === 0 ? 'No documents yet. Click "+ New document" to upload one.' : 'No documents match this filter.'}
        </div>
      ) : (
        <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Document</th>
                <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Category</th>
                <th className="px-4 py-2.5 text-left text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Date</th>
                <th className="px-4 py-2.5 text-right text-[10.5px] font-bold uppercase tracking-wide text-gray-400">Size</th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((doc) => {
                const badge = extBadge(doc.name)
                const cat = CATEGORY_COLORS[doc.category] ?? CATEGORY_COLORS.Other
                return (
                  <tr key={doc.id} className="border-b border-gray-100 last:border-b-0">
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <span
                          className="flex h-[26px] w-[26px] flex-shrink-0 items-center justify-center rounded-[7px] font-mono text-[9px] font-extrabold"
                          style={{ background: badge.bg, color: badge.text }}
                        >
                          {badge.label}
                        </span>
                        <span className="truncate text-[12.5px] font-semibold text-gray-900" title={doc.name}>
                          {doc.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className="rounded-full px-2 py-0.5 text-[10.5px] font-bold"
                        style={{ background: cat.bg, color: cat.text }}
                      >
                        {doc.category}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-[11px] text-gray-500">{doc.date}</td>
                    <td className="px-4 py-2.5 text-right font-mono text-[11px] text-gray-500">{formatSize(doc.size_bytes)}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center justify-end gap-3.5">
                        <a
                          href={fundManagerApi.downloadDocumentUrl(doc.id)}
                          className="text-[11.5px] font-semibold text-accent no-underline hover:text-accent-hover"
                        >
                          Download
                        </a>
                        <button
                          onClick={() => onRemove(doc.id)}
                          className="text-[11.5px] font-semibold text-gray-400 hover:text-red-600"
                        >
                          Remove
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function FundManager() {
  const [tab, setTab] = useState<'overview' | 'holdings' | 'documents'>('overview')
  const [data, setData] = useState<FundOverview | null>(null)

  const loadOverview = () => fundManagerApi.overview().then(setData)

  useEffect(() => {
    loadOverview()
  }, [])

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#F7F7F8] text-gray-900">
      <header className="flex flex-shrink-0 items-center justify-between border-b border-[#24352A] bg-[#1E2E23] px-7 py-[13px]">
        <div className="flex items-center gap-2.5">
          <Link to="/rules" className="flex items-center gap-1.5 text-xs font-semibold text-[#AEC2B3] no-underline hover:text-white">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#AEC2B3" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
            Back to app
          </Link>
          <span className="h-4 w-px bg-[#33473A]" />
          <div className="flex items-center gap-2">
            <div className="flex h-[22px] w-[22px] flex-shrink-0 items-center justify-center rounded-md bg-accent">
              <svg width="14" height="14" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path
                  transform="translate(1.7,3.2) scale(0.0595) translate(-65,-33)"
                  d="M229.592 92.2116C232.959 93.5674 232.925 98.3461 229.538 99.6536L99.6326 149.815C95.9576 151.234 92.6606 147.046 94.903 143.807L110.942 120.639C112.374 118.57 111.564 115.709 109.26 114.699L74.1763 99.3083C71.0127 97.9205 70.9777 93.4449 74.1193 92.0078L109.156 75.9805C111.392 74.9577 112.185 72.1788 110.825 70.1305L94.6287 45.7365C92.4555 42.4633 95.8105 38.346 99.4551 39.8135L229.592 92.2116Z"
                  fill="#FFFFFF"
                />
              </svg>
            </div>
            <span className="text-[14.5px] font-extrabold tracking-tight text-white">Fund Manager</span>
          </div>
        </div>
        {data && (
          <div className="flex items-center gap-1.5 text-[11px] text-[#8FA396]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#6FA57C]" />
            NAV {data.nav.toFixed(4)}
          </div>
        )}
      </header>

      <div className="flex flex-shrink-0 items-center gap-0.5 border-b border-gray-200 bg-white px-7">
        <button
          onClick={() => setTab('overview')}
          className={`relative px-3.5 py-[11px] text-[13px] font-semibold ${tab === 'overview' ? 'text-gray-900' : 'text-gray-400 hover:text-gray-700'}`}
        >
          Overview
          {tab === 'overview' && <span className="absolute inset-x-3.5 -bottom-px h-0.5 rounded-t bg-accent" />}
        </button>
        <button
          onClick={() => setTab('holdings')}
          className={`relative px-3.5 py-[11px] text-[13px] font-semibold ${tab === 'holdings' ? 'text-gray-900' : 'text-gray-400 hover:text-gray-700'}`}
        >
          Holdings
          {tab === 'holdings' && <span className="absolute inset-x-3.5 -bottom-px h-0.5 rounded-t bg-accent" />}
        </button>
        <button
          onClick={() => setTab('documents')}
          className={`relative px-3.5 py-[11px] text-[13px] font-semibold ${tab === 'documents' ? 'text-gray-900' : 'text-gray-400 hover:text-gray-700'}`}
        >
          Documents
          {tab === 'documents' && <span className="absolute inset-x-3.5 -bottom-px h-0.5 rounded-t bg-accent" />}
        </button>
      </div>

      <main className="flex-1 overflow-y-auto px-7 py-8">
        <div className="mx-auto max-w-[1080px]">
          {tab === 'overview' &&
            (data ? <OverviewTab data={data} onNavCalculated={loadOverview} /> : <p className="text-sm text-gray-500">Loading...</p>)}
          {tab === 'holdings' && <HoldingsTab onSaved={loadOverview} />}
          {tab === 'documents' && <DocumentsTab />}
        </div>
      </main>
    </div>
  )
}
