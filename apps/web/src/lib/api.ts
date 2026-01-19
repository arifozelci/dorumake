import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  services: Record<string, string>;
}

export interface StatsResponse {
  today_orders: number;
  today_successful: number;
  today_failed: number;
  pending_orders: number;
  today_emails: number;
  queue_mutlu: number;
  queue_mann: number;
}

export interface Order {
  id: string;
  order_code: string;
  supplier_type: string;
  status: string;
  customer_name: string | null;
  item_count: number;
  total_amount: number | null;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

export interface OrderListResponse {
  orders: Order[];
  total: number;
  page: number;
  page_size: number;
}

export interface Email {
  id: string;
  subject: string;
  from_address: string;
  received_at: string;
  status: string;
  has_attachments: boolean;
  attachment_count: number;
}

export interface EmailListResponse {
  emails: Email[];
  total: number;
  page: number;
  page_size: number;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: string;
  source: string;
  message: string;
  details: Record<string, any> | null;
}

export interface LogListResponse {
  logs: LogEntry[];
  total: number;
  page: number;
  page_size: number;
}

export interface Supplier {
  code: string;
  name: string;
  portal_url: string;
  active: boolean;
}

export interface SchedulerJob {
  id: string;
  name: string;
  next_run: string | null;
  trigger: string;
}

// API Functions
export const apiService = {
  // Health
  async getHealth(): Promise<HealthResponse> {
    const { data } = await api.get('/api/health');
    return data;
  },

  // Stats
  async getStats(): Promise<StatsResponse> {
    const { data } = await api.get('/api/stats');
    return data;
  },

  // Orders
  async getOrders(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    supplier?: string;
  }): Promise<OrderListResponse> {
    const { data } = await api.get('/api/orders', { params });
    return data;
  },

  async getOrder(orderId: string): Promise<Order> {
    const { data } = await api.get(`/api/orders/${orderId}`);
    return data;
  },

  async retryOrder(orderId: string): Promise<{ status: string; order_id: string }> {
    const { data } = await api.post(`/api/orders/${orderId}/retry`);
    return data;
  },

  // Emails
  async getEmails(params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<EmailListResponse> {
    const { data } = await api.get('/api/emails', { params });
    return data;
  },

  // Logs
  async getLogs(params?: {
    page?: number;
    page_size?: number;
    level?: string;
    source?: string;
  }): Promise<LogListResponse> {
    const { data } = await api.get('/api/logs', { params });
    return data;
  },

  // Suppliers
  async getSuppliers(): Promise<{ suppliers: Supplier[] }> {
    const { data } = await api.get('/api/suppliers');
    return data;
  },

  // Scheduler
  async getSchedulerJobs(): Promise<{ jobs: SchedulerJob[] }> {
    const { data } = await api.get('/api/scheduler/jobs');
    return data;
  },

  // Manual Order
  async createManualOrder(order: {
    supplier_type: string;
    order_code: string;
    customer_code: string;
    items: Array<{ product_code: string; quantity: number }>;
  }): Promise<{ status: string; order_id: string }> {
    const { data } = await api.post('/api/orders/manual', order);
    return data;
  },
};
