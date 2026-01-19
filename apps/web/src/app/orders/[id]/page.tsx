'use client';

import { useParams, useRouter } from 'next/navigation';
import { Header, StatusBadge } from '@/components';
import { useOrder, useRetryOrder } from '@/hooks/useApi';
import { formatDate, getSupplierLabel } from '@/lib/utils';
import { ArrowLeft, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import Link from 'next/link';

export default function OrderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.id as string;

  const { data: order, isLoading, error } = useOrder(orderId);
  const retryMutation = useRetryOrder();

  const handleRetry = async () => {
    if (confirm('Bu siparişi yeniden denemek istediğinize emin misiniz?')) {
      await retryMutation.mutateAsync(orderId);
    }
  };

  if (isLoading) {
    return (
      <div>
        <Header title="Sipariş Detayı" />
        <div className="p-6">
          <div className="card p-8 text-center">
            <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto" />
            <p className="mt-4 text-gray-500">Yükleniyor...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div>
        <Header title="Sipariş Detayı" />
        <div className="p-6">
          <div className="card p-8 text-center">
            <AlertCircle className="w-12 h-12 text-danger-500 mx-auto" />
            <p className="mt-4 text-gray-900 font-medium">Sipariş bulunamadı</p>
            <p className="mt-2 text-gray-500">İstenen sipariş mevcut değil veya silinmiş olabilir.</p>
            <Link href="/orders" className="btn btn-primary mt-4 inline-flex items-center">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Siparişlere Dön
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Header
        title={`Sipariş: ${order.order_code}`}
        subtitle={getSupplierLabel(order.supplier_type)}
      />

      <div className="p-6">
        {/* Back Button */}
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="w-4 h-4" />
            Geri
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Order Details */}
            <div className="card">
              <div className="p-4 border-b border-gray-100">
                <h2 className="font-semibold text-gray-900">Sipariş Bilgileri</h2>
              </div>
              <div className="p-4 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Sipariş Kodu</p>
                  <p className="font-medium text-gray-900">{order.order_code}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Tedarikçi</p>
                  <p className="font-medium text-gray-900">{getSupplierLabel(order.supplier_type)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Müşteri</p>
                  <p className="font-medium text-gray-900">{order.customer_name || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Ürün Sayısı</p>
                  <p className="font-medium text-gray-900">{order.item_count} adet</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Toplam Tutar</p>
                  <p className="font-medium text-gray-900">
                    {order.total_amount ? `₺${order.total_amount.toLocaleString()}` : '-'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Durum</p>
                  <StatusBadge status={order.status} />
                </div>
              </div>
            </div>

            {/* Timeline */}
            <div className="card">
              <div className="p-4 border-b border-gray-100">
                <h2 className="font-semibold text-gray-900">Zaman Çizelgesi</h2>
              </div>
              <div className="p-4">
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <CheckCircle className="w-4 h-4 text-primary-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">Sipariş Oluşturuldu</p>
                      <p className="text-sm text-gray-500">{formatDate(order.created_at)}</p>
                    </div>
                  </div>

                  {order.completed_at && (
                    <div className="flex items-start gap-3">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          order.status === 'completed'
                            ? 'bg-success-50'
                            : 'bg-danger-50'
                        }`}
                      >
                        {order.status === 'completed' ? (
                          <CheckCircle className="w-4 h-4 text-success-600" />
                        ) : (
                          <AlertCircle className="w-4 h-4 text-danger-600" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {order.status === 'completed' ? 'Tamamlandı' : 'Başarısız Oldu'}
                        </p>
                        <p className="text-sm text-gray-500">{formatDate(order.completed_at)}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Error Message */}
            {order.error_message && (
              <div className="card border-danger-200 bg-danger-50">
                <div className="p-4 border-b border-danger-200">
                  <h2 className="font-semibold text-danger-700">Hata Mesajı</h2>
                </div>
                <div className="p-4">
                  <p className="text-danger-700">{order.error_message}</p>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Actions */}
            <div className="card">
              <div className="p-4 border-b border-gray-100">
                <h2 className="font-semibold text-gray-900">İşlemler</h2>
              </div>
              <div className="p-4 space-y-3">
                {order.status === 'failed' && (
                  <button
                    onClick={handleRetry}
                    disabled={retryMutation.isPending}
                    className="btn btn-primary w-full flex items-center justify-center"
                  >
                    <RefreshCw
                      className={`w-4 h-4 mr-2 ${retryMutation.isPending ? 'animate-spin' : ''}`}
                    />
                    Yeniden Dene
                  </button>
                )}
                <Link
                  href="/orders"
                  className="btn btn-secondary w-full flex items-center justify-center"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Listeye Dön
                </Link>
              </div>
            </div>

            {/* Quick Info */}
            <div className="card">
              <div className="p-4 border-b border-gray-100">
                <h2 className="font-semibold text-gray-900">Hızlı Bilgi</h2>
              </div>
              <div className="p-4 space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">ID</span>
                  <span className="text-gray-900 font-mono">{order.id.slice(0, 8)}...</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Oluşturulma</span>
                  <span className="text-gray-900">{formatDate(order.created_at)}</span>
                </div>
                {order.completed_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Tamamlanma</span>
                    <span className="text-gray-900">{formatDate(order.completed_at)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
