import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { lazy, Suspense, type ReactNode } from 'react'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { AppShell } from '../layouts/AppShell'
import { LoadingState } from '../components/ui'
import { ForecastDraftProvider } from './ForecastDraftContext'
const OverviewPage=lazy(()=>import('../features/overview/OverviewPage').then(m=>({default:m.OverviewPage})))
const ForecastPage=lazy(()=>import('../features/forecasting/ForecastPage').then(m=>({default:m.ForecastPage})))
const SegmentsPage=lazy(()=>import('../features/customers/SegmentsPage').then(m=>({default:m.SegmentsPage})))
const ReturnRiskPage=lazy(()=>import('../features/customers/ReturnRiskPage').then(m=>({default:m.ReturnRiskPage})))
const RecommendationsPage=lazy(()=>import('../features/recommendations/RecommendationsPage').then(m=>({default:m.RecommendationsPage})))
const AnomaliesPage=lazy(()=>import('../features/anomalies/AnomaliesPage').then(m=>({default:m.AnomaliesPage})))
const InventoryPage=lazy(()=>import('../features/inventory/InventoryPage').then(m=>({default:m.InventoryPage})))
const SystemPage=lazy(()=>import('../features/system/SystemPage').then(m=>({default:m.SystemPage})))
const NotFoundPage=lazy(()=>import('../features/NotFoundPage').then(m=>({default:m.NotFoundPage})))
const page=(node:ReactNode)=><Suspense fallback={<LoadingState label="Loading page"/>}>{node}</Suspense>
export const queryClient=new QueryClient({defaultOptions:{queries:{staleTime:30_000,retry:1},mutations:{retry:false}}})
export const router=createBrowserRouter([{element:<AppShell/>,children:[{index:true,element:page(<OverviewPage/>)},{path:'forecasting',element:page(<ForecastPage/>)},{path:'customers/segments',element:page(<SegmentsPage/>)},{path:'customers/return-risk',element:page(<ReturnRiskPage/>)},{path:'recommendations',element:page(<RecommendationsPage/>)},{path:'anomalies',element:page(<AnomaliesPage/>)},{path:'inventory',element:page(<InventoryPage/>)},{path:'system/models',element:page(<SystemPage/>)},{path:'*',element:page(<NotFoundPage/>)}]}])
export function App(){return <QueryClientProvider client={queryClient}><ForecastDraftProvider><RouterProvider router={router}/></ForecastDraftProvider></QueryClientProvider>}
