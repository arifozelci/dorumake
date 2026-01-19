'use client';

import { useState } from 'react';
import { Header, DataTable, StatusBadge } from '@/components';
import { useEmails } from '@/hooks/useApi';
import { formatDate, truncate } from '@/lib/utils';
import { RefreshCw, Filter, Paperclip, Mail as MailIcon } from 'lucide-react';
import type { Email } from '@/lib/api';

export default function EmailsPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
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
            <p className="text-2xl font-semibold text-warning-500">-</p>
          </div>
          <div className="card p-4">
            <p className="text-sm text-gray-500">İşlenen</p>
            <p className="text-2xl font-semibold text-success-500">-</p>
          </div>
          <div className="card p-4">
            <p className="text-sm text-gray-500">Başarısız</p>
            <p className="text-2xl font-semibold text-danger-500">-</p>
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
          />
        </div>
      </div>
    </div>
  );
}
