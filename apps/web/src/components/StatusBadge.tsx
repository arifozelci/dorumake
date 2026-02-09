'use client';

import { cn } from '@/lib/utils';
import { Clock, Loader2, CheckCircle, XCircle, ListOrdered } from 'lucide-react';
import { LucideIcon } from 'lucide-react';

type Status = 'pending' | 'processing' | 'completed' | 'failed' | 'queued' | 'cancelled' | 'processed' | 'ignored';

interface StatusBadgeProps {
  status: string;
  showIcon?: boolean;
  size?: 'sm' | 'md';
}

const statusConfig: Record<Status, { label: string; className: string; icon: LucideIcon; iconClass?: string }> = {
  pending: {
    label: 'Bekliyor',
    className: 'bg-warning-100 text-warning-700 border-warning-200',
    icon: Clock,
  },
  processing: {
    label: 'İşleniyor',
    className: 'bg-primary-100 text-primary-700 border-primary-200',
    icon: Loader2,
    iconClass: 'animate-spin',
  },
  completed: {
    label: 'Tamamlandı',
    className: 'bg-success-100 text-success-700 border-success-200',
    icon: CheckCircle,
  },
  failed: {
    label: 'Başarısız',
    className: 'bg-danger-100 text-danger-700 border-danger-200',
    icon: XCircle,
  },
  queued: {
    label: 'Sırada',
    className: 'bg-gray-100 text-gray-700 border-gray-200',
    icon: ListOrdered,
  },
  cancelled: {
    label: 'İptal Edildi',
    className: 'bg-gray-100 text-gray-700 border-gray-200',
    icon: XCircle,
  },
  processed: {
    label: 'İşlendi',
    className: 'bg-success-100 text-success-700 border-success-200',
    icon: CheckCircle,
  },
  ignored: {
    label: 'Göz Ardı Edildi',
    className: 'bg-gray-100 text-gray-500 border-gray-200',
    icon: Clock,
  },
};

export function StatusBadge({ status, showIcon = true, size = 'md' }: StatusBadgeProps) {
  const config = statusConfig[status.toLowerCase() as Status] || {
    label: status,
    className: 'bg-gray-100 text-gray-700 border-gray-200',
    icon: Clock,
  };

  const Icon = config.icon;

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 rounded-full border font-medium',
      config.className,
      size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
    )}>
      {showIcon && (
        <Icon className={cn(
          size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5',
          config.iconClass
        )} />
      )}
      {config.label}
    </span>
  );
}
