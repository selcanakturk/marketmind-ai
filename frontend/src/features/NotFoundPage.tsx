import { Link } from 'react-router-dom'
import { EmptyState, PageHeader } from '../components/ui'
export function NotFoundPage(){return <><PageHeader eyebrow="404" title="Page not found" description="This route is not part of the MarketMind workspace."/><EmptyState title="Nothing here"><Link className="button" to="/">Return to Overview</Link></EmptyState></>}
