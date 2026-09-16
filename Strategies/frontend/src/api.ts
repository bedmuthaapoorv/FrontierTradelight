export const API_BASE_URL = 'http://localhost:8000'

export interface FileContent {
  content: string
}

export interface BackupGroups {
  [group: string]: string[]
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => null)
    throw new Error(detail?.detail ?? `Request to ${path} failed with ${res.status}`)
  }
  return res.json() as Promise<T>
}

/** CRUD + backup/restore client for a markdown strategy file, mirroring
 * api/routers/markdown_files.py's make_markdown_router. Both /rules and
 * (later) /exit-rules use the same shape, so one client factory covers
 * both instead of duplicating fetch calls per tab. */
export function makeMarkdownFileApi(prefix: '/rules' | '/exit-rules') {
  return {
    get: () => request<FileContent>(prefix),
    save: (content: string) =>
      request<FileContent & { backed_up_as: string | null }>(prefix, {
        method: 'PUT',
        body: JSON.stringify({ content }),
      }),
    listBackups: () => request<BackupGroups>(`${prefix}/backups`),
    getBackup: (filename: string) =>
      request<FileContent>(`${prefix}/backups/${encodeURIComponent(filename)}`),
    restoreBackup: (filename: string) =>
      request<FileContent & { backed_up_as: string | null }>(
        `${prefix}/backups/${encodeURIComponent(filename)}/restore`,
        { method: 'POST' },
      ),
    renameBackup: (filename: string, newName: string) =>
      request<{ filename: string }>(`${prefix}/backups/${encodeURIComponent(filename)}/rename`, {
        method: 'POST',
        body: JSON.stringify({ new_name: newName }),
      }),
    deleteBackup: (filename: string) =>
      request<{ status: string }>(`${prefix}/backups/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      }),
  }
}

/** Runs a long-lived script job (api/routers/jobs.py) and calls onLine for
 * every stdout line as it streams in, in order - mirrors
 * ui_helpers.run_script's line-at-a-time output, just over HTTP instead of
 * st.empty(). Resolves with the process's exit code once the stream ends. */
export type JobPath =
  | '/jobs/generate-screener'
  | '/jobs/run-screener'
  | '/jobs/generate-exit-strategy'
  | '/jobs/check-exit-signals'

export async function streamJob(path: JobPath, onLine: (line: string) => void): Promise<number> {
  const res = await fetch(`${API_BASE_URL}${path}`, { method: 'POST' })
  if (!res.ok || !res.body) {
    throw new Error(`Request to ${path} failed with ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let exitCode = 0

  const handleLine = (line: string) => {
    const match = line.match(/^__EXIT_CODE__:(-?\d+)$/)
    if (match) {
      exitCode = Number(match[1])
    } else if (line) {
      onLine(line)
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) handleLine(line)
  }
  if (buffer) handleLine(buffer)

  return exitCode
}

export type CellValue = string | number | boolean | null

export interface ReportResponse {
  columns: string[]
  rows: Record<string, CellValue>[]
}

/** Fetches a screener/sell-screener report CSV as JSON, mirroring
 * api/routers/results.py's make_report_router. Shared by /results and
 * /sell-report - same response shape, no per-report logic. */
export const fetchReport = (prefix: '/results' | '/sell-report' | '/backtest-trades' | '/backtest-summary') =>
  request<ReportResponse>(prefix)

export interface Holding {
  Symbol: string
  EntryPrice: number | ''
  EntryDate: string
  CurrentPrice: number | '' | null
}

export const holdingsApi = {
  get: () => request<{ holdings: Holding[] }>('/holdings'),
  save: (holdings: Holding[]) =>
    request<{ status: string; count: number }>('/holdings', {
      method: 'PUT',
      body: JSON.stringify({ holdings }),
    }),
}

export interface BacktestStatus {
  running: boolean
  day?: number | null
  total_days?: number | null
  eta_seconds?: number | null
  log_tail?: string
  exit_code?: number
  stats_recorded?: boolean
  stats_reason?: string
}

export interface BacktestMeta {
  strategy_name: string | null
  exit_strategy_name: string | null
  start_date: string | null
  end_date: string | null
}

export interface BacktestResult {
  available: boolean
  initial_capital?: number
  final_equity?: number
  total_return_pct?: number
  cagr_pct?: number | null
  max_dd_pct?: number
  composite_score?: number | null
  funded_count?: number
  skipped_count?: number
  meta?: BacktestMeta
}

export interface BacktestChart {
  dates: string[]
  nominal: number[]
  inflation_adjusted: number[] | null
  nifty: number[] | null
}

export interface YearlyRow {
  year: number
  start_equity: number
  end_equity: number
  return_pct: number
}

export interface PortfolioYear {
  year: number
  dates: string[]
  equity: number[]
  return_pct: number
}

export interface PortfolioByYear {
  years: PortfolioYear[]
  overall_min: string | null
  overall_max: string | null
}

/** Client for api/routers/backtest.py - launch/poll/stop backtest.py and
 * read its results, mirroring backtest_runner.py's launch/poll/record
 * cycle from the Streamlit app. */
export const backtestApi = {
  run: (params: { start: string; end: string; initial_capital: number; max_positions: number }) =>
    request<{ status: string } | { detail: string }>('/backtest/run', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  stop: () => request<{ status: string }>('/backtest/stop', { method: 'POST' }),
  status: () => request<BacktestStatus>('/backtest/status'),
  result: () => request<BacktestResult>('/backtest/result'),
  chart: (inflation: boolean, nifty: boolean) =>
    request<BacktestChart>(`/backtest/chart?inflation=${inflation}&nifty=${nifty}`),
  yearly: () => request<{ rows: YearlyRow[] }>('/backtest/yearly'),
  portfolioByYear: () => request<PortfolioByYear>('/backtest/portfolio-by-year'),
}

export interface MissedOpportunitiesRuleRow {
  rule: string
  count: number
  avg_forward_return_pct: number
  win_rate_pct: number
}

export interface MissedOpportunitiesTopRow {
  date: string
  symbol: string
  reason: string
  closeness_score: number
  forward_return_pct: number
}

export interface MissedOpportunities {
  available: boolean
  strategy_name?: string | null
  exit_strategy_name?: string | null
  realized_avg_profit?: number | null
  realized_win_rate?: number | null
  rule_rows?: MissedOpportunitiesRuleRow[]
  top_rows?: MissedOpportunitiesTopRow[]
}

/** Client for api/routers/missed_opportunities.py - near-misses grouped by
 * blocking rule plus the realized-trade benchmark, mirroring
 * tabs/missed_opportunities.py's aggregation exactly. */
export const missedOpportunitiesApi = {
  get: () => request<MissedOpportunities>('/missed-opportunities'),
}

export interface StatsRow {
  strategy_name: string
  exit_strategy_name: string | null
  cagr_pct: number | null
  max_dd_pct: number | null
  num_trades: number | null
  composite_score: number | null
  last_updated: string
}

export interface Stats {
  benchmark_start: string
  benchmark_end: string
  rows: StatsRow[]
}

export interface StrategyOption {
  key: string
  label: string
}

/** Client for api/routers/stats.py - the strategy leaderboard and the
 * strategy-switch flow used before a benchmark backtest, mirroring
 * tabs/stats.py exactly. Actually running the benchmark reuses
 * backtestApi.run/status with the fixed benchmark date range. */
export const statsApi = {
  get: () => request<Stats>('/stats'),
  strategyOptions: () => request<{ options: StrategyOption[] }>('/stats/strategy-options'),
  loadStrategy: (groupKey: string) =>
    request<{ status: string; message?: string }>('/stats/load-strategy', {
      method: 'POST',
      body: JSON.stringify({ group_key: groupKey }),
    }),
}

export interface FundNavPoint {
  date: string
  nav: number
}

export interface FundCapitalEvent {
  index: number
  date: string
  investor_id: string
  type: 'DEPOSIT' | 'WITHDRAWAL'
  amount: number
  units: number
}

export interface FundInvestorRow {
  investor_id: string
  name: string
  email: string
  join_date: string
  units_held: number
  current_value: number
  return_pct: number | null
}

export interface FundOverview {
  aum: number
  nav: number
  total_units: number
  investor_count: number
  nav_history: FundNavPoint[]
  recent_capital_events: FundCapitalEvent[]
  investors: FundInvestorRow[]
}

export interface FundHoldingRow {
  Symbol: string
  Qty: number
  AvgCost: number
  CurrentPrice: number
}

/** Client for api/routers/fund_manager.py - the real-money fund's NAV/units
 * dashboard, entirely separate from the backtest engine. Fund holdings here
 * are a distinct record from the personal Holdings/Sell tab's holdingsApi. */
export const fundManagerApi = {
  overview: () => request<FundOverview>('/fund-manager/overview'),
  calculateNav: () =>
    request<{ status: string; message?: string; date?: string; aum?: number; total_units?: number; nav?: number }>(
      '/fund-manager/nav/calculate',
      { method: 'POST' },
    ),
  holdings: () => request<{ holdings: FundHoldingRow[]; cash: number }>('/fund-manager/holdings'),
  saveHoldings: (holdings: FundHoldingRow[], cash: number) =>
    request<{ status: string; count: number }>('/fund-manager/holdings', {
      method: 'PUT',
      body: JSON.stringify({ holdings, cash }),
    }),
  addInvestor: (investorId: string, name: string, email: string, joinDate: string) =>
    request<{ status: string }>('/fund-manager/investors', {
      method: 'POST',
      body: JSON.stringify({ investor_id: investorId, name, email, join_date: joinDate }),
    }),
  removeInvestor: (investorId: string) =>
    request<{ status: string; message?: string }>(`/fund-manager/investors/${encodeURIComponent(investorId)}`, {
      method: 'DELETE',
    }),
  addCapitalEvent: (
    date: string,
    investorId: string,
    type: 'DEPOSIT' | 'WITHDRAWAL',
    amount: number,
    navOverride?: number,
  ) =>
    request<{ status: string; message?: string; nav?: number; units?: number }>('/fund-manager/capital-events', {
      method: 'POST',
      body: JSON.stringify({ date, investor_id: investorId, type, amount, nav_override: navOverride ?? null }),
    }),
  removeCapitalEvent: (rowIndex: number) =>
    request<{ status: string; message?: string }>(`/fund-manager/capital-events/${rowIndex}`, {
      method: 'DELETE',
    }),
}
