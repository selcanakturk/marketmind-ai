import '@testing-library/jest-dom/vitest'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { cleanup } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { handlers } from './mocks'
export const server=setupServer(...handlers)
beforeAll(()=>server.listen({onUnhandledRequest:'error'}));afterEach(()=>{cleanup();server.resetHandlers()});afterAll(()=>server.close())
class ResizeObserver { observe(){} unobserve(){} disconnect(){} }
Object.defineProperty(globalThis,'ResizeObserver',{value:ResizeObserver,writable:true})
Object.defineProperty(window,'matchMedia',{value:()=>({matches:false,addEventListener(){},removeEventListener(){}}),writable:true})
Object.defineProperty(HTMLCanvasElement.prototype,'getContext',{value:()=>null,writable:true})
