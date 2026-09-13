import { useEffect, useState } from 'react'
import { makeMarkdownFileApi } from '../api'
import MarkdownEditor from '../components/MarkdownEditor'
import VersionDrawer from '../components/VersionDrawer'

const rulesApi = makeMarkdownFileApi('/rules')

function declaredStrategyName(content: string) {
  const match = content.match(/Strategy Name:\s*(.+)/)
  return match ? match[1].trim() : null
}

export default function Rules() {
  const [content, setContent] = useState('')
  const [savedContent, setSavedContent] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [saving, setSaving] = useState(false)
  const [justSaved, setJustSaved] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(true)

  useEffect(() => {
    rulesApi
      .get()
      .then((res) => {
        setContent(res.content)
        setSavedContent(res.content)
        setLoaded(true)
      })
      .catch((err) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!message) return
    const timeout = setTimeout(() => setMessage(null), 4000)
    return () => clearTimeout(timeout)
  }, [message])

  const dirty = content !== savedContent

  const handleSave = () => {
    setSaving(true)
    setError(null)
    rulesApi
      .save(content)
      .then((res) => {
        setSavedContent(content)
        setJustSaved(true)
        setTimeout(() => setJustSaved(false), 2200)
        setMessage(
          res.backed_up_as ? `Saved rules.md (previous version backed up as ${res.backed_up_as})` : 'Saved rules.md',
        )
      })
      .catch((err) => setError(err.message))
      .finally(() => setSaving(false))
  }

  const strategyName = declaredStrategyName(content)

  return (
    <div className="flex min-h-0 flex-1">
      <main className="flex-1 overflow-y-auto px-6 py-10">
        <div className="mx-auto flex max-w-[780px] flex-col gap-7">
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-[22px] font-extrabold tracking-tight">Rules</h1>
              {strategyName && (
                <span className="rounded-full border border-accent-softBorder bg-accent-soft px-2.5 py-[3px] font-mono text-[11.5px] font-semibold text-accent-hover">
                  {strategyName}
                </span>
              )}
            </div>
            <p className="max-w-[620px] text-[13.5px] leading-relaxed text-gray-500">
              Define stock-selection rules in plain English &mdash; mandatory filters, ranking formulas, indicator
              thresholds. This document compiles into the screening logic used by Run and Backtest.
            </p>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
          {message && <p className="text-sm text-green-700">{message}</p>}

          {!loaded ? (
            <p className="text-sm text-gray-500">Loading...</p>
          ) : (
            <MarkdownEditor
              value={content}
              onChange={setContent}
              toolbarExtra={
                <div className="flex items-center gap-3.5">
                  {dirty && !justSaved && (
                    <div className="flex items-center gap-1.5 text-xs text-gray-400">
                      <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                      Unsaved changes
                    </div>
                  )}
                  {justSaved && (
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-green-600">
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      Saved
                    </div>
                  )}
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-1.5 rounded-[9px] bg-accent px-4 py-2 text-[13px] font-semibold text-white hover:brightness-95 disabled:opacity-50"
                  >
                    {saving ? 'Saving...' : 'Save rules.md'}
                  </button>
                </div>
              }
              footer={
                <div className="flex items-center justify-between border-t border-gray-100 px-4 py-2.5">
                  <span className="text-[11.5px] text-gray-400">{content.split('\n').length} lines</span>
                  <span className="text-[11.5px] text-gray-400">rules.md</span>
                </div>
              }
            />
          )}

          <div className="flex items-start justify-between gap-5 border-t border-gray-200 pt-6">
            <div className="flex flex-col gap-1">
              <div className="text-sm font-bold">Version history</div>
              <p className="max-w-[480px] text-[12.5px] leading-relaxed text-gray-500">
                Every save keeps the previous version. Browse, restore, rename, or delete any past strategy from the
                panel on the right.
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
              Browse strategy versions
            </button>
          </div>
        </div>
      </main>

      <VersionDrawer
        api={rulesApi}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        onRestored={(restoredContent) => {
          setContent(restoredContent)
          setSavedContent(restoredContent)
        }}
        onMessage={setMessage}
      />
    </div>
  )
}
