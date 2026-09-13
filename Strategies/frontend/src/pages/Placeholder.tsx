type Props = { title: string }

export default function Placeholder({ title }: Props) {
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-sm text-gray-500">Not migrated yet - see the phased migration plan.</p>
    </div>
  )
}
