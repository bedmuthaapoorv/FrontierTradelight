import { useEffect, useState } from 'react'
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

export default function Results() {
  const [data, setData] = useState<ResultsResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [passedOnly, setPassedOnly] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE_URL}/results`)
      .then((res) => {
        if (!res.ok) throw new Error(`Request to /results failed with ${res.status}`)
        return res.json() as Promise<ResultsResponse>
      })
      .then(setData)
      .catch((err) => setError(err.message))
  }, [])

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
  const rows = hasPassedColumn && passedOnly ? data.rows.filter((r) => r.Passed === true) : data.rows
  const passedCount = hasPassedColumn ? data.rows.filter((r) => r.Passed === true).length : 0

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

            <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse" style={{ minWidth: `${Math.max(700, data.columns.length * 130)}px` }}>
                  <thead>
                    <tr className="border-b border-gray-100 bg-[#FAFAFB]">
                      {data.columns.map((col) => (
                        <th
                          key={col}
                          className={`sticky top-0 whitespace-nowrap px-3.5 py-2.5 text-[10.5px] font-bold uppercase tracking-wide text-gray-400 ${
                            col === 'Symbol' ? 'left-0 bg-[#FAFAFB] text-left' : typeof rows[0]?.[col] === 'number' ? 'text-right' : 'text-left'
                          }`}
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, i) => (
                      <tr key={i} className="border-b border-gray-100 hover:bg-[#FAFAFB]">
                        {data.columns.map((col) => {
                          if (col === 'Symbol') {
                            return (
                              <td key={col} className="sticky left-0 whitespace-nowrap bg-white px-3.5 py-2.5 font-mono text-xs font-bold text-gray-900">
                                {row[col]}
                              </td>
                            )
                          }
                          if (col === 'Passed') {
                            const passed = row[col] === true
                            return (
                              <td key={col} className="whitespace-nowrap px-3.5 py-2.5">
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
                                className="max-w-[260px] overflow-hidden text-ellipsis whitespace-nowrap px-3.5 py-2.5 text-xs text-gray-400"
                              >
                                {full || '—'}
                              </td>
                            )
                          }
                          const isNumeric = typeof row[col] === 'number'
                          return (
                            <td
                              key={col}
                              className={`whitespace-nowrap px-3.5 py-2.5 text-xs text-gray-700 ${
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
            </div>
          </>
        )}
      </div>
    </main>
  )
}
