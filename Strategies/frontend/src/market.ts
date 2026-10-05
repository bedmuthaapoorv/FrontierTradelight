/** Which market's backend the app is talking to. India (Strategies/Default,
 * port 8000) and US (Strategies/US, port 8001) are separate backend
 * processes with separate rules, caches, and holdings; the frontend is
 * shared and switches between them. Switching reloads the page, so every
 * module can read MARKET once at load instead of subscribing to changes. */

export type Market = 'IN' | 'US'

export interface MarketConfig {
  code: Market
  label: string
  apiBase: string
  currencyPrefix: string
  locale: string
  benchmarkLabel: string
  symbolLabel: string
  symbolPlaceholder: string
  dataSource: string
  hasEventWatcher: boolean
  /** Query param / response field the backend's /backtest/chart uses for
   * its benchmark series. The India backend is left as-is and still calls
   * it `nifty`; the US backend uses the market-neutral `benchmark`. */
  chartBenchmarkKey: 'nifty' | 'benchmark'
  /** The US backend serves /market (so the header can confirm it reached
   * the right process); the India backend only has /health. */
  identifiesMarket: boolean
}

export const MARKETS: Record<Market, MarketConfig> = {
  IN: {
    code: 'IN',
    label: 'India',
    apiBase: 'http://localhost:8000',
    currencyPrefix: 'Rs.',
    locale: 'en-IN',
    benchmarkLabel: 'Nifty 50',
    symbolLabel: 'NSE symbol',
    symbolPlaceholder: 'e.g. RELIANCE',
    dataSource: 'NSE',
    hasEventWatcher: true,
    chartBenchmarkKey: 'nifty',
    identifiesMarket: false,
  },
  US: {
    code: 'US',
    label: 'US',
    apiBase: 'http://localhost:8001',
    currencyPrefix: '$',
    locale: 'en-US',
    benchmarkLabel: 'S&P 500 (SPY)',
    symbolLabel: 'Ticker',
    symbolPlaceholder: 'e.g. AAPL',
    dataSource: 'Alpaca',
    hasEventWatcher: false,
    chartBenchmarkKey: 'benchmark',
    identifiesMarket: true,
  },
}

const STORAGE_KEY = 'ftl.market'

function readMarket(): Market {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'US' ? 'US' : 'IN'
  } catch {
    return 'IN'
  }
}

export const MARKET: MarketConfig = MARKETS[readMarket()]

// Drives the per-market background colours in index.css.
document.documentElement.dataset.market = MARKET.code

export function switchMarket(code: Market) {
  try {
    localStorage.setItem(STORAGE_KEY, code)
  } catch {
    // Storage unavailable - nothing to persist, stay on the current market.
    return
  }
  window.location.assign('/')
}

/** Money in the active market's currency and digit grouping. */
export function formatCurrency(n: number, maximumFractionDigits = 2) {
  return `${MARKET.currencyPrefix}${n.toLocaleString(MARKET.locale, { maximumFractionDigits })}`
}
