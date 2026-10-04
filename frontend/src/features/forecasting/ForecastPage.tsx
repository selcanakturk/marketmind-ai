import { useMemo, useState } from 'react'
import { ArrowRight, CalendarDays, Database, TrendingUp } from 'lucide-react'
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { useInference } from '../../api/queries'
import { ChartContainer, Disclosure, EmptyState, ErrorState, PageHeader, RunButton, Table, Warnings } from '../../components/ui'
import { JsonEditor } from '../../components/JsonEditor'
import { demoLabels, forecastDemo } from '../../demo/fixtures'
import type { CalendarRow, ForecastRequest, HistoryRow } from '../../types/api'
import { useForecastDrafts } from '../../app/ForecastDraftContext'

export function ForecastPage() {
  const demo = forecastDemo()
  const [history, setHistory] = useState<HistoryRow[]>(demo.history)
  const [calendar, setCalendar] = useState<CalendarRow[]>(demo.future_calendar)
  const mutation = useInference<ForecastRequest, Awaited<ReturnType<typeof api.forecast>>>(api.forecast)
  const navigate = useNavigate()
  const drafts = useForecastDrafts()
  const series = useMemo(() => new Set(history.map(row => `${row.store_id}::${row.dept_id}`)).size, [history])
  const first = history[0]
  const submit = (event: React.FormEvent) => { event.preventDefault(); mutation.mutate({ history, future_calendar: calendar }) }
  const chart = [...history.map(row => ({ date: row.date, historical: row.sales, forecast: null })), ...(mutation.data?.rows ?? []).map(row => ({ date: row.date, historical: null, forecast: row.predicted_sales }))]
  const summary = useMemo(() => { const rows = mutation.data?.rows ?? []; const total = rows.reduce((sum, row) => sum + row.predicted_sales, 0); const peak = rows.reduce<typeof rows[number] | undefined>((best, row) => !best || row.predicted_sales > best.predicted_sales ? row : best, undefined); return { total, average: rows.length ? total / rows.length : 0, peak, series: new Set(rows.map(row => `${row.store_id}::${row.dept_id}`)).size } }, [mutation.data])
  const loadDemo = () => { const next = forecastDemo(); setHistory(next.history); setCalendar(next.future_calendar) }
  const toInventory = () => { if (!mutation.data) return; drafts.createInventoryDraft(mutation.data.rows); void navigate('/inventory') }
  const toAnomalies = () => { if (!mutation.data) return; drafts.createAnomalyDraft(mutation.data.rows, calendar); void navigate('/anomalies') }
  return <div className="workflow-page forecast-page">
    <PageHeader eyebrow="Demand intelligence" title="Demand Forecasting" description="How much are we likely to sell over the next 28 days?" />
    <form onSubmit={submit}><section className="input-workspace" aria-labelledby="forecast-setup-title">
      <div className="workspace-heading"><div><div className="eyebrow">Forecast setup</div><h2 id="forecast-setup-title">Review the demand window</h2><p>{demoLabels.forecast}</p></div><button className="button secondary" type="button" onClick={loadDemo}>Load demo input</button></div>
      <div className="input-summary forecast-input-summary"><div><span>Store</span><strong>{first?.store_id ?? 'Not supplied'}</strong></div><div><span>Department</span><strong>{first?.dept_id ?? 'Not supplied'}</strong></div><div><span>Historical window</span><strong>{history.length} days</strong></div><div><span>Forecast horizon</span><strong>{calendar.length} days</strong></div><div><span>Series</span><strong>{series}</strong></div></div>
      <Disclosure summary="Advanced input"><p className="muted small">Edit the complete API payload. Validation remains authoritative and input is never silently corrected.</p><div className="json-grid"><JsonEditor id="forecast-history" label="Historical daily sales" value={history} onChange={setHistory} help="At least 56 shared consecutive dates per series; maximum 70 series." /><JsonEditor id="forecast-calendar" label="Future calendar" value={calendar} onChange={setCalendar} help="Exactly 28 consecutive dates beginning after the common cutoff." /></div></Disclosure>
      <div className="workspace-action"><RunButton pending={mutation.isPending}>Generate 28-day forecast</RunButton><span>Point forecast · no confidence interval</span></div>
    </section></form>
    {mutation.isError && <ErrorState error={mutation.error} />}
    <div aria-live="polite">{mutation.data ? <section className="result-zone" aria-labelledby="forecast-result-title">
      <div className="result-heading"><div><div className="eyebrow">Forecast result</div><h2 id="forecast-result-title">28-day demand outlook</h2></div><div className="result-actions"><button className="text-link" type="button" onClick={toInventory}>Use forecast in Inventory <ArrowRight size={15} /></button><button className="text-link" type="button" onClick={toAnomalies}>Use forecast as expected sales <ArrowRight size={15} /></button></div></div>
      <Warnings warnings={mutation.data.meta.warnings} />
      <div className="metric-cluster forecast-metrics"><div><Database /><span>Total predicted sales</span><strong>{summary.total.toFixed(1)}</strong></div><div><TrendingUp /><span>Average per forecast row</span><strong>{summary.average.toFixed(1)}</strong></div><div><CalendarDays /><span>Peak forecast day</span><strong>{summary.peak ? `${summary.peak.date.slice(0, 10)} · ${summary.peak.predicted_sales.toFixed(1)}` : '—'}</strong></div><div><ArrowRight /><span>Series count</span><strong>{summary.series}</strong></div></div>
      <div className="primary-chart"><ChartContainer title="Historical context and 28-day forecast" summary={`${history.length} submitted historical observations and ${mutation.data.rows.length} returned forecast rows. No uncertainty interval is provided by V1.`}><ResponsiveContainer><LineChart data={chart}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" minTickGap={28} /><YAxis /><Tooltip /><Legend /><ReferenceLine x={mutation.data.rows[0]?.date} stroke="#7c3aed" strokeDasharray="4 4" label="Forecast starts" /><Line type="linear" dataKey="historical" stroke="#64748b" dot={false} connectNulls={false} /><Line type="linear" dataKey="forecast" stroke="#5b35d5" strokeWidth={3} dot={false} connectNulls={false} /></LineChart></ResponsiveContainer></ChartContainer></div>
      <Disclosure summary="Technical details"><Table caption="Returned 28-day point forecasts" headers={['Date', 'Store', 'Department', 'State', 'Horizon', 'Predicted sales']} rows={mutation.data.rows.map(row => [row.date.slice(0, 10), row.store_id, row.dept_id, row.state_id, row.horizon, <span className="number">{row.predicted_sales.toFixed(2)}</span>])} /></Disclosure>
    </section> : <section className="pre-result"><EmptyState>Review the setup, then generate a forecast to see the 28-day demand outlook.</EmptyState></section>}</div>
  </div>
}
