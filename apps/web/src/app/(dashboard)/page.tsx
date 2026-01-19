'use client';

import { Header, StatsCard, DataTable, StatusBadge } from '@/components';
import { useStats, useOrders, useHealth } from '@/hooks/useApi';
import { formatDate, formatRelativeTime, getSupplierLabel, truncate } from '@/lib/utils';
import {
  ShoppingCart,
  CheckCircle,
  XCircle,
  Clock,
  Mail,
  Box,
  Activity,
  AlertTriangle,
} from 'lucide-react';
import type { Order } from '@/lib/api';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useStats();
  const { data: health } = useHealth();
  const { data: ordersData, isLoading: ordersLoading } = useOrders({ page: 1, page_size: 5 });

  const recentOrderColumns = [
    {
      key: 'order_code',
      header: 'Sipariş Kodu',
      render: (order: Order) => (
        <span className="font-medium text-gray-900">{order.order_code}</span>
      ),
    },
    {
      key: 'supplier_type',
      header: 'Tedarikçi',
      render: (order: Order) => (
        <span className="text-gray-600">{getSupplierLabel(order.supplier_type)}</span>
      ),
    },
    {
      key: 'status',
      header: 'Durum',
      render: (order: Order) => <StatusBadge status={order.status} />,
    },
    {
      key: 'created_at',
      header: 'Tarih',
      render: (order: Order) => (
        <span className="text-gray-500 text-sm">{formatRelativeTime(order.created_at)}</span>
      ),
    },
  ];

  return (
    <div>
      <Header title="Dashboard" subtitle="Sipariş otomasyon sistemine genel bakış" />

      <div className="p-6">
        {/* System Status */}
        <div className="mb-6 card p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="w-5 h-5 text-green-500" />
              <span className="font-medium">Sistem Durumu</span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              {health?.services &&
                Object.entries(health.services).map(([service, status]) => (
                  <div key={service} className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        status === 'running' ? 'bg-green-500' : 'bg-red-500'
                      }`}
                    />
                    <span className="text-gray-600 capitalize">{service.replace('_', ' ')}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Bugünkü Siparişler"
            value={statsLoading ? '-' : stats?.today_orders ?? 0}
            icon={ShoppingCart}
            color="primary"
          />
          <StatsCard
            title="Başarılı"
            value={statsLoading ? '-' : stats?.today_successful ?? 0}
            icon={CheckCircle}
            color="success"
          />
          <StatsCard
            title="Başarısız"
            value={statsLoading ? '-' : stats?.today_failed ?? 0}
            icon={XCircle}
            color="danger"
          />
          <StatsCard
            title="Bekleyen"
            value={statsLoading ? '-' : stats?.pending_orders ?? 0}
            icon={Clock}
            color="warning"
          />
        </div>

        {/* Secondary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatsCard
            title="Bugünkü E-postalar"
            value={statsLoading ? '-' : stats?.today_emails ?? 0}
            icon={Mail}
            color="primary"
          />
          <StatsCard
            title="Mutlu Akü Kuyruğu"
            value={statsLoading ? '-' : stats?.queue_mutlu ?? 0}
            icon={Box}
            color="primary"
          />
          <StatsCard
            title="Mann & Hummel Kuyruğu"
            value={statsLoading ? '-' : stats?.queue_mann ?? 0}
            icon={Box}
            color="primary"
          />
        </div>

        {/* Recent Orders */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <div className="p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">Son Siparişler</h2>
            </div>
            <div className="p-4">
              <DataTable
                columns={recentOrderColumns}
                data={ordersData?.orders ?? []}
                page={1}
                pageSize={5}
                total={ordersData?.total ?? 0}
                onPageChange={() => {}}
                isLoading={ordersLoading}
                emptyMessage="Henüz sipariş yok"
              />
            </div>
          </div>

          {/* Alerts / Warnings */}
          <div className="card">
            <div className="p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">Uyarılar</h2>
            </div>
            <div className="p-4">
              {stats?.today_failed && stats.today_failed > 0 ? (
                <div className="flex items-start gap-3 p-4 bg-danger-50 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-danger-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-danger-600">Başarısız Siparişler</p>
                    <p className="text-sm text-gray-600 mt-1">
                      Bugün {stats.today_failed} sipariş başarısız oldu. Siparişler sayfasından
                      detayları kontrol edebilirsiniz.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3 p-4 bg-success-50 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-success-500" />
                  <p className="text-success-600">Tüm sistemler sorunsuz çalışıyor</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
