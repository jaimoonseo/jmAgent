import type { TokensUsed } from '@/types/actions'

interface ExecutionStatsProps {
  tokens_used: TokensUsed
  execution_time: number
  showCostEstimate?: boolean
}

// Approximate pricing per 1M tokens (Claude Haiku)
const COST_PER_MILLION_INPUT = 0.80
const COST_PER_MILLION_OUTPUT = 4.00

export const ExecutionStats = ({
  tokens_used,
  execution_time,
  showCostEstimate = true,
}: ExecutionStatsProps) => {
  const totalTokens = tokens_used.input + tokens_used.output
  const estimatedCost =
    (tokens_used.input / 1000000) * COST_PER_MILLION_INPUT +
    (tokens_used.output / 1000000) * COST_PER_MILLION_OUTPUT

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-xs text-slate-600 uppercase tracking-wide">
            Input Tokens
          </div>
          <div className="text-lg font-semibold text-slate-900">
            {tokens_used.input}
          </div>
        </div>

        <div>
          <div className="text-xs text-slate-600 uppercase tracking-wide">
            Output Tokens
          </div>
          <div className="text-lg font-semibold text-slate-900">
            {tokens_used.output}
          </div>
        </div>

        <div>
          <div className="text-xs text-slate-600 uppercase tracking-wide">
            Total Tokens
          </div>
          <div className="text-lg font-semibold text-slate-900">
            {totalTokens}
          </div>
        </div>

        <div>
          <div className="text-xs text-slate-600 uppercase tracking-wide">
            Time (seconds)
          </div>
          <div className="text-lg font-semibold text-slate-900">
            {execution_time.toFixed(2)}
          </div>
        </div>

        {showCostEstimate && (
          <div className="col-span-2 md:col-span-4 pt-2 border-t border-slate-200">
            <div className="text-xs text-slate-600 uppercase tracking-wide">
              Estimated Cost
            </div>
            <div className="text-lg font-semibold text-slate-900">
              ${estimatedCost.toFixed(4)}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
