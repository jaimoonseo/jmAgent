import { ChangeEvent } from 'react'
import type { Model } from '@/types/actions'

interface ModelSelectorProps {
  value: Model
  onChange: (model: Model) => void
  label?: string
  disabled?: boolean
}

const MODELS: { value: Model; label: string; description: string }[] = [
  {
    value: 'haiku',
    label: 'Haiku 4.5',
    description: 'Fast & efficient (default)',
  },
  {
    value: 'sonnet',
    label: 'Sonnet 4.6',
    description: 'Balanced performance',
  },
  {
    value: 'opus',
    label: 'Opus 4.6',
    description: 'High quality output',
  },
]

export const ModelSelector = ({
  value,
  onChange,
  label = 'Model',
  disabled = false,
}: ModelSelectorProps) => {
  const handleChange = (e: ChangeEvent<HTMLSelectElement>) => {
    onChange(e.target.value as Model)
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-slate-900">{label}</label>
      <select
        value={value}
        onChange={handleChange}
        disabled={disabled}
        className="px-4 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-slate-100 disabled:cursor-not-allowed"
      >
        {MODELS.map((model) => (
          <option key={model.value} value={model.value}>
            {model.label} - {model.description}
          </option>
        ))}
      </select>
    </div>
  )
}
