'use client';

import { useState } from 'react';
import { Header, DataTable, StatusBadge } from '@/components';
import { useOrders, useRetryOrder } from '@/hooks/useApi';
import { formatDate, getSupplierLabel, truncate } from '@/lib/utils';
import { RefreshCw, Eye, Filter } from 'lucide-react';
import type { Order } from '@/lib/api';
import Link from 'next/link';

export default function OrdersPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [supplierFilter, setSupplierFilter] = useState<string>('');
  const pageSize = 20;

  const { data, isLoading, refetch } = useOrders({
    page,
    page_size: pageSize,
    status: statusFilter || undefined,
    supplier: supplierFilter || undefined,
  });

  const retryMutation = useRetryOrder();

  const handleRetry = async (orderId: string) => {
    if (confirm('Bu siparişi yeniden denemek istediğinize emin misiniz?')) {
      await retryMutation.mutateAsync(orderId);
    }
  };

  const columns = [
    {
      key: 'order_code',
      header: 'Sipariş Kodu',
      render: (order: Order) => (
        <Link href={`/orders/${order.id}`} className="font-medium text-primary-600 hover:underline">
          {order.order_code}
        </Link>
      ),
    },
    {
      key: 'supplier_type',
      header: 'Tedarikçi',
      render: (order: Order) => (
        <span className="text-gray-700">{getSupplierLabel(order.supplier_type)}</span>
      ),
    },
    {
      key: 'customer_name',
      header: 'Müşteri',
      render: (order: Order) => (
        <span className="text-gray-600">{order.customer_name || '-'}</span>
      ),
    },
    {
      key: 'item_count',
      header: 'Ürün',
      render: (order: Order) => <span className="text-gray-600">{order.item_count} adet</span>,
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
        <span className="text-gray-500 text-sm">{formatDate(order.created_at)}</span>
      ),
    },
    {
      key: 'actions',
      header: 'İşlemler',
      render: (order: Order) => (
        <div className="flex items-center gap-2">
          <Link
            href={`/orders/${order.id}`}
            className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-gray-100 rounded"
            title="Detay"
          >
            <Eye className="w-4 h-4" />
          </Link>
          {order.status === 'failed' && (
            <button
              onClick={() => handleRetry(order.id)}
              disabled={retryMutation.isPending}
              className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-gray-100 rounded disabled:opacity-50"
              title="Yeniden Dene"
            >
              <RefreshCw className={`w-4 h-4 ${retryMutation.isPending ? 'animate-spin' : ''}`} />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <Header title="Siparişler" subtitle="Tüm sipariş işlemlerini görüntüleyin ve yönetin" />

      <div className="p-6">
        {/* Filters */}
        <div className="card p-4 mb-6">
          <div className="flex items-center gap-4">
            <Filter className="w-5 h-5 text-gray-400" />
            <div className="flex items-center gap-4">
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="input w-40"
              >
                <option value="">Tüm Durumlar</option>
                <option value="pending">Bekliyor</option>
                <option value="processing">İşleniyor</option>
                <option value="completed">Tamamlandı</option>
                <option value="failed">Başarısız</option>
              </select>

              <select
                value={supplierFilter}
                onChange={(e) => {
                  setSupplierFilter(e.target.value);
                  setPage(1);
                }}
                className="input w-48"
              >
                <option value="">Tüm Tedarikçiler</option>
                <option value="MUTLU">Mutlu Akü</option>
                <option value="MANN">Mann & Hummel</option>
              </select>

              <button onClick={() => refetch()} className="btn btn-secondary">
                <RefreshCw className="w-4 h-4 mr-2" />
                Yenile
              </button>
            </div>
          </div>
        </div>

        {/* Orders Table */}
        <div className="card">
          <DataTable
            columns={columns}
            data={data?.orders ?? []}
            page={page}
            pageSize={pageSize}
            total={data?.total ?? 0}
            onPageChange={setPage}
            isLoading={isLoading}
            emptyMessage="Sipariş bulunamadı"
          />
        </div>
      </div>
    </div>
  );
}
