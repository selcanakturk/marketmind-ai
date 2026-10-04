import { ArrowRight, Boxes, ChartNoAxesCombined, Database, PackageSearch, ShieldAlert, Sparkles, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useModels, useReady } from '../../api/queries'
import type { ModuleKey } from '../../types/api'
import { Banner, ErrorState, LoadingState, StatusBadge } from '../../components/ui'

const workflows: Array<{ module: ModuleKey; name: string; question: string; path: string; Icon: typeof ChartNoAxesCombined }> = [
  { module: 'forecasting', name: 'Forecast demand', question: 'How much are we likely to sell?', path: '/forecasting', Icon: ChartNoAxesCombined },
  { module: 'anomalies', name: 'Detect unusual sales', question: 'Did actual sales depart from expectations?', path: '/anomalies', Icon: ShieldAlert },
  { module: 'inventory', name: 'Plan inventory', question: 'What should we replenish—and why?', path: '/inventory', Icon: Boxes },
  { module: 'segmentation', name: 'Understand customers', question: 'Which behavioral groups are present?', path: '/customers/segments', Icon: Users },
  { module: 'recommendations', name: 'Recommend products', question: 'Which items best match recent interest?', path: '/recommendations', Icon: Sparkles },
  { module: 'return_risk', name: 'Prioritize re-engagement', question: 'Who should receive limited outreach?', path: '/customers/return-risk', Icon: PackageSearch },
]

const evidence = [['6', 'Intelligence engines'], ['3', 'Real-world datasets'], ['28 days', 'Forecast horizon'], ['3.43M', 'Item-neighbor edges'], ['6', 'Production artifacts']] as const

export function OverviewPage() {
  const ready = useReady()
  const models = useModels()
  if (ready.isLoading || models.isLoading) return <><header className="overview-hero"><div><div className="eyebrow">MarketMind AI</div><h1>Retail intelligence, from data to decisions.</h1></div></header><LoadingState label="Loading system capabilities" /></>
  const readyCount = ready.data ? Object.values(ready.data.modules).filter(Boolean).length : 0
  const modelByModule = new Map(models.data?.models.map(model => [model.module, model]))
  return <div className="overview-page">
    <header className="overview-hero">
      <div className="overview-hero-copy"><div className="eyebrow">MarketMind AI</div><h1>Retail intelligence,<br /><span>from data to decisions.</span></h1><p>Six focused workflows turn historical retail signals into transparent forecasts, priorities, and decisions—without pretending unrelated datasets describe the same customer.</p><div className="hero-actions"><Link className="button" to="/forecasting">Start with demand <ArrowRight size={16} /></Link><Link className="text-link" to="/system/models">Explore system evidence <ArrowRight size={15} /></Link></div></div>
      <div className="intelligence-map" aria-label="MarketMind intelligence workflow map"><div className="map-track"><span>Demand</span><ArrowRight /><span>Detect</span><ArrowRight /><span>Decide</span></div><div className="map-track secondary"><span>Understand</span><ArrowRight /><span>Recommend</span><ArrowRight /><span>Re-engage</span></div><p>Independent workflows, connected by clear decisions—not fabricated identity.</p></div>
    </header>
    {ready.isError && <ErrorState error={ready.error} />}{ready.data?.status === 'degraded' && <Banner tone="warning" title="Service is degraded">Unavailable modules remain visible; unaffected workflows can still run.</Banner>}
    <section className="evidence-strip" aria-label="Verified project evidence">{evidence.map(([value, label]) => <div className="evidence-item" key={label}><strong>{value}</strong><span>{label}</span></div>)}<div className="evidence-item live"><span className={`readiness-dot ${ready.data?.status === 'ready' ? 'positive' : 'warning'}`} aria-hidden="true" /><strong>{readyCount} / 6 ready</strong><span>Live readiness</span></div></section>
    <section className="overview-section" aria-labelledby="workflows-title"><div className="section-heading"><div><div className="eyebrow">Decision workflows</div><h2 id="workflows-title">Start with the business question.</h2></div><p>Each engine is bounded to the evidence its source can support.</p></div><div className="workflow-grid">{workflows.map(({ module, name, question, path, Icon }) => { const model = modelByModule.get(module); const available = model?.ready ?? ready.data?.modules[module] ?? false; return <article className="workflow-card" key={module}><div className="workflow-card-top"><div className="workflow-icon"><Icon size={19} aria-hidden="true" /></div><StatusBadge status={available ? 'success' : 'danger'}>{available ? 'Ready' : 'Unavailable'}</StatusBadge></div><h3>{name}</h3><p>{question}</p><Link className="workflow-link" to={available ? path : '/system/models'}>{available ? 'Open workflow' : 'View system status'} <ArrowRight size={15} /></Link></article> })}</div></section>
    <section className="dataset-foundation" aria-labelledby="datasets-title"><div className="dataset-intro"><Database size={22} aria-hidden="true" /><div><div className="eyebrow">Dataset foundation</div><h2 id="datasets-title">Real sources. Honest boundaries.</h2><p>Each dataset powers only the questions its historical structure can answer.</p></div></div><div className="dataset-list"><article><strong>M5</strong><span>Demand, anomaly, and inventory forecast context</span></article><article><strong>Complete Journey 2.0</strong><span>Segmentation and re-engagement</span></article><article><strong>RetailRocket</strong><span>Product recommendations</span></article></div><p className="boundary-note"><strong>No cross-dataset identity.</strong> MarketMind does not fabricate a Customer 360 across unrelated sources.</p></section>
  </div>
}
