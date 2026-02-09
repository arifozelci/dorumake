'use client';

import { cn } from '@/lib/utils';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';
import Link from 'next/link';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'primary' | 'success' | 'warning' | 'danger';
  loading?: boolean;
  href?: string;
}

const colorConfig = {
  primary: {
    bg: 'bg-primary-50',
    icon: 'text-primary-600',
    iconBg: 'bg-primary-100',
    gradient: 'from-primary-500/10 to-primary-600/5',
    border: 'border-primary-100',
  },
  success: {
    bg: 'bg-success-50',
    icon: 'text-success-600',
    iconBg: 'bg-success-100',
    gradient: 'from-success-500/10 to-success-600/5',
    border: 'border-success-100',
  },
  warning: {
    bg: 'bg-warning-50',
    icon: 'text-warning-600',
    iconBg: 'bg-warning-100',
    gradient: 'from-warning-500/10 to-warning-600/5',
    border: 'border-warning-100',
  },
  danger: {
    bg: 'bg-danger-50',
    icon: 'text-danger-600',
    iconBg: 'bg-danger-100',
    gradient: 'from-danger-500/10 to-danger-600/5',
    border: 'border-danger-100',
  },
};

export function StatsCard({ title, value, icon: Icon, trend, color = 'primary', loading = false, href }: StatsCardProps) {
  const config = colorConfig[color];

  const cardContent = (
    <>
      {/* Background gradient */}
      <div className={cn(
        'absolute inset-0 bg-gradient-to-br opacity-50',
        config.gradient
      )} />

      {/* Content */}
      <div className="relative">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
            {loading ? (
              <div className="h-9 w-20 skeleton rounded-lg" />
            ) : (
              <p className="text-3xl font-bold text-gray-900 tracking-tight">{value}</p>
            )}
            {trend && !loading && (
              <div className={cn(
                'flex items-center gap-1 mt-2 text-sm font-medium',
                trend.isPositive ? 'text-success-600' : 'text-danger-600'
              )}>
                {trend.isPositive ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
                <span>{trend.isPositive ? '+' : ''}{trend.value}%</span>
                <span className="text-gray-400 font-normal">vs onceki</span>
              </div>
            )}
          </div>

          {/* Icon */}
          <div className={cn(
            'p-3 rounded-xl transition-transform duration-300',
            'group-hover:scale-110',
            config.iconBg
          )}>
            <Icon className={cn('w-6 h-6', config.icon)} />
          </div>
        </div>
      </div>

      {/* Decorative element */}
      <div className={cn(
        'absolute -bottom-4 -right-4 w-24 h-24 rounded-full opacity-10',
        config.bg
      )} />
    </>
  );

  const cardClassName = cn(
    'relative overflow-hidden rounded-2xl border bg-white p-6',
    'transition-all duration-300 ease-out',
    'hover:shadow-lg hover:scale-[1.02]',
    'group',
    config.border,
    href && 'cursor-pointer'
  );

  if (href) {
    return (
      <Link href={href} className={cn(cardClassName, 'block')}>
        {cardContent}
      </Link>
    );
  }

  return (
    <div className={cardClassName}>
      {cardContent}
    </div>
  );
}

// Mini stat card variant
export function MiniStatsCard({
  title,
  value,
  icon: Icon,
  color = 'primary',
  loading = false,
  href
}: Omit<StatsCardProps, 'trend'>) {
  const config = colorConfig[color];

  const cardContent = (
    <>
      <div className={cn('p-2.5 rounded-lg', config.iconBg)}>
        <Icon className={cn('w-5 h-5', config.icon)} />
      </div>
      <div>
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{title}</p>
        {loading ? (
          <div className="h-6 w-12 skeleton rounded mt-0.5" />
        ) : (
          <p className="text-xl font-bold text-gray-900">{value}</p>
        )}
      </div>
    </>
  );

  const cardClassName = cn(
    'flex items-center gap-4 p-4 rounded-xl border bg-white',
    'transition-all duration-200 hover:shadow-md',
    config.border,
    href && 'cursor-pointer'
  );

  if (href) {
    return (
      <Link href={href} className={cardClassName}>
        {cardContent}
      </Link>
    );
  }

  return (
    <div className={cardClassName}>
      {cardContent}
    </div>
  );
}
