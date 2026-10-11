# Frontier TradeLight frontend

The React web app for Frontier TradeLight. A single build serves both
markets: it talks to the India backend (port 8000) or the US backend
(port 8001), depending on the **India / US** switch in the header.

For what each tab does from a user's point of view, see the
[project README](../../README.md#the-app). For the endpoints this app
calls, see the [API reference](../Default/api/README.md).

## Stack

React 18, TypeScript, Vite 5, React Router 6, Tailwind CSS 3 (with
`@tailwindcss/typography`), and `react-markdown` for spec previews.

## Running

The usual way to start the app is from `Strategies/` with `npm run dev`,
which also starts both backends. To run only the frontend:

```bash
cd Strategies/frontend
npm install
npm run dev        # http://localhost:5173 (Vite uses the next free port if 5173 is taken)
npm run build      # type-check, then build to dist/
npm run lint       # ESLint
npm run preview    # serve the production build
```

The backends allow CORS from any `http://localhost:<port>`, so a different
Vite port still works.

## Source layout

```
src/
  main.tsx          entry point
  App.tsx           header, India/US switch, backend health check, tab bar, routes
  market.ts         market configs (API base URL, currency, labels, feature flags)
  api.ts            typed API client: one helper or object per backend router
  index.css         Tailwind base, plus per-market colour variables
  pages/            one component per tab
  components/       shared UI pieces
```

### Market switching (`market.ts`)

`MARKETS` holds one config per market: `apiBase`, currency prefix, locale,
benchmark label, symbol placeholder, `hasEventWatcher`, and so on. The
chosen market is stored in `localStorage` (`ftl.market`) and read once at
load into `MARKET`. `switchMarket()` saves the new choice and reloads the
page, so modules can read `MARKET` directly without subscribing to changes.
`market.ts` also sets `<html data-market="...">`, which `index.css` uses to
tint the US app differently so the active market is obvious at a glance.

On startup `App.tsx` calls `/market` on the US backend (or `/health` on
India) and shows a warning if the backend isn't reachable or reports a
different market.

### API client (`api.ts`)

- `API_BASE_URL` comes from `MARKET.apiBase`.
- `makeMarkdownFileApi('/rules' | '/exit-rules')` covers spec editing and
  the backup/version endpoints.
- `streamJob(path, onLine)` POSTs to a `/jobs/*` endpoint and calls
  `onLine` for each streamed output line. It resolves to the script's exit
  code, read from the final `__EXIT_CODE__:<n>` line.
- `fetchReport(prefix)`, `holdingsApi`, `backtestApi`,
  `missedOpportunitiesApi`, `statsApi`, plus the Fund Manager, Event
  Watcher, and Multi-Strategy helpers, each come with TypeScript types for
  their responses.

### Pages

| File | Route | Notes |
| --- | --- | --- |
| `Rules.tsx` | `/rules` | Default route |
| `Run.tsx` | `/run` | |
| `Results.tsx` | `/results` | |
| `Sell.tsx` | `/sell` | |
| `Backtest.tsx` | `/backtest` | |
| `DeepDive.tsx` | `/deep-dive` | |
| `MissedOpportunities.tsx` | `/missed-opportunities` | |
| `Stats.tsx` | `/stats` | |
| `EventWatcher.tsx` | `/event-watcher` | India only (`MARKET.hasEventWatcher`) |
| `MultiStrategy.tsx` | `/multi-strategy` | |
| `FundManager.tsx` | `/fund-manager` | Standalone page outside the tab shell, linked from the header |
| `Placeholder.tsx` | | Leftover stub from the Streamlit migration. Imported in `App.tsx` but not used |

### Components

| File | Used for |
| --- | --- |
| `MarkdownEditor.tsx` | Edit/Preview toggle over a textarea, for `rules.md` and `exit_rules.md` |
| `VersionDrawer.tsx` | Resizable slide-over listing spec backups, with restore, rename, and delete |
| `PipelineStep.tsx` | Numbered step card with idle, running, success, and error states (Run tab) |
| `KeywordDrawer.tsx` | Event Watcher keyword, watchlist, and vessel-alias editor |

## Adding a tab

1. Create `src/pages/YourTab.tsx`.
2. In `App.tsx`, add `{ path: '/your-tab', label: 'Your Tab' }` to `TABS`
   and a matching `<Route>`. For an India-only tab, add `indiaOnly: true`
   and guard the route the same way Event Watcher's is.
3. Add any endpoint helpers and types to `api.ts`, and the backend router
   to both `Strategies/Default/api/` and `Strategies/US/api/` (see the
   [API reference](../Default/api/README.md)).
