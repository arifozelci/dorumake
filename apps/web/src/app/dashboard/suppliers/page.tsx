'use client';

import { Header } from '@/components';
import { useSuppliers } from '@/hooks/useApi';
import { ExternalLink, CheckCircle, XCircle } from 'lucide-react';

export default function SuppliersPage() {
  const { data, isLoading } = useSuppliers();

  return (
    <div>
      <Header title="Tedarikçiler" subtitle="Yapılandırılmış tedarikçi portallarını görüntüleyin" />

      <div className="p-6">
        {isLoading ? (
          <div className="card p-8 text-center">
            <div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full mx-auto" />
            <p className="mt-4 text-gray-500">Yükleniyor...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {data?.suppliers.map((supplier) => (
              <div key={supplier.code} className="card">
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{supplier.name}</h3>
                      <p className="text-sm text-gray-500 mt-1">Kod: {supplier.code}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {supplier.active ? (
                        <span className="flex items-center gap-1 text-success-600 text-sm">
                          <CheckCircle className="w-4 h-4" />
                          Aktif
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-danger-600 text-sm">
                          <XCircle className="w-4 h-4" />
                          Pasif
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 space-y-3">
                    <div>
                      <p className="text-sm text-gray-500">Portal URL</p>
                      <a
                        href={supplier.portal_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary-600 hover:underline flex items-center gap-1 min-w-0"
                        title={supplier.portal_url}
                      >
                        <span className="truncate">{supplier.portal_url}</span>
                        <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      </a>
                    </div>

                    {supplier.code === 'MUTLU' && (
                      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                        <p className="text-sm font-medium text-gray-700">Sipariş Süreci</p>
                        <ul className="mt-2 text-xs text-gray-600 space-y-1">
                          <li>1. Portal girişi</li>
                          <li>2. Müşteri seçimi</li>
                          <li>3. Sipariş formu doldurma</li>
                          <li>4. Ürün ekleme</li>
                          <li>5. SAP onayı</li>
                        </ul>
                      </div>
                    )}

                    {supplier.code === 'MANN' && (
                      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                        <p className="text-sm font-medium text-gray-700">Sipariş Süreci</p>
                        <ul className="mt-2 text-xs text-gray-600 space-y-1">
                          <li>1. TecCom portalına giriş</li>
                          <li>2. CSV dosyası yükleme</li>
                          <li>3. Tedarikçi ve müşteri seçimi</li>
                          <li>4. Sipariş oluşturma</li>
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
