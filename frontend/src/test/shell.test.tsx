import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axe from 'axe-core'
import { http, HttpResponse } from 'msw'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { expect, it } from 'vitest'
import { API_BASE_URL } from '../api/config'
import { AppShell } from '../layouts/AppShell'
import { server } from './setup'

const destinations = [
  ['/', 'Overview test'],
  ['/forecasting', 'Forecast route'],
  ['/recommendations', 'Recommendations route'],
  ['/anomalies', 'Anomalies route'],
  ['/inventory', 'Inventory route'],
  ['/customers/segments', 'Segments route'],
  ['/customers/return-risk', 'Re-engagement route'],
  ['/system/models', 'Models route'],
] as const

function shell(initial='/') {
  const router=createMemoryRouter([{element:<AppShell/>,children:destinations.map(([path,title])=>path==='/'?{index:true,element:<h1>{title}</h1>}:{path,element:<h1>{title}</h1>})}],{initialEntries:[initial]})
  const client=new QueryClient({defaultOptions:{queries:{retry:false}}})
  const view=render(<QueryClientProvider client={client}><RouterProvider router={router}/></QueryClientProvider>)
  return {router,...view}
}

it('renders every desktop destination with the approved user-facing terminology',()=>{
  shell()
  for(const name of ['Overview','Forecasting','Recommendations','Anomalies','Inventory','Segmentation','Re-engagement','Models']) expect(screen.getByRole('link',{name})).toBeInTheDocument()
  expect(screen.getByRole('link',{name:'Re-engagement'})).toHaveAttribute('href','/customers/return-risk')
  expect(screen.queryByRole('link',{name:'Return Risk'})).not.toBeInTheDocument()
})

it('supports route navigation and exposes the active destination',async()=>{
  shell()
  const link=screen.getByRole('link',{name:'Forecasting'})
  await userEvent.click(link)
  expect(await screen.findByRole('heading',{name:'Forecast route'})).toBeInTheDocument()
  expect(link).toHaveClass('active')
  expect(link).toHaveAttribute('aria-current','page')
})

it('derives readiness text from live readiness data',async()=>{
  server.use(http.get(`${API_BASE_URL}/ready`,()=>HttpResponse.json({status:'degraded',modules:{forecasting:true,segmentation:true,return_risk:false,recommendations:true,anomalies:false,inventory:true}})))
  shell()
  expect((await screen.findAllByRole('link',{name:'4 of 6 engines ready. View Models and API.'})).length).toBeGreaterThan(0)
})

it('opens, traps focus, closes with Escape, and restores the mobile trigger',async()=>{
  shell()
  const open=screen.getByRole('button',{name:'Open navigation'})
  await userEvent.click(open)
  const close=screen.getAllByRole('button',{name:'Close navigation'}).at(-1)!
  expect(close).toHaveFocus()
  await userEvent.tab({shift:true})
  expect(screen.getAllByRole('link',{name:/View Models and API/}).at(-1)).toHaveFocus()
  await userEvent.tab()
  expect(close).toHaveFocus()
  await userEvent.keyboard('{Escape}')
  expect(open).toHaveFocus()
  expect(open).toHaveAttribute('aria-expanded','false')
})

it('closes the drawer after route selection',async()=>{
  const {container}=shell()
  const open=screen.getByRole('button',{name:'Open navigation'})
  await userEvent.click(open)
  await userEvent.click(screen.getByRole('link',{name:'Forecasting'}))
  await waitFor(()=>expect(open).toHaveAttribute('aria-expanded','false'))
  await screen.findByRole('heading',{name:'Forecast route'})
  expect(container.querySelector('#main-content')).toHaveFocus()
})

it('has no obvious shell accessibility violations',async()=>{
  const {container}=shell()
  await screen.findAllByRole('link',{name:/engines ready/})
  expect((await axe.run(container)).violations).toEqual([])
})
