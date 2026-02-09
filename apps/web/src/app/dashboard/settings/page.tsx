'use client';

import { Header } from '@/components';
import { useHealth } from '@/hooks/useApi';
import { Settings as SettingsIcon, Database, Mail, Server, Shield, Clock } from 'lucide-react';

export default function SettingsPage() {
  const { data: health } = useHealth();

  return (
    <div>
      <Header title="Ayarlar" subtitle="Sistem ayarlarını görüntüleyin" />

      <div className="p-6">
        {/* System Info */}
        <div className="card mb-6">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <Server className="w-5 h-5 text-gray-400" />
              Sistem Bilgileri
            </h2>
          </div>
          <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Versiyon</p>
              <p className="font-medium text-gray-900">{health?.version || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Durum</p>
              <p className="font-medium text-gray-900 capitalize">{health?.status || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Son Güncelleme</p>
              <p className="font-medium text-gray-900">
                {health?.timestamp ? new Date(health.timestamp).toLocaleString('tr-TR') : '-'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Ortam</p>
              <p className="font-medium text-gray-900">Production</p>
            </div>
          </div>
        </div>

        {/* Services Status */}
        <div className="card mb-6">
          <div className="p-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <SettingsIcon className="w-5 h-5 text-gray-400" />
              Servis Durumları
            </h2>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {health?.services &&
                Object.entries(health.services).map(([service, status]) => (
                  <div key={service} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {service.replace('_', ' ')}
                      </span>
                      <span
                        className={`w-2 h-2 rounded-full ${
                          status === 'running' ? 'bg-green-500' : 'bg-red-500'
                        }`}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1 capitalize">{status}</p>
                  </div>
                ))}
            </div>
          </div>
        </div>

        {/* Configuration Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Email Configuration */}
          <div className="card">
            <div className="p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <Mail className="w-5 h-5 text-gray-400" />
                E-posta Yapılandırması
              </h2>
            </div>
            <div className="p-4 space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">IMAP Sunucu</span>
                <span className="text-sm text-gray-900">imap.gmail.com</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Port</span>
                <span className="text-sm text-gray-900">993</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">SSL</span>
                <span className="text-sm text-gray-900">Aktif</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Polling Aralığı</span>
                <span className="text-sm text-gray-900">1 dakika</span>
              </div>
            </div>
          </div>

          {/* Database Configuration */}
          <div className="card">
            <div className="p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <Database className="w-5 h-5 text-gray-400" />
                Veritabanı Yapılandırması
              </h2>
            </div>
            <div className="p-4 space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Veritabanı</span>
                <span className="text-sm text-gray-900">MySQL</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Host</span>
                <span className="text-sm text-gray-900">localhost</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Port</span>
                <span className="text-sm text-gray-900">3306</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Veritabanı Adı</span>
                <span className="text-sm text-gray-900">kolayrobot</span>
              </div>
            </div>
          </div>

          {/* Retry Configuration */}
          <div className="card">
            <div className="p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-gray-400" />
                Yeniden Deneme Ayarları
              </h2>
            </div>
            <div className="p-4 space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Maksimum Deneme</span>
                <span className="text-sm text-gray-900">3</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">İlk Bekleme</span>
                <span className="text-sm text-gray-900">1 saniye</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Maksimum Bekleme</span>
                <span className="text-sm text-gray-900">60 saniye</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Exponential Backoff</span>
                <span className="text-sm text-gray-900">Aktif</span>
              </div>
            </div>
          </div>

          {/* Security */}
          <div className="card">
            <div className="p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <Shield className="w-5 h-5 text-gray-400" />
                Güvenlik
              </h2>
            </div>
            <div className="p-4 space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Headless Modu</span>
                <span className="text-sm text-gray-900">Aktif</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Screenshot Saklama</span>
                <span className="text-sm text-gray-900">7 gün</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Log Saklama</span>
                <span className="text-sm text-gray-900">30 gün</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Debug Modu</span>
                <span className="text-sm text-gray-900">Kapalı</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
