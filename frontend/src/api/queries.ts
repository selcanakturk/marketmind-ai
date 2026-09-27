import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from './client'

export const useHealth = () => useQuery({ queryKey: ['health'], queryFn: ({ signal }) => api.health(signal), retry: 1, refetchInterval: false })
export const useReady = () => useQuery({ queryKey: ['ready'], queryFn: ({ signal }) => api.ready(signal), retry: 1, refetchInterval: false })
export const useModels = () => useQuery({ queryKey: ['models'], queryFn: ({ signal }) => api.models(signal), retry: 1, refetchInterval: false })
export const useInference = <TInput, TOutput>(fn: (input: TInput) => Promise<TOutput>) => useMutation({ mutationFn: (input:TInput) => fn(input), retry: false })
