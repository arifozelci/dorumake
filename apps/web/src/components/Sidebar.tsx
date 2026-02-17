'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  ShoppingCart,
  Mail,
  FileText,
  Settings,
  Calendar,
  Building2,
  LogOut,
  Users,
  FileEdit,
  Activity,
  ChevronRight,
  Bell,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { authService } from '@/lib/auth';
import { useTranslation } from '@/contexts/LanguageContext';
import { LanguageSwitcher } from './LanguageSwitcher';

interface NavItem {
  key: string;
  href: string;
  icon: React.ElementType;
}

const mainNavItems: NavItem[] = [
  { key: 'nav.dashboard', href: '/dashboard', icon: LayoutDashboard },
  { key: 'nav.orders', href: '/dashboard/orders', icon: ShoppingCart },
  { key: 'nav.emails', href: '/dashboard/emails', icon: Mail },
  { key: 'nav.logs', href: '/dashboard/logs', icon: FileText },
  { key: 'nav.reports', href: '/dashboard/reports', icon: BarChart3 },
];

const managementNavItems: NavItem[] = [
  { key: 'nav.suppliers', href: '/dashboard/suppliers', icon: Building2 },
  { key: 'nav.users', href: '/dashboard/users', icon: Users },
  { key: 'nav.templates', href: '/dashboard/templates', icon: FileEdit },
];

const systemNavItems: NavItem[] = [
  { key: 'nav.notifications', href: '/dashboard/notifications', icon: Bell },
  { key: 'nav.scheduler', href: '/dashboard/scheduler', icon: Calendar },
  { key: 'nav.settings', href: '/dashboard/settings', icon: Settings },
];

interface NavSectionProps {
  title?: string;
  items: NavItem[];
  pathname: string;
  t: (key: string) => string;
  onLinkClick?: () => void;
}

function NavSection({ title, items, pathname, t, onLinkClick }: NavSectionProps) {
  return (
    <div className="mb-6">
      {title && (
        <p className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
          {title}
        </p>
      )}
      <div className="space-y-1">
        {items.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.key}
              href={item.href}
              onClick={onLinkClick}
              className={cn(
                'group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium',
                'transition-all duration-200 ease-out',
                isActive
                  ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-md shadow-primary-500/25'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )}
            >
              <item.icon className={cn(
                'w-5 h-5 transition-transform duration-200',
                isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-600',
                'group-hover:scale-110'
              )} />
              <span className="flex-1">{t(item.key)}</span>
              {isActive && (
                <ChevronRight className="w-4 h-4 text-white/70" />
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

interface SidebarProps {
  onClose?: () => void;
}

export function Sidebar({ onClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { t } = useTranslation();

  const handleLogout = () => {
    authService.logout();
    router.push('/login');
  };

  return (
    <aside className="w-64 bg-white border-r border-gray-100 min-h-screen flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-100">
        <Link href="/dashboard" onClick={onClose} className="flex items-center gap-3 group">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30 transition-transform duration-200 group-hover:scale-105">
            <span className="text-white font-bold text-xl">K</span>
          </div>
          <div>
            <span className="font-bold text-lg text-gray-900 block leading-tight">KolayRobot</span>
            <span className="text-xs text-gray-400">{t('sidebar.orderAutomation')}</span>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-y-auto">
        <NavSection items={mainNavItems} pathname={pathname} t={t} onLinkClick={onClose} />
        <NavSection title={t('nav.management')} items={managementNavItems} pathname={pathname} t={t} onLinkClick={onClose} />
        <NavSection title={t('nav.system')} items={systemNavItems} pathname={pathname} t={t} onLinkClick={onClose} />
      </nav>

      {/* Status, Language & Logout */}
      <div className="p-4 border-t border-gray-100 space-y-3">
        {/* System Status */}
        <div className="flex items-center gap-3 px-3 py-2.5 bg-success-50 rounded-xl">
          <div className="relative">
            <Activity className="w-5 h-5 text-success-600" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-success-500 rounded-full animate-pulse" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-success-700">{t('sidebar.systemActive')}</p>
            <p className="text-xs text-success-600">{t('sidebar.allServicesRunning')}</p>
          </div>
        </div>

        {/* Language Switcher */}
        <LanguageSwitcher />

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className={cn(
            'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium w-full',
            'text-gray-600 hover:bg-danger-50 hover:text-danger-600',
            'transition-all duration-200 group'
          )}
        >
          <LogOut className="w-5 h-5 text-gray-400 group-hover:text-danger-500 transition-colors" />
          <span>{t('nav.logout')}</span>
        </button>
      </div>
    </aside>
  );
}
