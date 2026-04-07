import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ExecutionStats } from '@/components/ExecutionStats'
import type { TokensUsed } from '@/types/actions'

describe('ExecutionStats', () => {
  const mockTokens: TokensUsed = {
    input: 100,
    output: 50,
  }

  it('renders input token count', () => {
    render(
      <ExecutionStats tokens_used={mockTokens} execution_time={1.5} />
    )
    expect(screen.getByText('100')).toBeInTheDocument()
  })

  it('renders output token count', () => {
    render(
      <ExecutionStats tokens_used={mockTokens} execution_time={1.5} />
    )
    expect(screen.getByText('50')).toBeInTheDocument()
  })

  it('calculates and renders total tokens', () => {
    render(
      <ExecutionStats tokens_used={mockTokens} execution_time={1.5} />
    )
    expect(screen.getByText('150')).toBeInTheDocument()
  })

  it('renders execution time', () => {
    render(
      <ExecutionStats tokens_used={mockTokens} execution_time={2.345} />
    )
    expect(screen.getByText('2.35')).toBeInTheDocument()
  })

  it('shows cost estimate by default', () => {
    render(
      <ExecutionStats tokens_used={mockTokens} execution_time={1.5} />
    )
    expect(screen.getByText(/Estimated Cost/)).toBeInTheDocument()
  })

  it('hides cost estimate when showCostEstimate is false', () => {
    render(
      <ExecutionStats
        tokens_used={mockTokens}
        execution_time={1.5}
        showCostEstimate={false}
      />
    )
    expect(screen.queryByText(/Estimated Cost/)).not.toBeInTheDocument()
  })

  it('calculates cost correctly', () => {
    const tokens: TokensUsed = {
      input: 1000000, // 1M input tokens
      output: 1000000, // 1M output tokens
    }
    render(
      <ExecutionStats tokens_used={tokens} execution_time={1.5} />
    )
    // Cost = (1M * $0.80/1M) + (1M * $4.00/1M) = $0.80 + $4.00 = $4.80
    const costText = screen.getByText(/Estimated Cost/).parentElement?.textContent
    expect(costText).toContain('4.80')
  })

  it('displays all stat labels', () => {
    render(
      <ExecutionStats tokens_used={mockTokens} execution_time={1.5} />
    )
    expect(screen.getByText(/Input Tokens/)).toBeInTheDocument()
    expect(screen.getByText(/Output Tokens/)).toBeInTheDocument()
    expect(screen.getByText(/Total Tokens/)).toBeInTheDocument()
    expect(screen.getByText(/Time/)).toBeInTheDocument()
  })
})
