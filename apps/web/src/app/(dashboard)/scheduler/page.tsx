'use client';

import { Header } from '@/components';
import { useSchedulerJobs } from '@/hooks/useApi';
import { formatDate } from '@/lib/utils';
import { Calendar, Clock, RefreshCw, Play, Pause } from 'lucide-react';

export default function SchedulerPage() {
  const { data, isLoading, refetch } = useSchedulerJobs();

  return (
    <div>
      <Header title="Zamanlayıcı" subtitle="Zamanlanmış görevleri görüntüleyin ve yönetin" />

      <div className="p-6">
        {/* Info Card */}
        <div className="card p-4 mb-6 bg-primary-50 border-primary-200">
          <div className="flex items-start gap-3">
            <Calendar className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-primary-700">Zamanlanmış Görevler</p>
              <p className="text-sm text-primary-600 mt-1">
                Sistem, arka planda çeşitli görevleri otomatik olarak çalıştırır: sağlık kontrolleri,
                eski dosyaların temizliği ve günlük raporlar.
              </p>
            </div>
          </div>
        </div>

        {/* Jobs List */}
        <div className="card">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Görevler</h2>
            <button onClick={() => refetch()} className="btn btn-secondary text-sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Yenile
            </button>
          </div>

          {isLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto" />
              <p className="mt-4 text-gray-500">Yükleniyor...</p>
            </div>
          ) : data?.jobs && data.jobs.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {data.jobs.map((job) => (
                <div key={job.id} className="p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{job.name || job.id}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                          {job.trigger}
                        </span>
                      </p>
                    </div>
                    <div className="text-right">
                      {job.next_run ? (
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Clock className="w-4 h-4" />
                          <span>Sonraki: {formatDate(job.next_run)}</span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">Zamanlama yok</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-gray-500">Zamanlanmış görev bulunamadı</div>
          )}
        </div>

        {/* Default Jobs Info */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <Play className="w-4 h-4 text-green-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Sağlık Kontrolü</p>
                <p className="text-xs text-gray-500">Her 5 dakikada</p>
              </div>
            </div>
          </div>

          <div className="card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <RefreshCw className="w-4 h-4 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Screenshot Temizliği</p>
                <p className="text-xs text-gray-500">Her gün 03:00</p>
              </div>
            </div>
          </div>

          <div className="card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <RefreshCw className="w-4 h-4 text-purple-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Log Temizliği</p>
                <p className="text-xs text-gray-500">Her Pazar 04:00</p>
              </div>
            </div>
          </div>

          <div className="card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-50 rounded-lg">
                <Calendar className="w-4 h-4 text-orange-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Günlük Rapor</p>
                <p className="text-xs text-gray-500">Her gün 18:00</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
