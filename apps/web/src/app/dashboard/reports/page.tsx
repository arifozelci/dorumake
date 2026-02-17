'use client';

import { useState } from 'react';
import { Header } from '@/components';
import { useTeccomReport } from '@/hooks/useApi';
import { formatDate } from '@/lib/utils';
import { Download, Search, FileSpreadsheet, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';

interface TeccomOrder {
  id: string;
  customer_code: string;
  customer_name: string;
  created_at: string;
  order_code: string;
  total_items: number;
  portal_order_number: string | null;
  processed_at: string | null;
  status: string;
}

function StatusBadge({ status }: { status: string }) {
  const s = status?.toLowerCase();
  const cls =
    s === 'completed'
      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
      : s === 'failed'
        ? 'bg-red-50 text-red-700 border-red-200'
        : s === 'processing'
          ? 'bg-blue-50 text-blue-700 border-blue-200'
          : 'bg-gray-50 text-gray-700 border-gray-200';
  const label =
    s === 'completed' ? 'Tamamlandı' : s === 'failed' ? 'Başarısız' : s === 'processing' ? 'İşleniyor' : 'Bekliyor';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {label}
    </span>
  );
}

export default function ReportsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const pageSize = 50;

  const { data, isLoading, refetch } = useTeccomReport({ page, page_size: pageSize, search: search || undefined });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const handleDownload = async () => {
    try {
      const response = await api.get('/api/reports/teccom/download', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'TecCom_Siparis_Listesi.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      // silently fail
    }
  };

  const orders: TeccomOrder[] = data?.orders ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <Header
        title="Raporlar"
        subtitle="TecCom sipariş raporlarını görüntüleyin ve indirin"
        actions={
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition-colors text-sm font-medium shadow-sm"
          >
            <Download className="w-4 h-4" />
            Excel İndir
          </button>
        }
      />

      <div className="p-6">
        {/* Search & Info */}
        <div className="card p-4 mb-6">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="w-5 h-5 text-primary-500" />
              <div>
                <h3 className="text-sm font-semibold text-gray-900">TecCom Girilen Sipariş Listesi</h3>
                <p className="text-xs text-gray-500">Mann & Hummel portal siparişleri</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <form onSubmit={handleSearch} className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Sipariş kodu, müşteri ara..."
                    className="input pl-9 w-64"
                  />
                </div>
                <button type="submit" className="btn btn-secondary">
                  Ara
                </button>
              </form>
              <button onClick={() => refetch()} className="btn btn-secondary">
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50/80">
                  <th className="px-4 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Müşteri Kodu</th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Müşteri Adı</th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Sipariş Tarihi</th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Sipariş Kodu</th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Ürün Sayısı</th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">TECCOM SİPARİŞ NO</th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Kayıt Tarihi</th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Durum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i} className="animate-pulse">
                      {Array.from({ length: 8 }).map((_, j) => (
                        <td key={j} className="px-4 py-4"><div className="h-4 bg-gray-200 rounded w-3/4" /></td>
                      ))}
                    </tr>
                  ))
                ) : orders.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-gray-500">
                      Kayıt bulunamadı
                    </td>
                  </tr>
                ) : (
                  orders.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-4 py-3.5 text-gray-700 font-medium">{order.customer_code || '-'}</td>
                      <td className="px-4 py-3.5 text-gray-600 max-w-xs truncate">{order.customer_name || '-'}</td>
                      <td className="px-4 py-3.5 text-gray-500">{formatDate(order.created_at)}</td>
                      <td className="px-4 py-3.5 text-primary-600 font-medium">{order.order_code}</td>
                      <td className="px-4 py-3.5 text-gray-600 text-center">{order.total_items}</td>
                      <td className="px-4 py-3.5 font-semibold text-emerald-700">{order.portal_order_number || '-'}</td>
                      <td className="px-4 py-3.5 text-gray-500">{order.processed_at ? formatDate(order.processed_at) : '-'}</td>
                      <td className="px-4 py-3.5"><StatusBadge status={order.status} /></td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
              <p className="text-sm text-gray-500">
                Toplam <span className="font-medium text-gray-700">{total}</span> kayıt,
                sayfa <span className="font-medium text-gray-700">{page}</span> / {totalPages}
              </p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50 hover:bg-gray-50"
                >
                  Önceki
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-50 hover:bg-gray-50"
                >
                  Sonraki
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
