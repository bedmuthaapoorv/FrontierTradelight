import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { streamJob } from '../api'
import PipelineStep from '../components/PipelineStep'

type Status = 'idle' | 'running' | 'success' | 'error'

export default function Run() {
  const navigate = useNavigate()
  const [step1Status, setStep1Status] = useState<Status>('idle')
  const [step1Log, setStep1Log] = useState<string[]>([])
  const [step1Meta, setStep1Meta] = useState<string | null>(null)

  const [step2Status, setStep2Status] = useState<Status>('idle')
  const [step2Log, setStep2Log] = useState<string[]>([])
  const [step2Meta, setStep2Meta] = useState<string | null>(null)

  const runStep1 = () => {
    setStep1Status('running')
    setStep1Log([])
    streamJob('/jobs/generate-screener', (line) => setStep1Log((prev) => [...prev, line]))
      .then((code) => {
        setStep1Status(code === 0 ? 'success' : 'error')
        setStep1Meta(code === 0 ? 'Last run: just now' : `Exited with code ${code}`)
      })
      .catch((err) => {
        setStep1Status('error')
        setStep1Log((prev) => [...prev, err.message])
      })
  }

  const runStep2 = () => {
    setStep2Status('running')
    setStep2Log([])
    streamJob('/jobs/run-screener', (line) => setStep2Log((prev) => [...prev, line]))
      .then((code) => {
        setStep2Status(code === 0 ? 'success' : 'error')
        setStep2Meta(code === 0 ? 'Last run: just now' : `Exited with code ${code}`)
        if (code === 0) navigate('/results')
      })
      .catch((err) => {
        setStep2Status('error')
        setStep2Log((prev) => [...prev, err.message])
      })
  }

  return (
    <main className="flex-1 overflow-y-auto px-6 py-10">
      <div className="mx-auto flex max-w-[720px] flex-col gap-7">
        <div className="flex flex-col gap-2">
          <h1 className="text-[22px] font-extrabold tracking-tight">Run</h1>
          <p className="max-w-[560px] text-[13.5px] leading-relaxed text-gray-500">
            Compile <span className="font-mono text-[12.5px]">rules.md</span> into executable screening logic, then
            run it against the stock universe to produce today's candidates.
          </p>
        </div>

        <div className="flex flex-col">
          <PipelineStep
            stepNumber={1}
            title="Generate screening logic"
            description="Reads rules.md, calls Gemini, writes generated_rules.py. Requires GEMINI_API_KEY in .env."
            status={step1Status}
            idleLabel="Run generate_screener.py"
            runningLabel="Generating..."
            successLabel="Run again"
            onRun={runStep1}
            log={step1Log}
            meta={step1Meta}
          />

          <PipelineStep
            stepNumber={2}
            title="Run the screener"
            description="Fetches the stock universe and price history, scores each stock, writes stock_report.csv."
            status={step2Status}
            idleLabel="Run stock_screener.py"
            runningLabel="Screening..."
            successLabel="Run again"
            onRun={runStep2}
            log={step2Log}
            meta={step2Meta}
            showConnector={false}
          />
        </div>
      </div>
    </main>
  )
}
