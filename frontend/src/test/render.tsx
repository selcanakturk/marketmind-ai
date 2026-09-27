import type { ReactElement } from 'react';import { QueryClient, QueryClientProvider } from '@tanstack/react-query';import { render } from '@testing-library/react';import { MemoryRouter } from 'react-router-dom'
import { ForecastDraftProvider } from '../app/ForecastDraftContext'
export function renderPage(ui:ReactElement){const client=new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}});return render(<QueryClientProvider client={client}><ForecastDraftProvider><MemoryRouter>{ui}</MemoryRouter></ForecastDraftProvider></QueryClientProvider>)}
