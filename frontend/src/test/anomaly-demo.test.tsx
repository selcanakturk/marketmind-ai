import { fireEvent, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { expect, it, vi } from 'vitest'
import { API_BASE_URL } from '../api/config'
import { AnomaliesPage } from '../features/anomalies/AnomaliesPage'
import type { AnomalyRequest } from '../types/api'
import { renderPage } from './render'
import { server } from './setup'

const editorValue = (label: string) => JSON.parse((screen.getByLabelText(label) as HTMLTextAreaElement).value)

it('loads a deterministic one-date anomaly demo with aligned actual and expected rows', async () => {
  renderPage(<AnomaliesPage />)
  await userEvent.click(screen.getByRole('button', { name: 'Load demo input' }))
  await userEvent.click(screen.getByText('Advanced input'))

  const actual = editorValue('Observed actual sales — required')
  const expected = editorValue('Expected sales')
  const actualDates = new Set(actual.map((row: { date: string }) => row.date))
  const expectedDates = new Set(expected.map((row: { date: string }) => row.date))

  expect(actualDates).toEqual(new Set(['2016-05-23']))
  expect(expectedDates).toEqual(actualDates)
  expect(actual.map(({ date, store_id, dept_id }: typeof actual[number]) => ({ date, store_id, dept_id })))
    .toEqual(expected.map(({ date, store_id, dept_id }: typeof expected[number]) => ({ date, store_id, dept_id })))
  expect(editorValue('Optional calendar context')).toEqual([])
})

it('submits the built-in anomaly demo successfully under the one-date API contract', async () => {
  const received = vi.fn()
  server.use(http.post(`${API_BASE_URL}/api/v1/anomalies`, async ({ request }) => {
    const body = await request.json() as AnomalyRequest
    received(body)
    const dates = new Set(body.actual_sales.map(row => row.date))
    if (dates.size !== 1) return HttpResponse.json({ error: { code: 'ENGINE_VALIDATION_ERROR', message: 'score_batch accepts exactly one date', details: null }, request_id: 'demo-test' }, { status: 422 })
    return HttpResponse.json({ meta: { module_version: 'v1', artifact_version: '1', generated_at: '2026-09-27T00:00:00Z', warnings: [] }, rows: [] })
  }))
  renderPage(<AnomaliesPage />)
  await userEvent.click(screen.getByRole('button', { name: 'Load demo input' }))
  await userEvent.click(screen.getByRole('button', { name: 'Preview anomalies' }))

  expect(await screen.findByText('Observed sales assessment')).toBeInTheDocument()
  expect(received).toHaveBeenCalledOnce()
})

it('passes user-entered multi-date input through unchanged and displays engine validation', async () => {
  const received = vi.fn()
  server.use(http.post(`${API_BASE_URL}/api/v1/anomalies`, async ({ request }) => {
    const body = await request.json() as AnomalyRequest
    received(body)
    return HttpResponse.json({ error: { code: 'ENGINE_VALIDATION_ERROR', message: 'score_batch accepts exactly one date', details: null }, request_id: 'invalid-test' }, { status: 422 })
  }))
  renderPage(<AnomaliesPage />)
  await userEvent.click(screen.getByText('Advanced input'))
  const invalidActual = [
    { date: '2016-05-23', store_id: 'CA_1', dept_id: 'FOODS_1', actual_sales: 120 },
    { date: '2016-05-24', store_id: 'CA_1', dept_id: 'FOODS_1', actual_sales: 70 },
  ]
  fireEvent.change(screen.getByLabelText('Observed actual sales — required'), { target: { value: JSON.stringify(invalidActual) } })
  await userEvent.click(screen.getByRole('button', { name: 'Preview anomalies' }))

  expect(await screen.findByText('ENGINE_VALIDATION_ERROR')).toBeInTheDocument()
  expect(screen.getByText('score_batch accepts exactly one date')).toBeInTheDocument()
  expect(received.mock.calls[0][0].actual_sales).toEqual(invalidActual)
})

it('renders zero alerts and review priority as independent successful statuses', async () => {
  server.use(http.post(`${API_BASE_URL}/api/v1/anomalies`, () => HttpResponse.json({ meta: { module_version: 'v1', artifact_version: '1', generated_at: '2026-09-27T00:00:00Z', warnings: [] }, rows: [{ date: '2016-05-23T00:00:00Z', store_id: 'CA_1', dept_id: 'FOODS_1', actual_sales: 120, expected_sales: 100, residual: 20, anomaly_score: 1.2, direction: 'spike', is_statistical_alert: false, daily_review_rank: 1, is_review_priority: true, if_anomaly_score: null, event_name: null, event_type: null, snap_active: 0, undefined_score_reason: null }] })))
  renderPage(<AnomaliesPage />)
  await userEvent.click(screen.getByRole('button', { name: 'Preview anomalies' }))
  expect(await screen.findByText('No statistical alert')).toBeInTheDocument()
  expect(screen.getAllByText('Review priority').length).toBeGreaterThan(0)
})
