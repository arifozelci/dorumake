'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header, StatusBadge } from '@/components';
import { useOrder, useOrderLogs, useRetryOrder, useProcessOrder } from '@/hooks/useApi';
import { formatDate, getSupplierLabel, cn } from '@/lib/utils';
import { downloadOrderAttachment, api } from '@/lib/api';
import { ArrowLeft, RefreshCw, AlertCircle, CheckCircle, Play, Loader2, XCircle, Monitor, LogIn, User, Menu, FileText, Upload, Database, Send, Package, Download, FileSpreadsheet, X, Image as ImageIcon } from 'lucide-react';
import Link from 'next/link';

// Get icon for log action
function getActionIcon(action: string) {
  const icons: Record<string, React.ReactNode> = {
    portal_open: <Monitor className="w-4 h-4" />,
    login: <LogIn className="w-4 h-4" />,
    customer_select: <User className="w-4 h-4" />,
    menu_navigate: <Menu className="w-4 h-4" />,
    form_create: <FileText className="w-4 h-4" />,
    form_fill: <FileText className="w-4 h-4" />,
    products_tab: <Package className="w-4 h-4" />,
    products_add: <Package className="w-4 h-4" />,
    order_save: <Database className="w-4 h-4" />,
    order_submit: <Send className="w-4 h-4" />,
    sap_confirm: <CheckCircle className="w-4 h-4" />,
    complete: <CheckCircle className="w-4 h-4" />,
    csv_generate: <FileText className="w-4 h-4" />,
    file_upload: <Upload className="w-4 h-4" />,
    supplier_select: <User className="w-4 h-4" />,
  };
  return icons[action] || <Play className="w-4 h-4" />;
}

export default function OrderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.id as string;

  const { data: order, isLoading, error } = useOrder(orderId);
  const { data: logsData, isLoading: logsLoading } = useOrderLogs(orderId);
  const retryMutation = useRetryOrder();
  const processMutation = useProcessOrder();

  // Screenshot modal state
  const [screenshotModal, setScreenshotModal] = useState<{
    open: boolean;
    imageUrl: string | null;
    loading: boolean;
    error: string | null;
  }>({ open: false, imageUrl: null, loading: false, error: null });

  const handleViewScreenshot = async (screenshotPath: string) => {
    // Extract path after "screenshots/"
    let path = screenshotPath;
    if (path.startsWith('screenshots/')) {
      path = path.substring('screenshots/'.length);
    }

    setScreenshotModal({ open: true, imageUrl: null, loading: true, error: null });

    try {
      const response = await api.get(`/api/screenshots/${path}`, {
        responseType: 'blob'
      });
      const url = URL.createObjectURL(response.data);
      setScreenshotModal({ open: true, imageUrl: url, loading: false, error: null });
    } catch (err) {
      setScreenshotModal({ open: true, imageUrl: null, loading: false, error: 'Screenshot yüklenemedi' });
    }
  };

  const closeScreenshotModal = () => {
    if (screenshotModal.imageUrl) {
      URL.revokeObjectURL(screenshotModal.imageUrl);
    }
    setScreenshotModal({ open: false, imageUrl: null, loading: false, error: null });
  };

  const handleRetry = async () => {
    if (confirm('Bu siparişi yeniden denemek istediğinize emin misiniz?')) {
      await retryMutation.mutateAsync(orderId);
    }
  };

  const handleProcess = async () => {
    if (confirm('Bu siparişi işlemeye başlamak istediğinize emin misiniz?')) {
      await processMutation.mutateAsync(orderId);
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
            <Link href="/dashboard/orders" className="btn btn-primary mt-4 inline-flex items-center">
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
              {/* Portal Order Number - prominent display */}
              {order.portal_order_number && (
                <div className="px-4 pt-4">
                  <div className="bg-success-50 border border-success-200 rounded-lg p-4 flex items-center gap-3">
                    <CheckCircle className="w-6 h-6 text-success-600 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-success-700 font-medium">Portal Sipariş Numarası</p>
                      <p className="text-2xl font-bold text-success-800">{order.portal_order_number}</p>
                    </div>
                  </div>
                </div>
              )}

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

            {/* Operation Logs */}
            <div className="card">
              <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                <h2 className="font-semibold text-gray-900">İşlem Adımları</h2>
                {logsData && (
                  <span className="text-sm text-gray-500">{logsData.total} adım</span>
                )}
              </div>
              <div className="p-4">
                {logsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
                    <span className="ml-2 text-gray-500">Yükleniyor...</span>
                  </div>
                ) : logsData && logsData.logs.length > 0 ? (
                  <div className="relative">
                    {/* Vertical line */}
                    <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

                    <div className="space-y-4">
                      {logsData.logs.map((log, index) => (
                        <div key={log.id} className="relative flex items-start gap-4 pl-10">
                          {/* Step indicator */}
                          <div
                            className={cn(
                              'absolute left-0 w-8 h-8 rounded-full flex items-center justify-center',
                              log.status === 'success' && 'bg-success-100 text-success-600',
                              log.status === 'error' && 'bg-danger-100 text-danger-600',
                              log.status === 'processing' && 'bg-primary-100 text-primary-600'
                            )}
                          >
                            {log.status === 'processing' ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : log.status === 'error' ? (
                              <XCircle className="w-4 h-4" />
                            ) : (
                              getActionIcon(log.action)
                            )}
                          </div>

                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-medium text-gray-400">
                                Adım {log.step}
                              </span>
                              <span
                                className={cn(
                                  'text-xs px-1.5 py-0.5 rounded',
                                  log.status === 'success' && 'bg-success-50 text-success-700',
                                  log.status === 'error' && 'bg-danger-50 text-danger-700',
                                  log.status === 'processing' && 'bg-primary-50 text-primary-700'
                                )}
                              >
                                {log.status === 'success' ? 'Başarılı' : log.status === 'error' ? 'Hata' : 'İşleniyor'}
                              </span>
                            </div>
                            <p className="text-gray-900 mt-0.5">{log.message}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {formatDate(log.timestamp)}
                            </p>
                            {log.screenshot && (
                              <div className="mt-2">
                                <button
                                  onClick={() => handleViewScreenshot(log.screenshot!)}
                                  className="text-xs text-danger-600 bg-danger-50 px-2 py-1 rounded inline-flex items-center gap-1 hover:bg-danger-100 transition-colors cursor-pointer"
                                >
                                  <ImageIcon className="w-3 h-3" />
                                  Screenshot Görüntüle
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Play className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p>Henüz işlem kaydı yok</p>
                    <p className="text-sm">Sipariş işlenmeye başladığında adımlar burada görünecek</p>
                  </div>
                )}
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
                {(order.status === 'pending' || order.status === 'failed') && (
                  <button
                    onClick={handleProcess}
                    disabled={processMutation.isPending}
                    className="btn btn-success w-full flex items-center justify-center"
                  >
                    <Play
                      className={`w-4 h-4 mr-2 ${processMutation.isPending ? 'animate-pulse' : ''}`}
                    />
                    {processMutation.isPending ? 'İşleniyor...' : 'Siparişi İşle'}
                  </button>
                )}
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
                  href="/dashboard/orders"
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

            {/* Excel Attachment */}
            {order.attachment_filename && (
              <div className="card">
                <div className="p-4 border-b border-gray-100">
                  <h2 className="font-semibold text-gray-900">Sipariş Dosyası</h2>
                </div>
                <div className="p-4">
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="p-2 bg-success-100 rounded-lg">
                      <FileSpreadsheet className="w-6 h-6 text-success-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {order.attachment_filename}
                      </p>
                      <p className="text-xs text-gray-500">Excel Dosyası</p>
                    </div>
                  </div>
                  <button
                    onClick={() => downloadOrderAttachment(order.id, order.attachment_filename || 'order.xlsx')}
                    className="btn btn-primary w-full mt-3 flex items-center justify-center"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Excel İndir
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Screenshot Modal */}
      {screenshotModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70" onClick={closeScreenshotModal}>
          <div className="relative max-w-4xl max-h-[90vh] mx-4" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={closeScreenshotModal}
              className="absolute -top-10 right-0 text-white hover:text-gray-300"
            >
              <X className="w-8 h-8" />
            </button>

            {screenshotModal.loading && (
              <div className="bg-white rounded-lg p-8 text-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary-500 mx-auto" />
                <p className="mt-2 text-gray-500">Yükleniyor...</p>
              </div>
            )}

            {screenshotModal.error && (
              <div className="bg-white rounded-lg p-8 text-center">
                <AlertCircle className="w-12 h-12 text-danger-500 mx-auto" />
                <p className="mt-2 text-danger-600">{screenshotModal.error}</p>
              </div>
            )}

            {screenshotModal.imageUrl && (
              <img
                src={screenshotModal.imageUrl}
                alt="Hata Screenshot"
                className="max-w-full max-h-[85vh] rounded-lg shadow-2xl"
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
