import { useEffect, useState } from 'react'
import { eventWatcherKeywordsApi, type KeywordConfig } from '../api'

// Fallback used only until the real watchlist loads from the backend (see
// symbolOptions below) - keeps newAliasSymbol's initial useState call valid
// without needing config to exist yet.
const FALLBACK_SYMBOL_OPTIONS = ['COCHINSHIP', 'MAZDOCK', 'GRSE']

interface KeywordDrawerProps {
  open: boolean
  onClose: () => void
}

/** Slide-over editor for the Event Watcher's matching config (event
 * keywords, shipbuilder watchlist, vessel-class aliases) - backed by
 * api/routers/event_watcher.py's get_keywords/put_keywords, which read and
 * write event_watcher_utils.py's live EVENT_KEYWORDS/WATCHLIST/
 * VESSEL_CLASS_TO_SYMBOL (persisted to data/event_watcher/keywords.json).
 * Always mounted so it can animate in/out via translate-x rather than
 * mount/unmount. */
export default function KeywordDrawer({ open, onClose }: KeywordDrawerProps) {
  // The full keyword config as last loaded/edited. null until the GET
  // request finishes, which is also how the UI knows whether to show the
  // "Loading..." message or the actual form.
  const [config, setConfig] = useState<KeywordConfig | null>(null)
  // Set if the initial GET request fails, so we can show the user why
  // nothing loaded instead of leaving them staring at a blank drawer.
  const [error, setError] = useState<string | null>(null)
  // True while a save is in flight - disables the Save button and swaps
  // its label to "Saving..." so the user can't double-submit.
  const [saving, setSaving] = useState(false)
  // Short status text shown next to the Save button (e.g. "Saved." or an
  // error) - cleared on the next edit so it doesn't linger and mislead.
  const [message, setMessage] = useState<string | null>(null)

  // What the user is currently typing into the "Add a keyword" box, before
  // they hit Add/Enter - kept separate from `config` since it's not a
  // saved keyword yet, just a draft.
  const [newKeyword, setNewKeyword] = useState('')
  // Same idea as newKeyword, but one per shipbuilder group (keyed by
  // symbol) since each watchlist card has its own "add a name fragment"
  // input running at the same time.
  const [nameDrafts, setNameDrafts] = useState<Record<string, string>>({})
  // Draft text for the vessel-class alias phrase being added.
  const [newAliasPhrase, setNewAliasPhrase] = useState('')
  // Which symbol the new alias should map to - defaults to the fallback's
  // first entry so the dropdown always has a valid value before config
  // loads; reset to the real watchlist's first symbol once it does (see
  // the load effect below), so this never points at a symbol that isn't
  // actually on the watchlist.
  const [newAliasSymbol, setNewAliasSymbol] = useState(FALLBACK_SYMBOL_OPTIONS[0])

  // The symbols the alias dropdown should actually offer - derived from
  // the loaded watchlist (so adding/removing a watchlist group updates
  // this automatically) rather than a hardcoded list that would silently
  // go stale, as the old SYMBOL_OPTIONS constant did when BDL was added.
  const symbolOptions = config ? config.watchlist.map((g) => g.symbol) : FALLBACK_SYMBOL_OPTIONS

  // Loads the current keyword config from the backend whenever the drawer
  // opens, and points the alias-symbol dropdown at that config's first
  // real watchlist symbol.
  useEffect(() => {
    if (!open) return
    setError(null)
    setMessage(null)
    eventWatcherKeywordsApi
      .get()
      .then((c) => {
        setConfig(c)
        if (c.watchlist.length > 0) setNewAliasSymbol(c.watchlist[0].symbol)
      })
      .catch((err) => setError(err.message))
  }, [open])

  // Removes one event keyword by its index in the list.
  const removeKeyword = (i: number) => {
    setConfig((c) => c && { ...c, event_keywords: c.event_keywords.filter((_, idx) => idx !== i) })
    setMessage(null)
  }

  // Called when the user clicks "Add" (or presses Enter) next to the
  // keyword input. Takes whatever they typed, and if it's not blank and
  // not already in the list, adds it as a new keyword. Then clears the
  // input box so they can type the next one.
  const addKeyword = () => {
    const v = newKeyword.trim().toLowerCase()
    if (!v) return
    setConfig(
        (c) => c && (c.event_keywords.includes(v) ? c : { ...c, event_keywords: [...c.event_keywords, v] }))
    setNewKeyword('')
    setMessage(null)
  }

  // Removes one name fragment from a shipbuilder's watchlist group.
  const removeWatchlistName = (symbol: string, name: string) => {
    setConfig(
      (c) =>
        c && {
          ...c,
          watchlist: c.watchlist.map((g) => (g.symbol === symbol ? { ...g, names: g.names.filter((n) => n !== name) } : g)),
        },
    )
    setMessage(null)
  }

  // Adds the pending name-fragment draft to a shipbuilder's watchlist group, skipping duplicates.
  const addWatchlistName = (symbol: string) => {
    const v = (nameDrafts[symbol] || '').trim().toLowerCase()
    if (!v) return
    setConfig(
      (c) =>
        c && {
          ...c,
          watchlist: c.watchlist.map((g) =>
            g.symbol === symbol && !g.names.includes(v) ? { ...g, names: [...g.names, v] } : g,
          ),
        },
    )
    setNameDrafts((d) => ({ ...d, [symbol]: '' }))
    setMessage(null)
  }

  // Removes one vessel-class alias by its index in the list.
  const removeAlias = (i: number) => {
    setConfig((c) => c && { ...c, vessel_class_aliases: c.vessel_class_aliases.filter((_, idx) => idx !== i) })
    setMessage(null)
  }

  // Adds the pending phrase/symbol draft as a new vessel-class alias.
  const addAlias = () => {
    const phrase = newAliasPhrase.trim().toLowerCase()
    if (!phrase) return
    setConfig(
      (c) => c && { ...c, vessel_class_aliases: [...c.vessel_class_aliases, { phrase, symbol: newAliasSymbol }] },
    )
    setNewAliasPhrase('')
    setMessage(null)
  }

  // Saves the current (locally edited) config to the backend.
  const onSave = async () => {
    if (!config) return
    setSaving(true)
    setMessage(null)
    try {
      const result = await eventWatcherKeywordsApi.save(config)
      if (result.status === 'ok') {
        setMessage('Saved.')
      } else {
        setMessage(`Save failed: ${result.message}`)
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <div
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-black/30 transition-opacity duration-300 ${
          open ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
      />
      <div
        className={`fixed right-0 top-0 z-50 flex h-full w-[440px] flex-col border-l border-gray-200 bg-white shadow-xl transition-transform duration-300 ease-in-out ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex flex-shrink-0 items-center justify-between border-b border-gray-100 px-5 py-4">
          <div className="text-[14.5px] font-bold">Edit keywords</div>
          <button onClick={onClose} className="flex h-[26px] w-[26px] items-center justify-center rounded-[7px] hover:bg-gray-100">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {error && <p className="text-xs text-red-600">{error}</p>}
          {!error && !config && <p className="text-xs text-gray-500">Loading...</p>}

          {config && (
            <div className="flex flex-col gap-6">
              <p className="text-[12px] leading-relaxed text-gray-500">
                A release only becomes a match when its title contains at least one Event keyword AND either a
                Shipbuilder name or a Vessel-class alias.
              </p>

              <div className="flex flex-col gap-2.5">
                <div className="text-[12.5px] font-bold text-gray-900">Event keywords</div>
                <div className="flex flex-wrap gap-1.5">
                  {config.event_keywords.map((kw, i) => (
                    <span
                      key={kw}
                      className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 py-[5px] pl-3 pr-1.5 text-[11.5px] text-gray-600"
                    >
                      {kw}
                      <button
                        onClick={() => removeKeyword(i)}
                        aria-label="Remove keyword"
                        className="flex h-[17px] w-[17px] items-center justify-center rounded-full text-gray-400 hover:bg-gray-200 hover:text-red-600"
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    placeholder="Add a keyword"
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
                    className="flex-1 rounded-[7px] border border-gray-300 px-2.5 py-1.5 text-xs text-gray-700"
                  />
                  <button
                    onClick={addKeyword}
                    className="rounded-[7px] border border-gray-300 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                  >
                    Add
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-2.5">
                <div className="text-[12.5px] font-bold text-gray-900">Shipbuilder watchlist</div>
                {config.watchlist.map((group) => (
                  <div key={group.symbol} className="flex flex-col gap-2 rounded-[10px] border border-gray-100 bg-[#FAFAFB] p-3">
                    <span className="w-fit rounded-full border border-accent-softBorder bg-accent-soft px-2.5 py-[3px] font-mono text-[11px] font-bold text-accent">
                      {group.symbol}
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {group.names.map((name) => (
                        <span
                          key={name}
                          className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-white py-[5px] pl-3 pr-1.5 text-[11.5px] text-gray-600"
                        >
                          {name}
                          <button
                            onClick={() => removeWatchlistName(group.symbol, name)}
                            aria-label="Remove name fragment"
                            className="flex h-[17px] w-[17px] items-center justify-center rounded-full text-gray-400 hover:bg-gray-200 hover:text-red-600"
                          >
                            &times;
                          </button>
                        </span>
                      ))}
                    </div>
                    <div className="flex gap-1.5">
                      <input
                        type="text"
                        placeholder="Add a name fragment"
                        value={nameDrafts[group.symbol] || ''}
                        onChange={(e) => setNameDrafts((d) => ({ ...d, [group.symbol]: e.target.value }))}
                        onKeyDown={(e) => e.key === 'Enter' && addWatchlistName(group.symbol)}
                        className="flex-1 rounded-[7px] border border-gray-300 px-2.5 py-1.5 text-xs text-gray-700"
                      />
                      <button
                        onClick={() => addWatchlistName(group.symbol)}
                        className="rounded-[7px] border border-gray-300 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                      >
                        Add
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex flex-col gap-2.5">
                <div className="text-[12.5px] font-bold text-gray-900">Vessel-class aliases</div>
                <p className="text-[11px] leading-relaxed text-gray-400">
                  PIB commissioning headlines often name the vessel/class, not the shipbuilder (e.g. "Mahe-class" never
                  says "Cochin Shipyard") &mdash; map those phrases to the symbol they should still tag.
                </p>
                <div className="flex flex-col gap-1">
                  {config.vessel_class_aliases.map((a, i) => (
                    <div key={`${a.phrase}-${i}`} className="flex items-center gap-2 border-b border-gray-100 py-1.5">
                      <span className="flex-1 text-[12px] text-gray-700">{a.phrase}</span>
                      <span className="text-[10px] text-gray-400">&rarr;</span>
                      <span className="rounded-full bg-accent-soft px-2 py-[2px] font-mono text-[10px] font-bold text-accent">
                        {a.symbol}
                      </span>
                      <button
                        onClick={() => removeAlias(i)}
                        aria-label="Remove alias"
                        className="flex h-[17px] w-[17px] items-center justify-center rounded-full text-gray-400 hover:bg-gray-100 hover:text-red-600"
                      >
                        &times;
                      </button>
                    </div>
                  ))}
                </div>
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    placeholder="Vessel or class phrase"
                    value={newAliasPhrase}
                    onChange={(e) => setNewAliasPhrase(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && addAlias()}
                    className="flex-1 rounded-[7px] border border-gray-300 px-2.5 py-1.5 text-xs text-gray-700"
                  />
                  <select
                    value={newAliasSymbol}
                    onChange={(e) => setNewAliasSymbol(e.target.value)}
                    className="rounded-[7px] border border-gray-300 px-2 py-1.5 text-xs text-gray-700"
                  >
                    {symbolOptions.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={addAlias}
                    className="rounded-[7px] border border-gray-300 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-shrink-0 items-center gap-3 border-t border-gray-100 px-5 py-3.5">
          <button
            onClick={onSave}
            disabled={!config || saving}
            className="rounded-[8px] bg-accent px-4 py-2 text-xs font-semibold text-white hover:bg-accent-hover disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save changes'}
          </button>
          {message && <span className="text-xs text-gray-500">{message}</span>}
        </div>
      </div>
    </>
  )
}
