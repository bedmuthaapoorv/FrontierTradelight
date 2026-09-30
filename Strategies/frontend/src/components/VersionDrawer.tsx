import { useEffect, useMemo, useState, type PointerEvent as ReactPointerEvent } from 'react'
import type { makeMarkdownFileApi } from '../api'

const DEFAULT_WIDTH = 340
const MIN_WIDTH = 260
const MAX_WIDTH = 800
const WIDTH_STORAGE_KEY = 'versionDrawerWidth'

interface VersionDrawerProps {
  api: ReturnType<typeof makeMarkdownFileApi>
  onRestored: (content: string) => void
  onMessage: (message: string) => void
  /** Controls the drawer's open/collapsed state from the parent, so a page
   * can offer its own trigger (e.g. "Browse strategy versions") in
   * addition to the rail itself. */
  open: boolean
  onOpenChange: (open: boolean) => void
  /** The backup group key (see backup_utils.group_backups) of the
   * strategy with the highest recorded Composite Score from the Stats
   * leaderboard - e.g. "trendline_bounce_confirmation_v4_rules". When a
   * group's key matches, it gets a "BEST PERFORMING" badge on its header.
   * Omit (or pass null) to show no such badge - only Rules.tsx supplies
   * this, since Composite Score is keyed by entry strategy name, not
   * exit strategy. */
  bestGroupKey?: string | null
  /** group_key -> the exact backup filename within that group whose
   * content produced its recorded Composite Score. That specific version
   * (not just the group as a whole) gets an inline "BEST SCORE" badge
   * next to its timestamp when the group is expanded - e.g. if
   * "Trendline Bounce Confirmation" was benchmarked three times across
   * three different saves, this marks which ONE of those three actually
   * earned the recorded score, since later edits under the same strategy
   * name don't necessarily perform the same. */
  bestScoringFileByGroup?: Record<string, string>
}

/** Parses the "_YYYYMMDD_HHMMSS" suffix backup_utils.backup_markdown always
 * appends before ".md", and formats it for display - a manually renamed
 * backup (see rename_backup) loses this suffix, so falls back to null and
 * the raw filename is shown instead. */
function parseBackupTimestamp(filename: string): Date | null {
  const match = filename.match(/_(\d{8})_(\d{6})\.md$/)
  if (!match) return null
  const [, ymd, hms] = match
  const year = Number(ymd.slice(0, 4))
  const month = Number(ymd.slice(4, 6)) - 1
  const day = Number(ymd.slice(6, 8))
  const hour = Number(hms.slice(0, 2))
  const minute = Number(hms.slice(2, 4))
  const second = Number(hms.slice(4, 6))
  return new Date(year, month, day, hour, minute, second)
}

function formatBackupTimestamp(date: Date): string {
  return date.toLocaleString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

/** Collapsible right-hand panel listing every backup, grouped by strategy,
 * with every version visible at once (no drill-down) - mirrors
 * ui_helpers.backup_restore_section + manage_backup_file, but laid out as
 * a persistent docked drawer instead of a modal dialog. */
export default function VersionDrawer({
  api,
  onRestored,
  onMessage,
  open,
  onOpenChange,
  bestGroupKey,
  bestScoringFileByGroup,
}: VersionDrawerProps) {
  const [groups, setGroups] = useState<Record<string, string[]>>({})
  const [search, setSearch] = useState('')
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [previewContent, setPreviewContent] = useState('')
  const [renameOpen, setRenameOpen] = useState(false)
  const [renameValue, setRenameValue] = useState('')
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [width, setWidth] = useState(() => {
    const saved = Number(localStorage.getItem(WIDTH_STORAGE_KEY))
    return saved >= MIN_WIDTH && saved <= MAX_WIDTH ? saved : DEFAULT_WIDTH
  })

  useEffect(() => {
    localStorage.setItem(WIDTH_STORAGE_KEY, String(width))
  }, [width])

  const loadGroups = () => {
    api
      .listBackups()
      .then((g) => {
        setGroups(g)
        setError(null)
      })
      .catch((err) => setError(err.message))
  }

  useEffect(() => {
    loadGroups()
  }, [])

  const filteredGroups = useMemo(() => {
    if (!search) return groups
    const lower = search.toLowerCase()
    const filtered: Record<string, string[]> = {}
    for (const [group, files] of Object.entries(groups)) {
      if (group.toLowerCase().includes(lower)) filtered[group] = files
    }
    return filtered
  }, [groups, search])

  useEffect(() => {
    if (!selectedKey) {
      setPreviewContent('')
      return
    }
    const filename = selectedKey.split('::')[1]
    api
      .getBackup(filename)
      .then((res) => setPreviewContent(res.content))
      .catch((err) => setError(err.message))
    setRenameValue(filename.replace(/\.md$/, ''))
    setRenameOpen(false)
    setDeleteConfirmOpen(false)
  }, [selectedKey])

  const selectVersion = (group: string, filename: string) => {
    const key = `${group}::${filename}`
    setSelectedKey((current) => (current === key ? null : key))
  }

  const handleRestore = (filename: string) => {
    api
      .restoreBackup(filename)
      .then((res) => {
        onRestored(res.content)
        onMessage(
          res.backed_up_as ? `Restored ${filename} (previous content backed up as ${res.backed_up_as})` : `Restored ${filename}`,
        )
      })
      .catch((err) => setError(err.message))
  }

  const handleRename = (filename: string) => {
    api
      .renameBackup(filename, renameValue)
      .then((res) => {
        onMessage(`Renamed to ${res.filename}`)
        setRenameOpen(false)
        setSelectedKey(null)
        loadGroups()
      })
      .catch((err) => setError(err.message))
  }

  const handleDelete = (filename: string) => {
    api
      .deleteBackup(filename)
      .then(() => {
        onMessage(`Deleted ${filename}`)
        setDeleteConfirmOpen(false)
        setSelectedKey(null)
        loadGroups()
      })
      .catch((err) => setError(err.message))
  }

  if (!open) {
    return (
      <button
        onClick={() => onOpenChange(true)}
        className="flex w-12 flex-shrink-0 flex-col items-center gap-3.5 border-l border-gray-200 bg-white pt-[18px] hover:bg-gray-50"
        title="Version history"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <polyline points="12 7 12 12 15 15" />
        </svg>
        <span className="font-mono text-[11px] font-semibold tracking-wide text-gray-500" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
          VERSION HISTORY
        </span>
      </button>
    )
  }

  const groupKeys = Object.keys(filteredGroups)

  const startResize = (e: ReactPointerEvent<HTMLDivElement>) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = width
    const maxWidth = Math.min(MAX_WIDTH, window.innerWidth - 320)
    const onMove = (ev: PointerEvent) => {
      // Drawer is docked on the right, so dragging left grows it.
      setWidth(Math.max(MIN_WIDTH, Math.min(maxWidth, startWidth + (startX - ev.clientX))))
    }
    const onUp = () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    }
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'col-resize'
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
  }

  return (
    <div
      className="relative flex flex-shrink-0 flex-col border-l border-gray-200 bg-white"
      style={{ width }}
    >
      <div
        onPointerDown={startResize}
        onDoubleClick={() => setWidth(DEFAULT_WIDTH)}
        title="Drag to resize (double-click to reset)"
        className="absolute -left-1 top-0 z-10 h-full w-2 cursor-col-resize hover:bg-accent/20 active:bg-accent/30"
      />
      <div className="flex flex-shrink-0 items-center justify-between border-b border-gray-100 px-4 py-3.5">
        <div className="text-[13.5px] font-bold">Version history</div>
        <button
          onClick={() => onOpenChange(false)}
          className="flex h-[26px] w-[26px] items-center justify-center rounded-[7px] hover:bg-gray-100"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>

      <div className="flex-shrink-0 px-3.5 pb-2 pt-3">
        <div className="relative">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#9AA0AC"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Filter strategies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-[8px] border border-gray-200 py-2 pl-[30px] pr-2.5 font-mono text-xs text-gray-900 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10"
          />
        </div>
      </div>

      {error && <p className="px-3.5 pb-2 text-xs text-red-600">{error}</p>}

      <div className="flex-1 overflow-y-auto px-2.5 pb-4">
        {groupKeys.length === 0 && <p className="px-2 py-2 text-xs text-gray-500">No backups yet.</p>}

        {groupKeys.map((group) => {
          const versions = filteredGroups[group]
          const isExpanded = expandedGroups[group] === true
          const isBestPerforming = bestGroupKey != null && group === bestGroupKey
          const bestScoringFile = bestScoringFileByGroup?.[group]
          return (
            <div key={group} className="mb-1">
              <button
                onClick={() => setExpandedGroups((prev) => ({ ...prev, [group]: !isExpanded }))}
                className="flex w-full items-center justify-between rounded-lg px-2 py-2 text-left hover:bg-gray-50"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <div className="truncate text-[12.5px] font-semibold text-gray-900">
                      {group.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                    </div>
                    {isBestPerforming && (
                      <span
                        title="Highest Composite Score recorded on the Stats leaderboard"
                        className="flex flex-shrink-0 items-center gap-1 rounded-full bg-amber-50 px-1.5 py-[1px] font-mono text-[9px] font-bold tracking-wide text-amber-700"
                      >
                        <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 2l2.9 6.26L21.5 9l-5 4.87L17.8 21 12 17.77 6.2 21l1.3-7.13-5-4.87 6.6-.74L12 2z" />
                        </svg>
                        BEST PERFORMING
                      </span>
                    )}
                  </div>
                  <div className="text-[10.5px] text-gray-400">{versions.length === 1 ? '1 version' : `${versions.length} versions`}</div>
                </div>
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#9AA0AC"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="flex-shrink-0 transition-transform"
                  style={{ transform: isExpanded ? 'rotate(0deg)' : 'rotate(-90deg)' }}
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>

              {isExpanded && (
                <div className="flex flex-col gap-px py-0.5 pl-2 pr-1">
                  {versions.map((filename, versionIndex) => {
                    const key = `${group}::${filename}`
                    const isSelected = key === selectedKey
                    const isLatest = versionIndex === 0
                    const isBestScore = filename === bestScoringFile
                    const timestamp = parseBackupTimestamp(filename)
                    return (
                      <div key={filename}>
                        <button
                          onClick={() => selectVersion(group, filename)}
                          title={filename}
                          className={`flex w-full items-center justify-between gap-2 rounded-md px-2 py-1.5 text-left hover:bg-gray-100 ${
                            isSelected ? 'bg-accent-soft' : ''
                          }`}
                        >
                          <div className="flex min-w-0 items-center gap-1.5">
                            {isLatest && (
                              <span className="flex-shrink-0 rounded-full bg-accent-soft px-1.5 py-[1px] font-mono text-[9px] font-bold tracking-wide text-accent">
                                LATEST
                              </span>
                            )}
                            {isBestScore && (
                              <span
                                title="This exact saved version produced the highest recorded Composite Score for this strategy"
                                className="flex flex-shrink-0 items-center gap-1 rounded-full bg-amber-50 px-1.5 py-[1px] font-mono text-[9px] font-bold tracking-wide text-amber-700"
                              >
                                <svg width="8" height="8" viewBox="0 0 24 24" fill="currentColor">
                                  <path d="M12 2l2.9 6.26L21.5 9l-5 4.87L17.8 21 12 17.77 6.2 21l1.3-7.13-5-4.87 6.6-.74L12 2z" />
                                </svg>
                                BEST SCORE
                              </span>
                            )}
                            <span className="truncate font-mono text-[11.5px] text-gray-600">
                              {timestamp ? formatBackupTimestamp(timestamp) : filename}
                            </span>
                          </div>
                          {isSelected && <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent" />}
                        </button>

                        {isSelected && (
                          <div className="my-1 flex flex-col gap-2 rounded-[9px] border border-gray-100 bg-[#FCFCFD] p-2.5">
                            <pre className="max-h-[90px] overflow-y-auto whitespace-pre-wrap font-mono text-[10.5px] leading-relaxed text-gray-500">
                              {previewContent}
                            </pre>

                            <div className="flex items-center gap-1.5">
                              <button
                                onClick={() => handleRestore(filename)}
                                className="flex-1 rounded-[7px] bg-accent px-2.5 py-1.5 text-[11.5px] font-semibold text-white hover:brightness-95"
                              >
                                Restore
                              </button>
                              <button
                                onClick={() => {
                                  setRenameOpen((v) => !v)
                                  setDeleteConfirmOpen(false)
                                }}
                                className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-[7px] border border-gray-200 hover:bg-gray-50"
                                title="Rename"
                              >
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4B5160" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                  <path d="M12 20h9" />
                                  <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => {
                                  setDeleteConfirmOpen((v) => !v)
                                  setRenameOpen(false)
                                }}
                                className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-[7px] border border-red-200 hover:bg-red-50"
                                title="Delete"
                              >
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#DC2626" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                  <polyline points="3 6 5 6 21 6" />
                                  <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                                  <path d="M10 11v6" />
                                  <path d="M14 11v6" />
                                </svg>
                              </button>
                            </div>

                            {renameOpen && (
                              <div className="flex flex-col gap-1.5 border-t border-gray-100 pt-2">
                                <input
                                  type="text"
                                  value={renameValue}
                                  onChange={(e) => setRenameValue(e.target.value)}
                                  className="rounded-[7px] border border-gray-200 px-2 py-1.5 font-mono text-[11.5px] text-gray-900 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/10"
                                />
                                <button
                                  onClick={() => handleRename(filename)}
                                  className="rounded-[7px] bg-accent px-2.5 py-1.5 text-[11.5px] font-semibold text-white hover:brightness-95"
                                >
                                  Confirm rename
                                </button>
                              </div>
                            )}

                            {deleteConfirmOpen && (
                              <div className="flex flex-col gap-1.5 border-t border-gray-100 pt-2">
                                <p className="text-[11px] leading-snug text-gray-600">
                                  Permanently delete <span className="font-bold">{filename}</span>? This cannot be undone.
                                </p>
                                <button
                                  onClick={() => handleDelete(filename)}
                                  className="rounded-[7px] border border-red-600 bg-red-600 px-2.5 py-1.5 text-[11.5px] font-semibold text-white hover:bg-red-700"
                                >
                                  Confirm delete
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
