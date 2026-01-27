'use client';

import { useState } from 'react';
import { Header } from '@/components';
import { formatDate, cn } from '@/lib/utils';
import {
  Bell,
  CheckCircle,
  AlertTriangle,
  Info,
  XCircle,
  Trash2,
  CheckCheck,
  Filter
} from 'lucide-react';

interface Notification {
  id: number;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// Sample notifications - will be replaced with API data
const sampleNotifications: Notification[] = [
  {
    id: 1,
    type: 'success',
    title: 'Sipariş tamamlandı',
    message: 'ORD-2026-00001 başarıyla Mutlu Akü portalına girildi.',
    timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    read: false,
  },
  {
    id: 2,
    type: 'warning',
    title: 'Kuyruk uyarısı',
    message: 'Mutlu Akü kuyruğunda 3 sipariş bekliyor. İşlem süresi normalin üzerinde.',
    timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    read: false,
  },
  {
    id: 3,
    type: 'info',
    title: 'Yeni e-posta',
    message: 'Caspar\'dan yeni sipariş e-postası alındı. Sipariş kuyruğa eklendi.',
    timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    read: true,
  },
  {
    id: 4,
    type: 'error',
    title: 'Sipariş hatası',
    message: 'ORD-2026-00003 işlenirken hata oluştu: SAP onay butonu bulunamadı.',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    read: true,
  },
  {
    id: 5,
    type: 'success',
    title: 'Sipariş tamamlandı',
    message: 'ORD-2026-00002 başarıyla Mann & Hummel portalına girildi.',
    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    read: true,
  },
  {
    id: 6,
    type: 'info',
    title: 'Sistem başlatıldı',
    message: 'DoruMake sistemi başarıyla başlatıldı. Tüm servisler aktif.',
    timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    read: true,
  },
];

const typeConfig = {
  success: {
    icon: CheckCircle,
    color: 'text-success-600',
    bg: 'bg-success-50',
    border: 'border-l-success-500'
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-warning-600',
    bg: 'bg-warning-50',
    border: 'border-l-warning-500'
  },
  error: {
    icon: XCircle,
    color: 'text-danger-600',
    bg: 'bg-danger-50',
    border: 'border-l-danger-500'
  },
  info: {
    icon: Info,
    color: 'text-primary-600',
    bg: 'bg-primary-50',
    border: 'border-l-primary-500'
  },
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>(sampleNotifications);
  const [filter, setFilter] = useState<string>('all');

  const unreadCount = notifications.filter(n => !n.read).length;

  const filteredNotifications = notifications.filter(n => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !n.read;
    return n.type === filter;
  });

  const markAsRead = (id: number) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const deleteNotification = (id: number) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const NotificationItem = ({ notification }: { notification: Notification }) => {
    const config = typeConfig[notification.type];
    const Icon = config.icon;

    return (
      <div
        className={cn(
          'p-4 border-l-4 transition-all hover:shadow-sm',
          config.border,
          notification.read ? 'bg-white' : 'bg-gray-50'
        )}
      >
        <div className="flex items-start gap-4">
          <div className={cn('p-2 rounded-lg', config.bg)}>
            <Icon className={cn('w-5 h-5', config.color)} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className={cn(
                  'text-sm font-medium text-gray-900',
                  !notification.read && 'font-semibold'
                )}>
                  {notification.title}
                </h3>
                <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                <p className="text-xs text-gray-400 mt-2">{formatDate(notification.timestamp)}</p>
              </div>
              <div className="flex items-center gap-1">
                {!notification.read && (
                  <button
                    onClick={() => markAsRead(notification.id)}
                    className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                    title="Okundu olarak işaretle"
                  >
                    <CheckCheck className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => deleteNotification(notification.id)}
                  className="p-1.5 text-gray-400 hover:text-danger-600 hover:bg-danger-50 rounded-lg transition-colors"
                  title="Sil"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div>
      <Header
        title="Bildirimler"
        subtitle="Sistem bildirimlerini görüntüleyin"
        actions={
          <div className="flex items-center gap-2">
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="btn btn-secondary text-sm"
              >
                <CheckCheck className="w-4 h-4 mr-2" />
                Tümünü Okundu İşaretle
              </button>
            )}
            {notifications.length > 0 && (
              <button
                onClick={clearAll}
                className="btn btn-secondary text-sm text-danger-600 hover:bg-danger-50"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Tümünü Sil
              </button>
            )}
          </div>
        }
      />

      <div className="p-6">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={cn(
              'card p-4 text-left transition-all',
              filter === 'all' && 'ring-2 ring-primary-500'
            )}
          >
            <p className="text-sm text-gray-500">Toplam</p>
            <p className="text-2xl font-semibold text-gray-900">{notifications.length}</p>
          </button>
          <button
            onClick={() => setFilter('unread')}
            className={cn(
              'card p-4 text-left transition-all',
              filter === 'unread' && 'ring-2 ring-primary-500'
            )}
          >
            <p className="text-sm text-gray-500">Okunmamış</p>
            <p className="text-2xl font-semibold text-primary-600">{unreadCount}</p>
          </button>
          <button
            onClick={() => setFilter('error')}
            className={cn(
              'card p-4 text-left transition-all',
              filter === 'error' && 'ring-2 ring-danger-500'
            )}
          >
            <p className="text-sm text-gray-500">Hatalar</p>
            <p className="text-2xl font-semibold text-danger-600">
              {notifications.filter(n => n.type === 'error').length}
            </p>
          </button>
          <button
            onClick={() => setFilter('warning')}
            className={cn(
              'card p-4 text-left transition-all',
              filter === 'warning' && 'ring-2 ring-warning-500'
            )}
          >
            <p className="text-sm text-gray-500">Uyarılar</p>
            <p className="text-2xl font-semibold text-warning-600">
              {notifications.filter(n => n.type === 'warning').length}
            </p>
          </button>
          <button
            onClick={() => setFilter('success')}
            className={cn(
              'card p-4 text-left transition-all',
              filter === 'success' && 'ring-2 ring-success-500'
            )}
          >
            <p className="text-sm text-gray-500">Başarılı</p>
            <p className="text-2xl font-semibold text-success-600">
              {notifications.filter(n => n.type === 'success').length}
            </p>
          </button>
        </div>

        {/* Notifications List */}
        <div className="card overflow-hidden">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-gray-400" />
              <h2 className="font-semibold text-gray-900">
                {filter === 'all' && 'Tüm Bildirimler'}
                {filter === 'unread' && 'Okunmamış Bildirimler'}
                {filter === 'error' && 'Hata Bildirimleri'}
                {filter === 'warning' && 'Uyarı Bildirimleri'}
                {filter === 'success' && 'Başarı Bildirimleri'}
                {filter === 'info' && 'Bilgi Bildirimleri'}
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="input text-sm py-1.5 w-40"
              >
                <option value="all">Tümü</option>
                <option value="unread">Okunmamış</option>
                <option value="error">Hatalar</option>
                <option value="warning">Uyarılar</option>
                <option value="success">Başarılı</option>
                <option value="info">Bilgi</option>
              </select>
            </div>
          </div>

          {filteredNotifications.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {filteredNotifications.map(notification => (
                <NotificationItem key={notification.id} notification={notification} />
              ))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <Bell className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Bildirim bulunamadı</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
