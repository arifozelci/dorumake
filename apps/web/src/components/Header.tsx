'use client';

import { Bell, RefreshCw, User, ChevronDown, LogOut, Settings, UserCircle, X, CheckCircle, AlertTriangle, Info } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import { useRecentNotifications } from '@/hooks/useApi';

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function Header({ title, subtitle, actions }: HeaderProps) {
  const [refreshing, setRefreshing] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const notificationRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { user, logout } = useAuth();
  const { data: notifData } = useRecentNotifications();
  const notifications = notifData?.notifications ?? [];

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    window.location.reload();
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle className="w-4 h-4 text-success-500" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-warning-500" />;
      default: return <Info className="w-4 h-4 text-primary-500" />;
    }
  };

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-gray-100">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Title Section */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">{title}</h1>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>
          )}
        </div>

        {/* Actions Section */}
        <div className="flex items-center gap-2">
          {actions}

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            className={cn(
              'p-2.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl',
              'transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-primary-500/20'
            )}
            title="Yenile"
          >
            <RefreshCw className={cn('w-5 h-5', refreshing && 'animate-spin')} />
          </button>

          {/* Notifications */}
          <div className="relative" ref={notificationRef}>
            <button
              onClick={() => {
                setShowNotifications(!showNotifications);
                setShowUserMenu(false);
              }}
              className={cn(
                'relative p-2.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl',
                'transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-primary-500/20',
                showNotifications && 'bg-gray-100 text-gray-600'
              )}
              title="Bildirimler"
            >
              <Bell className="w-5 h-5" />
              {notifications.length > 0 && (
                <span className="absolute top-2 right-2 w-2 h-2 bg-danger-500 rounded-full ring-2 ring-white" />
              )}
            </button>

            {/* Notifications Dropdown */}
            {showNotifications && (
              <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden z-[100]">
                <div className="flex items-center justify-between p-4 border-b border-gray-100">
                  <h3 className="font-semibold text-gray-900">Bildirimler</h3>
                  <button
                    onClick={() => setShowNotifications(false)}
                    className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {notifications.length > 0 ? (
                    notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className="p-4 border-b border-gray-50 hover:bg-gray-50 transition-colors cursor-pointer"
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5">
                            {getNotificationIcon(notification.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                            <p className="text-sm text-gray-500 mt-0.5">{notification.message}</p>
                            <p className="text-xs text-gray-400 mt-1">{notification.time}</p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-8 text-center text-gray-500">
                      Bildirim yok
                    </div>
                  )}
                </div>
                <div className="p-3 border-t border-gray-100 bg-gray-50">
                  <button
                    onClick={() => {
                      setShowNotifications(false);
                      router.push('/dashboard/notifications');
                    }}
                    className="w-full text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Tüm bildirimleri gör
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Divider */}
          <div className="w-px h-8 bg-gray-200 mx-2" />

          {/* User Menu */}
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => {
                setShowUserMenu(!showUserMenu);
                setShowNotifications(false);
              }}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-xl',
                'hover:bg-gray-100 transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-primary-500/20',
                showUserMenu && 'bg-gray-100'
              )}
            >
              <div className="w-9 h-9 bg-gradient-to-br from-primary-400 to-primary-600 rounded-xl flex items-center justify-center shadow-sm">
                <User className="w-5 h-5 text-white" />
              </div>
              <div className="text-left hidden sm:block">
                <p className="text-sm font-semibold text-gray-900">{user?.username || 'Admin'}</p>
                <p className="text-xs text-gray-500">Yönetici</p>
              </div>
              <ChevronDown className={cn(
                'w-4 h-4 text-gray-400 hidden sm:block transition-transform',
                showUserMenu && 'rotate-180'
              )} />
            </button>

            {/* User Dropdown */}
            {showUserMenu && (
              <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden z-[100]">
                <div className="p-4 border-b border-gray-100">
                  <p className="text-sm font-semibold text-gray-900">{user?.username || 'Admin'}</p>
                  <p className="text-xs text-gray-500">{user?.email || 'admin@dorufinansal.com'}</p>
                </div>
                <div className="p-2">
                  <button
                    onClick={() => {
                      setShowUserMenu(false);
                      router.push('/dashboard/settings');
                    }}
                    className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <Settings className="w-4 h-4" />
                    Ayarlar
                  </button>
                  <button
                    onClick={() => {
                      setShowUserMenu(false);
                      router.push('/dashboard/users');
                    }}
                    className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <UserCircle className="w-4 h-4" />
                    Kullanıcılar
                  </button>
                </div>
                <div className="p-2 border-t border-gray-100">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-3 py-2 text-sm text-danger-600 hover:bg-danger-50 rounded-lg transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Çıkış Yap
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
