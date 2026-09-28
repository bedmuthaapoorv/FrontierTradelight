import { useEffect, useRef, useState } from 'react'
import { API_BASE_URL } from '../api'

type CellValue = string | number | boolean | null

interface ResultsResponse {
  columns: string[]
  rows: Record<string, CellValue>[]
}

function formatCell(value: CellValue): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(2)
  return String(value)
}

// Fallback used only until the real viewport measurement below runs once.
const DEFAULT_PAGE_SIZE = 20
const ROW_HEIGHT_PX = 37 // matches the rendered <tr>'s py-2.5 + text-xs + border
const HEADER_HEIGHT_PX = 37
const PAGINATION_BAR_HEIGHT_PX = 44
const BOTTOM_MARGIN_PX = 24 // breathing room so the table doesn't touch the page edge

type SortDirection = 'asc' | 'desc'

export default function Results() {
  const [data, setData] = useState<ResultsResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [passedOnly, setPassedOnly] = useState(false)
  const [isScrollable, setIsScrollable] = useState(false)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const scrollRef = useRef<HTMLDivElement>(null)
  const tableWrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch(`${API_BASE_URL}/results`)
      .then((res) => {
        if (!res.ok) throw new Error(`Request to /results failed with ${res.status}`)
        return res.json() as Promise<ResultsResponse>
      })
      .then(setData)
      .catch((err) => setError(err.message))
  }, [])

  // The table can be wider than the viewport (16 columns), and important
  // fields like Ideal Entry Price sit in the middle of that width with no
  // visual cue that there's more to scroll to - so track scroll position and
  // show arrow buttons on both edges whenever the table overflows at all,
  // disabling whichever side there's nothing left to scroll toward (rather
  // than hiding it, which made the layout jump and hid the affordance
  // entirely once you'd scrolled all the way to one end).
  useEffect(() => {
    const el = scrollRef.current
    if (!el) return

    const updateScrollState = () => {
      setIsScrollable(el.scrollWidth - el.clientWidth > 1)
      setCanScrollLeft(el.scrollLeft > 4)
      setCanScrollRight(el.scrollWidth - el.clientWidth - el.scrollLeft > 4)
    }

    updateScrollState()
    el.addEventListener('scroll', updateScrollState)
    const resizeObserver = new ResizeObserver(updateScrollState)
    resizeObserver.observe(el)

    return () => {
      el.removeEventListener('scroll', updateScrollState)
      resizeObserver.disconnect()
    }
  }, [data])

  // Size the page to however many rows actually fit below the table's own
  // position on screen, so a tall monitor shows more rows and a short one
  // (or a browser window resize) shows fewer - instead of a fixed count
  // that's either wastefully short or forces page-level vertical scroll,
  // which is what was hiding the horizontal-scroll arrow hint in the first
  // place.
  useEffect(() => {
    const computePageSize = () => {
      const wrapper = tableWrapperRef.current
      const top = wrapper ? wrapper.getBoundingClientRect().top : 0
      const available = window.innerHeight - top - HEADER_HEIGHT_PX - PAGINATION_BAR_HEIGHT_PX - BOTTOM_MARGIN_PX
      const rowsThatFit = Math.floor(available / ROW_HEIGHT_PX)
      setPageSize(Math.max(5, rowsThatFit))
    }

    computePageSize()
    window.addEventListener('resize', computePageSize)
    return () => window.removeEventListener('resize', computePageSize)
  }, [data])

  useEffect(() => {
    setPage(1)
  }, [passedOnly, data, sortColumn, sortDirection])

  // Cycles a column through unsorted -> ascending -> descending -> unsorted
  // on repeated clicks, same convention as most sortable tables.
  const handleSort = (col: string) => {
    if (sortColumn !== col) {
      setSortColumn(col)
      setSortDirection('asc')
    } else if (sortDirection === 'asc') {
      setSortDirection('desc')
    } else {
      setSortColumn(null)
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

  const hasPassedColumn = data.columns.includes('Passed')
  const filteredRows = hasPassedColumn && passedOnly ? data.rows.filter((r) => r.Passed === true) : data.rows
  const passedCount = hasPassedColumn ? data.rows.filter((r) => r.Passed === true).length : 0

  const rows = sortColumn
    ? [...filteredRows].sort((a, b) => {
        const av = a[sortColumn]
        const bv = b[sortColumn]
        // Nulls always sort to the end, regardless of direction, so sorting
        // never buries real values behind a page of blanks.
        if (av === null || av === undefined) return bv === null || bv === undefined ? 0 : 1
        if (bv === null || bv === undefined) return -1

        let cmp: number
        if (typeof av === 'number' && typeof bv === 'number') {
          cmp = av - bv
        } else if (typeof av === 'boolean' && typeof bv === 'boolean') {
          cmp = Number(av) - Number(bv)
        } else {
          cmp = String(av).localeCompare(String(bv))
        }
        return sortDirection === 'asc' ? cmp : -cmp
      })
    : filteredRows

  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize))
  const currentPage = Math.min(page, totalPages)
  const pageRows = rows.slice((currentPage - 1) * pageSize, currentPage * pageSize)

  return (
    <main className="flex-1 overflow-y-auto px-6 py-10">
      <div className="mx-auto flex max-w-[1060px] flex-col gap-5">
        <div className="flex flex-col gap-2">
          <h1 className="text-[22px] font-extrabold tracking-tight">Results</h1>
          <p className="max-w-[620px] text-[13.5px] leading-relaxed text-gray-500">
            Today's candidates from the last screener run, ranked by closeness score.
          </p>
        </div>

        {data.rows.length === 0 ? (
          <div className="rounded-[14px] border border-gray-200 bg-white p-10 text-center text-[13px] text-gray-400 shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
            No report yet. Run the screener from the Run tab first.
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              {hasPassedColumn ? (
                <div className="flex rounded-[9px] bg-gray-100 p-[3px]">
                  <button
                    onClick={() => setPassedOnly(false)}
                    className={`rounded-[7px] px-3.5 py-1.5 text-[12.5px] font-semibold ${
                      !passedOnly ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:bg-gray-200/50'
                    }`}
                  >
                    All stocks
                  </button>
                  <button
                    onClick={() => setPassedOnly(true)}
                    className={`rounded-[7px] px-3.5 py-1.5 text-[12.5px] font-semibold ${
                      passedOnly ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:bg-gray-200/50'
                    }`}
                  >
                    Passed only
                  </button>
                </div>
              ) : (
                <div />
              )}
              <div className="font-mono text-[11.5px] text-gray-400">
                {data.rows.length} rows{hasPassedColumn ? ` · ${passedCount} passed` : ''}
              </div>
            </div>

            <div ref={tableWrapperRef} className="flex overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
              {isScrollable && (
                <button
                  onClick={() => scrollRef.current?.scrollBy({ left: -130, behavior: 'smooth' })}
                  disabled={!canScrollLeft}
                  aria-label="Scroll table left"
                  className="mr-2 flex w-10 flex-shrink-0 items-center justify-center bg-accent hover:brightness-95 disabled:cursor-default disabled:bg-gray-300 disabled:hover:brightness-100"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#FFFFFF"
                    strokeWidth="2.75"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="15 6 9 12 15 18" />
                  </svg>
                </button>
              )}
              <div ref={scrollRef} className="min-w-0 flex-1 overflow-x-auto">
                <table className="w-full border-separate border-spacing-0" style={{ minWidth: `${Math.max(700, data.columns.length * 130)}px` }}>
                  <thead>
                    <tr className="bg-[#FAFAFB]">
                      {data.columns.map((col) => {
                        const isNumericCol = typeof rows[0]?.[col] === 'number'
                        const isSorted = sortColumn === col
                        return (
                          <th
                            key={col}
                            onClick={() => handleSort(col)}
                            aria-sort={isSorted ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}
                            className={`sticky top-0 cursor-pointer select-none whitespace-nowrap border-b border-gray-100 px-3.5 py-2.5 text-[10.5px] font-bold uppercase tracking-wide hover:text-gray-600 ${
                              isSorted ? 'text-gray-600' : 'text-gray-400'
                            } ${
                              col === 'Symbol'
                                ? 'left-0 z-20 bg-[#FAFAFB] text-left'
                                : `z-10 bg-[#FAFAFB] ${isNumericCol ? 'text-right' : 'text-left'}`
                            }`}
                          >
                            <span className={`inline-flex items-center gap-1 ${isNumericCol ? 'flex-row-reverse' : ''}`}>
                              {col}
                              <span className={`text-[9px] ${isSorted ? 'opacity-100' : 'opacity-30'}`}>
                                {isSorted && sortDirection === 'desc' ? '▼' : '▲'}
                              </span>
                            </span>
                          </th>
                        )
                      })}
                    </tr>
                  </thead>
                  <tbody>
                    {pageRows.map((row, i) => (
                      <tr key={i} className="group">
                        {data.columns.map((col) => {
                          if (col === 'Symbol') {
                            return (
                              <td
                                key={col}
                                className="sticky left-0 z-10 whitespace-nowrap border-b border-gray-100 bg-white px-3.5 py-2.5 font-mono text-xs font-bold text-gray-900 group-hover:bg-[#FAFAFB]"
                              >
                                {row[col]}
                              </td>
                            )
                          }
                          if (col === 'Passed') {
                            const passed = row[col] === true
                            return (
                              <td key={col} className="whitespace-nowrap border-b border-gray-100 px-3.5 py-2.5 group-hover:bg-[#FAFAFB]">
                                <span
                                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                                    passed ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                                  }`}
                                >
                                  {passed ? 'Passed' : 'Failed'}
                                </span>
                              </td>
                            )
                          }
                          if (col === 'FailedRules') {
                            const full = String(row[col] ?? '')
                            return (
                              <td
                                key={col}
                                title={full}
                                className="max-w-[260px] overflow-hidden text-ellipsis whitespace-nowrap border-b border-gray-100 px-3.5 py-2.5 text-xs text-gray-400 group-hover:bg-[#FAFAFB]"
                              >
                                {full || '—'}
                              </td>
                            )
                          }
                          const isNumeric = typeof row[col] === 'number'
                          return (
                            <td
                              key={col}
                              className={`whitespace-nowrap border-b border-gray-100 px-3.5 py-2.5 text-xs text-gray-700 group-hover:bg-[#FAFAFB] ${
                                isNumeric ? 'text-right font-mono' : ''
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

              {isScrollable && (
                <button
                  onClick={() => scrollRef.current?.scrollBy({ left: 130, behavior: 'smooth' })}
                  disabled={!canScrollRight}
                  aria-label="Scroll table right"
                  className="ml-2 flex w-10 flex-shrink-0 items-center justify-center bg-accent hover:brightness-95 disabled:cursor-default disabled:bg-gray-300 disabled:hover:brightness-100"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#FFFFFF"
                    strokeWidth="2.75"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="9 6 15 12 9 18" />
                  </svg>
                </button>
              )}
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <div className="font-mono text-[11.5px] text-gray-400">
                  Showing {(currentPage - 1) * pageSize + 1}-{Math.min(currentPage * pageSize, rows.length)} of {rows.length}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="rounded-[7px] border border-gray-200 bg-white px-3 py-1.5 text-[12.5px] font-semibold text-gray-700 hover:bg-gray-50 disabled:cursor-default disabled:opacity-40 disabled:hover:bg-white"
                  >
                    Prev
                  </button>
                  <div className="px-1 font-mono text-[12px] text-gray-500">
                    Page {currentPage} of {totalPages}
                  </div>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="rounded-[7px] border border-gray-200 bg-white px-3 py-1.5 text-[12.5px] font-semibold text-gray-700 hover:bg-gray-50 disabled:cursor-default disabled:opacity-40 disabled:hover:bg-white"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  )
}
