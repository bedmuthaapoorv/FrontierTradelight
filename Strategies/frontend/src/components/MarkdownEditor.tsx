import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

interface MarkdownEditorProps {
  value: string
  onChange: (value: string) => void
  height?: number
  toolbarExtra?: React.ReactNode
  footer?: React.ReactNode
}

/** Edit/Preview segmented toggle over a textarea, mirroring
 * ui_helpers.editable_markdown - swaps between an editable textarea and a
 * rendered Markdown view of the same content, in the same space. */
export default function MarkdownEditor({ value, onChange, height = 460, toolbarExtra, footer }: MarkdownEditorProps) {
  const [mode, setMode] = useState<'edit' | 'preview'>('edit')

  return (
    <div className="overflow-hidden rounded-[14px] border border-gray-200 bg-white shadow-[0_1px_2px_rgba(16,24,40,0.03)]">
      <div className="flex items-center justify-between gap-3 border-b border-gray-100 p-3">
        <div className="flex rounded-[9px] bg-gray-100 p-[3px]">
          <button
            onClick={() => setMode('edit')}
            className={`rounded-[7px] px-3.5 py-1.5 text-[12.5px] font-semibold transition ${
              mode === 'edit' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:bg-gray-200/50'
            }`}
          >
            Edit
          </button>
          <button
            onClick={() => setMode('preview')}
            className={`rounded-[7px] px-3.5 py-1.5 text-[12.5px] font-semibold transition ${
              mode === 'preview' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:bg-gray-200/50'
            }`}
          >
            Preview
          </button>
        </div>
        {toolbarExtra}
      </div>

      {mode === 'preview' ? (
        <div
          className="overflow-y-auto bg-white p-7 prose prose-sm max-w-none"
          style={{ height }}
        >
          <ReactMarkdown>{value}</ReactMarkdown>
        </div>
      ) : (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          spellCheck={false}
          style={{ height }}
          className="w-full resize-none border-0 bg-[#FCFCFD] p-5 font-mono text-[12.5px] leading-[1.7] text-gray-900 focus:outline-none focus:ring-2 focus:ring-accent/20"
        />
      )}

      {footer}
    </div>
  )
}
