import { useState } from 'react'

type Status = 'idle' | 'running' | 'success' | 'error'

interface PipelineStepProps {
  stepNumber: number
  title: string
  description: string
  status: Status
  idleLabel: string
  runningLabel: string
  successLabel: string
  onRun: () => void
  log: string[]
  meta: string | null
  /** 0-100 while running; null/undefined shows an indeterminate bar. */
  progress?: number | null
  /** Whether this step's connector line down to the next step is "done"
   * (drawn green) - only the last step omits a connector. */
  showConnector?: boolean
}

/** One stage of the Run tab's generate → screen pipeline: a numbered badge
 * (checkmark once successful) linked to the next step by a vertical
 * connector, a card with a Run button, and a collapsible log tail. */
export default function PipelineStep({
  stepNumber,
  title,
  description,
  status,
  idleLabel,
  runningLabel,
  successLabel,
  onRun,
  log,
  meta,
  progress = null,
  showConnector = true,
}: PipelineStepProps) {
  const [logOpen, setLogOpen] = useState(false)

  const badgeClass =
    status === 'success'
      ? 'bg-green-600'
      : status === 'running'
        ? 'border-2 border-accent bg-accent-soft'
        : 'border-2 border-gray-200 bg-gray-100'

  const buttonClass =
    status === 'running' ? 'cursor-default bg-gray-300 text-white' : 'bg-accent text-white hover:brightness-95'

  const buttonLabel = status === 'running' ? runningLabel : status === 'success' ? successLabel : idleLabel

  return (
    <div className="flex gap-4">
      <div className="flex flex-shrink-0 flex-col items-center">
        <div className={`flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full ${badgeClass}`}>
          {status === 'success' ? (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          ) : (
            <span className={`font-mono text-xs font-bold ${status === 'running' ? 'text-accent' : 'text-gray-400'}`}>
              {stepNumber}
            </span>
          )}
        </div>
        {showConnector && (
          <div className={`my-0.5 min-h-[24px] w-0.5 flex-1 ${status === 'success' ? 'bg-green-600' : 'bg-gray-200'}`} />
        )}
      </div>

      <div className={`flex-1 ${showConnector ? 'pb-5' : ''}`}>
        <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
          <div className="p-[18px]">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="mb-[3px] text-[14px] font-bold">{title}</div>
                <p className="m-0 max-w-[400px] text-[12.5px] leading-relaxed text-gray-500">{description}</p>
              </div>
              <button
                onClick={onRun}
                disabled={status === 'running'}
                className={`flex flex-shrink-0 items-center gap-[7px] whitespace-nowrap rounded-[9px] px-[15px] py-2 text-[12.5px] font-semibold ${buttonClass}`}
              >
                {status === 'running' && (
                  <svg className="animate-spin" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round">
                    <path d="M12 2a10 10 0 0 1 10 10" />
                  </svg>
                )}
                {buttonLabel}
              </button>
            </div>
            {status === 'running' && (
              <div className="mt-4">
                <div
                  role="progressbar"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={progress ?? undefined}
                  className="relative h-1.5 overflow-hidden rounded-full bg-gray-100"
                >
                  {progress === null ? (
                    <div className="absolute inset-y-0 w-1/3 animate-pulse rounded-full bg-accent" />
                  ) : (
                    <div
                      className="h-full rounded-full bg-accent transition-[width] duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  )}
                </div>
                {progress !== null && (
                  <div className="mt-1 text-right text-[11px] text-gray-400">{Math.round(progress)}%</div>
                )}
              </div>
            )}
          </div>

          {log.length > 0 && (
            <div>
              <button
                onClick={() => setLogOpen((v) => !v)}
                className="flex w-full items-center justify-between border-t border-gray-100 px-[18px] py-2 hover:bg-gray-50"
              >
                <div className="flex items-center gap-2">
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#9AA0AC"
                    strokeWidth="2.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ transform: logOpen ? 'rotate(0deg)' : 'rotate(-90deg)' }}
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                  <span className="text-[11.5px] font-semibold text-gray-500">
                    {status === 'running' ? 'Running...' : 'View log'}
                  </span>
                </div>
                {meta && <span className="text-[11px] text-gray-400">{meta}</span>}
              </button>

              {logOpen && (
                <pre className="max-h-40 overflow-y-auto whitespace-pre-wrap border-t border-gray-100 bg-[#FCFCFD] px-[18px] py-3 font-mono text-[11.5px] leading-relaxed text-gray-500">
                  {log.join('\n')}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
