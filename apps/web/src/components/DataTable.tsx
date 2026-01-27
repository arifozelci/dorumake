'use client';

import { ChevronLeft, ChevronRight, Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
  emptyMessage?: string;
}

function SkeletonRow({ columns }: { columns: number }) {
  return (
    <tr className="animate-pulse">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-4">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
        </td>
      ))}
    </tr>
  );
}

export function DataTable<T extends { id: string }>({
  columns,
  data,
  page,
  pageSize,
  total,
  onPageChange,
  isLoading = false,
  emptyMessage = 'Veri bulunamadı',
}: DataTableProps<T>) {
  const totalPages = Math.ceil(total / pageSize);

  if (isLoading) {
    return (
      <div className="overflow-hidden rounded-xl border border-gray-200/80 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50/80">
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className="px-4 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider"
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonRow key={i} columns={columns.length} />
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="overflow-hidden rounded-xl border border-gray-200/80 bg-white">
        <div className="flex flex-col items-center justify-center py-12 px-4">
          <div className="p-4 bg-gray-100 rounded-full mb-4">
            <Inbox className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-500 font-medium">{emptyMessage}</p>
          <p className="text-gray-400 text-sm mt-1">Henüz kayıt bulunmuyor</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-xl border border-gray-200/80 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50/80">
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={cn(
                    'px-4 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider',
                    column.className
                  )}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((item) => (
              <tr
                key={item.id}
                className="transition-colors duration-150 hover:bg-gray-50/50"
              >
                {columns.map((column) => (
                  <td
                    key={`${item.id}-${String(column.key)}`}
                    className={cn('px-4 py-4', column.className)}
                  >
                    {column.render
                      ? column.render(item)
                      : String(item[column.key as keyof T] ?? '-')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Toplam <span className="font-medium text-gray-700">{total}</span> kayit,
            sayfa <span className="font-medium text-gray-700">{page}</span> / {totalPages}
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className={cn(
                'flex items-center justify-center w-9 h-9 rounded-lg border',
                'transition-all duration-200',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                page <= 1
                  ? 'border-gray-200 text-gray-300'
                  : 'border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300'
              )}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            {/* Page numbers */}
            {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
              const pageNum = i + 1;
              return (
                <button
                  key={pageNum}
                  onClick={() => onPageChange(pageNum)}
                  className={cn(
                    'flex items-center justify-center w-9 h-9 rounded-lg text-sm font-medium',
                    'transition-all duration-200',
                    pageNum === page
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  )}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className={cn(
                'flex items-center justify-center w-9 h-9 rounded-lg border',
                'transition-all duration-200',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                page >= totalPages
                  ? 'border-gray-200 text-gray-300'
                  : 'border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300'
              )}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
