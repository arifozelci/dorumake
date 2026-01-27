'use client';

import { useState } from 'react';
import { Header } from '@/components';
import { useLogs } from '@/hooks/useApi';
import { formatDate, cn } from '@/lib/utils';
import { RefreshCw, Filter, AlertCircle, Info, AlertTriangle, Bug } from 'lucide-react';
import type { LogEntry } from '@/lib/api';

const levelConfig: Record<string, { icon: any; color: string; bg: string }> = {
  error: { icon: AlertCircle, color: 'text-danger-600', bg: 'bg-danger-50' },
  warning: { icon: AlertTriangle, color: 'text-warning-600', bg: 'bg-warning-50' },
  info: { icon: Info, color: 'text-primary-600', bg: 'bg-primary-50' },
  debug: { icon: Bug, color: 'text-gray-600', bg: 'bg-gray-50' },
};

export default function LogsPage() {
  const [page, setPage] = useState(1);
  const [levelFilter, setLevelFilter] = useState<string>('');
  const [sourceFilter, setSourceFilter] = useState<string>('');
  const pageSize = 50;

  const { data, isLoading, refetch } = useLogs({
    page,
    page_size: pageSize,
    level: levelFilter || undefined,
    source: sourceFilter || undefined,
  });

  const LogItem = ({ log }: { log: LogEntry }) => {
    const config = levelConfig[log.level.toLowerCase()] || levelConfig.info;
    const Icon = config.icon;

    return (
      <div className={cn('p-3 border-b border-gray-100 hover:bg-gray-50', config.bg)}>
        <div className="flex items-start gap-3">
          <div className={cn('p-1.5 rounded', config.bg)}>
            <Icon className={cn('w-4 h-4', config.color)} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={cn('text-xs font-medium uppercase', config.color)}>
                {log.level}
              </span>
              <span className="text-xs text-gray-400">|</span>
              <span className="text-xs text-gray-500">{log.source}</span>
              <span className="text-xs text-gray-400">|</span>
              <span className="text-xs text-gray-500">{formatDate(log.timestamp)}</span>
            </div>
            <p className="text-sm text-gray-900 break-all">{log.message}</p>
            {log.details && (
              <pre className="mt-2 text-xs text-gray-600 bg-gray-100 p-2 rounded overflow-x-auto">
                {JSON.stringify(log.details, null, 2)}
              </pre>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div>
      <Header title="Sistem Logları" subtitle="Sistem aktivitelerini ve hataları izleyin" />

      <div className="p-6">
        {/* Filters */}
        <div className="card p-4 mb-6">
          <div className="flex items-center gap-4">
            <Filter className="w-5 h-5 text-gray-400" />
            <div className="flex items-center gap-4">
              <select
                value={levelFilter}
                onChange={(e) => {
                  setLevelFilter(e.target.value);
                  setPage(1);
                }}
                className="input w-32"
              >
                <option value="">Tüm Seviyeler</option>
                <option value="error">Error</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
                <option value="debug">Debug</option>
              </select>

              <select
                value={sourceFilter}
                onChange={(e) => {
                  setSourceFilter(e.target.value);
                  setPage(1);
                }}
                className="input w-40"
              >
                <option value="">Tüm Kaynaklar</option>
                <option value="robot">Robot</option>
                <option value="email">E-posta</option>
                <option value="api">API</option>
                <option value="scheduler">Zamanlayıcı</option>
              </select>

              <button onClick={() => refetch()} className="btn btn-secondary">
                <RefreshCw className="w-4 h-4 mr-2" />
                Yenile
              </button>
            </div>
          </div>
        </div>

        {/* Log Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="card p-4 border-l-4 border-l-danger-500">
            <p className="text-sm text-gray-500">Hatalar</p>
            <p className="text-2xl font-semibold text-danger-600">
              {data?.stats?.error_count ?? 0}
            </p>
          </div>
          <div className="card p-4 border-l-4 border-l-warning-500">
            <p className="text-sm text-gray-500">Uyarılar</p>
            <p className="text-2xl font-semibold text-warning-600">
              {data?.stats?.warning_count ?? 0}
            </p>
          </div>
          <div className="card p-4 border-l-4 border-l-primary-500">
            <p className="text-sm text-gray-500">Bilgi</p>
            <p className="text-2xl font-semibold text-primary-600">
              {data?.stats?.info_count ?? 0}
            </p>
          </div>
          <div className="card p-4 border-l-4 border-l-gray-400">
            <p className="text-sm text-gray-500">Debug</p>
            <p className="text-2xl font-semibold text-gray-600">
              {data?.stats?.debug_count ?? 0}
            </p>
          </div>
        </div>

        {/* Logs List */}
        <div className="card">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Log Kayıtları</h2>
            <span className="text-sm text-gray-500">
              Toplam {data?.total ?? 0} kayıt
            </span>
          </div>

          {isLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto" />
              <p className="mt-4 text-gray-500">Yükleniyor...</p>
            </div>
          ) : data?.logs && data.logs.length > 0 ? (
            <div className="max-h-[600px] overflow-y-auto">
              {data.logs.map((log) => (
                <LogItem key={log.id} log={log} />
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-gray-500">Log kaydı bulunamadı</div>
          )}

          {/* Pagination */}
          {data && data.total > pageSize && (
            <div className="p-4 border-t border-gray-100 flex items-center justify-between">
              <span className="text-sm text-gray-500">
                Sayfa {page} / {Math.ceil(data.total / pageSize)}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="btn btn-secondary text-sm"
                >
                  Önceki
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= Math.ceil(data.total / pageSize)}
                  className="btn btn-secondary text-sm"
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
