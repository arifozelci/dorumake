'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  ShoppingCart,
  Mail,
  FileText,
  Settings,
  Calendar,
  Building2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Siparişler', href: '/orders', icon: ShoppingCart },
  { name: 'E-postalar', href: '/emails', icon: Mail },
  { name: 'Loglar', href: '/logs', icon: FileText },
  { name: 'Tedarikçiler', href: '/suppliers', icon: Building2 },
  { name: 'Zamanlayıcı', href: '/scheduler', icon: Calendar },
  { name: 'Ayarlar', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-200">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">D</span>
          </div>
          <span className="font-bold text-xl text-gray-900">DoruMake</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <item.icon className={cn('w-5 h-5', isActive ? 'text-primary-600' : 'text-gray-400')} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Status */}
      <div className="absolute bottom-0 w-64 p-4 border-t border-gray-200">
        <div className="flex items-center gap-2 text-sm">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-gray-600">Sistem Aktif</span>
        </div>
      </div>
    </aside>
  );
}
