'use client';

import { useState } from 'react';
import { Header, DataTable, StatusBadge } from '@/components';
import { useEmails } from '@/hooks/useApi';
import { formatDate, truncate } from '@/lib/utils';
import { RefreshCw, Filter, Paperclip, Mail as MailIcon, X, FileSpreadsheet, Download, Eye } from 'lucide-react';
import type { Email } from '@/lib/api';

function EmailDetailModal({
  email,
  onClose
}: {
  email: Email | null;
  onClose: () => void;
}) {
  if (!email) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">E-posta Detayı</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Email Info */}
          <div className="space-y-4 mb-6">
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider">Konu</label>
              <p className="text-gray-900 font-medium mt-1">{email.subject}</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-wider">Gönderen</label>
                <p className="text-gray-900 mt-1">{email.from_address}</p>
              </div>
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-wider">Tarih</label>
                <p className="text-gray-900 mt-1">{formatDate(email.received_at)}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-wider">Durum</label>
                <div className="mt-1">
                  <StatusBadge status={email.status} />
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-500 uppercase tracking-wider">Sipariş E-postası</label>
                <p className="text-gray-900 mt-1">
                  {email.is_order_email ? (
                    <span className="text-success-600 font-medium">Evet</span>
                  ) : (
                    <span className="text-gray-500">Hayır</span>
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Attachments */}
          {email.attachments && email.attachments.length > 0 && (
            <div className="mb-6">
              <label className="text-xs text-gray-500 uppercase tracking-wider">Ekler ({email.attachments.length})</label>
              <div className="mt-2 space-y-2">
                {email.attachments.map((attachment, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-success-100 rounded-lg">
                        <FileSpreadsheet className="w-5 h-5 text-success-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{attachment}</p>
                        <p className="text-xs text-gray-500">Excel Dosyası</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                        title="Önizle"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                        title="İndir"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Body Preview */}
          {email.body_text && (
            <div>
              <label className="text-xs text-gray-500 uppercase tracking-wider">İçerik</label>
              <div className="mt-2 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
                  {email.body_text}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-100 bg-gray-50">
          <button
            onClick={onClose}
            className="btn btn-secondary w-full"
          >
            Kapat
          </button>
        </div>
      </div>
    </div>
  );
}

export default function EmailsPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const pageSize = 20;

  const { data, isLoading, refetch } = useEmails({
    page,
    page_size: pageSize,
    status: statusFilter || undefined,
  });

  const columns = [
    {
      key: 'subject',
      header: 'Konu',
      render: (email: Email) => (
        <div className="flex items-center gap-2">
          <MailIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <span className="font-medium text-gray-900" title={email.subject}>
            {truncate(email.subject, 50)}
          </span>
          {email.has_attachments && (
            <div className="flex items-center gap-1 text-gray-400">
              <Paperclip className="w-3.5 h-3.5" />
              <span className="text-xs">{email.attachment_count}</span>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'from_address',
      header: 'Gönderen',
      render: (email: Email) => (
        <span className="text-gray-600">{truncate(email.from_address, 30)}</span>
      ),
    },
    {
      key: 'status',
      header: 'Durum',
      render: (email: Email) => <StatusBadge status={email.status} />,
    },
    {
      key: 'received_at',
      header: 'Alınma Tarihi',
      render: (email: Email) => (
        <span className="text-gray-500 text-sm">{formatDate(email.received_at)}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (email: Email) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setSelectedEmail(email);
          }}
          className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
          title="Detay"
        >
          <Eye className="w-4 h-4" />
        </button>
      ),
    },
  ];

  return (
    <div>
      <Header title="E-postalar" subtitle="Gelen sipariş e-postalarını görüntüleyin" />

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
                <option value="processed">İşlendi</option>
                <option value="failed">Başarısız</option>
                <option value="ignored">Göz Ardı Edildi</option>
              </select>

              <button onClick={() => refetch()} className="btn btn-secondary">
                <RefreshCw className="w-4 h-4 mr-2" />
                Yenile
              </button>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="card p-4">
            <p className="text-sm text-gray-500">Toplam E-posta</p>
            <p className="text-2xl font-semibold text-gray-900">{data?.total ?? 0}</p>
          </div>
          <div className="card p-4">
            <p className="text-sm text-gray-500">Bekleyen</p>
            <p className="text-2xl font-semibold text-warning-500">
              {data?.emails ? data.emails.filter(e => e.status === 'pending').length : 0}
            </p>
          </div>
          <div className="card p-4">
            <p className="text-sm text-gray-500">İşlenen</p>
            <p className="text-2xl font-semibold text-success-500">
              {data?.emails ? data.emails.filter(e => e.status === 'processed').length : 0}
            </p>
          </div>
          <div className="card p-4">
            <p className="text-sm text-gray-500">Başarısız</p>
            <p className="text-2xl font-semibold text-danger-500">
              {data?.emails ? data.emails.filter(e => e.status === 'failed').length : 0}
            </p>
          </div>
        </div>

        {/* Emails Table */}
        <div className="card">
          <DataTable
            columns={columns}
            data={data?.emails ?? []}
            page={page}
            pageSize={pageSize}
            total={data?.total ?? 0}
            onPageChange={setPage}
            isLoading={isLoading}
            emptyMessage="E-posta bulunamadı"
            onRowClick={(email: Email) => setSelectedEmail(email)}
          />
        </div>
      </div>

      {/* Email Detail Modal */}
      {selectedEmail && (
        <EmailDetailModal
          email={selectedEmail}
          onClose={() => setSelectedEmail(null)}
        />
      )}
    </div>
  );
}
