'use client';

import { cn } from '@/lib/utils';

type Status = 'pending' | 'processing' | 'completed' | 'failed' | 'queued';

interface StatusBadgeProps {
  status: string;
}

const statusConfig: Record<Status, { label: string; className: string }> = {
  pending: { label: 'Bekliyor', className: 'badge-warning' },
  processing: { label: 'İşleniyor', className: 'badge-primary' },
  completed: { label: 'Tamamlandı', className: 'badge-success' },
  failed: { label: 'Başarısız', className: 'badge-danger' },
  queued: { label: 'Sırada', className: 'badge-primary' },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status.toLowerCase() as Status] || {
    label: status,
    className: 'badge-primary',
  };

  return <span className={cn('badge', config.className)}>{config.label}</span>;
}
