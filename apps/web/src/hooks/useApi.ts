'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/lib/api';

// Health & Stats
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: apiService.getHealth,
    refetchInterval: 30000, // 30 seconds
  });
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: apiService.getStats,
    refetchInterval: 10000, // 10 seconds
  });
}

// Orders
export function useOrders(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  supplier?: string;
}) {
  return useQuery({
    queryKey: ['orders', params],
    queryFn: () => apiService.getOrders(params),
    refetchInterval: 15000, // 15 seconds
  });
}

export function useOrder(orderId: string) {
  return useQuery({
    queryKey: ['order', orderId],
    queryFn: () => apiService.getOrder(orderId),
    enabled: !!orderId,
  });
}

export function useOrderLogs(orderId: string) {
  return useQuery({
    queryKey: ['orderLogs', orderId],
    queryFn: () => apiService.getOrderLogs(orderId),
    enabled: !!orderId,
    refetchInterval: 5000, // 5 seconds for active orders
  });
}

export function useRetryOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (orderId: string) => apiService.retryOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}

// Emails
export function useEmails(params?: {
  page?: number;
  page_size?: number;
  status?: string;
}) {
  return useQuery({
    queryKey: ['emails', params],
    queryFn: () => apiService.getEmails(params),
    refetchInterval: 15000,
  });
}

// Logs
export function useLogs(params?: {
  page?: number;
  page_size?: number;
  level?: string;
  source?: string;
}) {
  return useQuery({
    queryKey: ['logs', params],
    queryFn: () => apiService.getLogs(params),
    refetchInterval: 5000, // 5 seconds
  });
}

// Suppliers
export function useSuppliers() {
  return useQuery({
    queryKey: ['suppliers'],
    queryFn: apiService.getSuppliers,
  });
}

// Scheduler
export function useSchedulerJobs() {
  return useQuery({
    queryKey: ['scheduler-jobs'],
    queryFn: apiService.getSchedulerJobs,
    refetchInterval: 60000, // 1 minute
  });
}

// Manual Order
export function useCreateManualOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: apiService.createManualOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}
