'use client';

import { Header, StatsCard, DataTable, StatusBadge } from '@/components';
import { MiniStatsCard } from '@/components/StatsCard';
import { useStats, useOrders, useHealth } from '@/hooks/useApi';
import { formatRelativeTime, getSupplierLabel, cn } from '@/lib/utils';
import {
  ShoppingCart,
  CheckCircle,
  XCircle,
  Clock,
  Mail,
  Package,
  Activity,
  AlertTriangle,
  ArrowRight,
  Zap,
  TrendingUp,
} from 'lucide-react';
import type { Order } from '@/lib/api';
import Link from 'next/link';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useStats();
  const { data: health } = useHealth();
  const { data: ordersData, isLoading: ordersLoading } = useOrders({ page: 1, page_size: 5 });

  const recentOrderColumns = [
    {
      key: 'order_code',
      header: 'Sipariş Kodu',
      render: (order: Order) => (
        <span className="font-semibold text-gray-900">{order.order_code}</span>
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

  const services = health?.services || {};
  const allServicesRunning = Object.values(services).every(s => s === 'running');

  return (
    <div className="min-h-screen">
      <Header title="Dashboard" subtitle="Sipariş otomasyon sistemine genel bakış" />

      <div className="p-6 space-y-6">
        {/* Welcome Banner */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary-600 via-primary-500 to-primary-600 p-6 text-white">
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-5 h-5" />
              <span className="text-sm font-medium text-primary-100">DoruMake Otomasyon</span>
            </div>
            <h2 className="text-2xl font-bold mb-1">Hosgeldiniz!</h2>
            <p className="text-primary-100 max-w-lg">
              Sipariş otomasyon sisteminiz aktif ve çalışıyor. Günlük operasyonlarınızı buradan takip edebilirsiniz.
            </p>
          </div>
          {/* Decorative elements */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 right-20 w-32 h-32 bg-white/10 rounded-full translate-y-1/2" />
        </div>

        {/* System Status Bar */}
        <div className="card-static p-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <div className={cn(
                'p-2 rounded-xl',
                allServicesRunning ? 'bg-success-100' : 'bg-danger-100'
              )}>
                <Activity className={cn(
                  'w-5 h-5',
                  allServicesRunning ? 'text-success-600' : 'text-danger-600'
                )} />
              </div>
              <div>
                <p className="font-semibold text-gray-900">Sistem Durumu</p>
                <p className="text-sm text-gray-500">
                  {allServicesRunning ? 'Tüm servisler aktif' : 'Bazı servisler çalışmıyor'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              {Object.entries(services).map(([service, status]) => (
                <div key={service} className="flex items-center gap-2">
                  <span className={cn(
                    'w-2.5 h-2.5 rounded-full',
                    status === 'running'
                      ? 'bg-success-500 shadow-sm shadow-success-500/50'
                      : 'bg-danger-500 shadow-sm shadow-danger-500/50'
                  )} />
                  <span className="text-sm font-medium text-gray-600 capitalize">
                    {service.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard
            title="Bugünkü Siparişler"
            value={stats?.today_orders ?? 0}
            icon={ShoppingCart}
            color="primary"
            loading={statsLoading}
          />
          <StatsCard
            title="Başarılı"
            value={stats?.today_successful ?? 0}
            icon={CheckCircle}
            color="success"
            loading={statsLoading}
          />
          <StatsCard
            title="Başarısız"
            value={stats?.today_failed ?? 0}
            icon={XCircle}
            color="danger"
            loading={statsLoading}
          />
          <StatsCard
            title="Bekleyen"
            value={stats?.pending_orders ?? 0}
            icon={Clock}
            color="warning"
            loading={statsLoading}
          />
        </div>

        {/* Secondary Stats - Queue Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MiniStatsCard
            title="Bugünkü E-postalar"
            value={stats?.today_emails ?? 0}
            icon={Mail}
            color="primary"
            loading={statsLoading}
          />
          <MiniStatsCard
            title="Mutlu Akü Kuyruğu"
            value={stats?.queue_mutlu ?? 0}
            icon={Package}
            color="warning"
            loading={statsLoading}
          />
          <MiniStatsCard
            title="Mann & Hummel Kuyruğu"
            value={stats?.queue_mann ?? 0}
            icon={Package}
            color="success"
            loading={statsLoading}
          />
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Orders - Takes 2 columns */}
          <div className="lg:col-span-2 card-static">
            <div className="flex items-center justify-between p-5 border-b border-gray-100">
              <div>
                <h2 className="font-semibold text-gray-900">Son Siparişler</h2>
                <p className="text-sm text-gray-500 mt-0.5">Son işlenen siparişler</p>
              </div>
              <Link
                href="/orders"
                className="flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors"
              >
                Tümünü gör
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="p-5">
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

          {/* Alerts / Quick Actions */}
          <div className="space-y-4">
            {/* Alerts Card */}
            <div className="card-static">
              <div className="p-5 border-b border-gray-100">
                <h2 className="font-semibold text-gray-900">Uyarılar</h2>
              </div>
              <div className="p-5">
                {stats?.today_failed && stats.today_failed > 0 ? (
                  <div className="flex items-start gap-3 p-4 bg-danger-50 rounded-xl border border-danger-100">
                    <div className="p-2 bg-danger-100 rounded-lg">
                      <AlertTriangle className="w-5 h-5 text-danger-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-danger-700">Başarısız Siparişler</p>
                      <p className="text-sm text-danger-600 mt-1">
                        Bugün {stats.today_failed} sipariş başarısız oldu.
                      </p>
                      <Link
                        href="/orders?status=failed"
                        className="inline-flex items-center gap-1 text-sm font-medium text-danger-700 hover:text-danger-800 mt-2"
                      >
                        Detayları gör
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-3 p-4 bg-success-50 rounded-xl border border-success-100">
                    <div className="p-2 bg-success-100 rounded-lg">
                      <CheckCircle className="w-5 h-5 text-success-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-success-700">Her şey yolunda!</p>
                      <p className="text-sm text-success-600 mt-1">
                        Tüm sistemler sorunsuz çalışıyor.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Stats */}
            <div className="card-static p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-primary-100 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Hızlı Bakış</p>
                  <p className="text-sm text-gray-500">Günlük özet</p>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2 border-b border-gray-100">
                  <span className="text-sm text-gray-600">Başarı Oranı</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {stats?.today_orders
                      ? `${Math.round((stats.today_successful / stats.today_orders) * 100) || 0}%`
                      : '-'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-gray-100">
                  <span className="text-sm text-gray-600">Toplam Kuyruk</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {(stats?.queue_mutlu ?? 0) + (stats?.queue_mann ?? 0)}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-gray-600">İşlem Bekleyen</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {stats?.pending_orders ?? 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
