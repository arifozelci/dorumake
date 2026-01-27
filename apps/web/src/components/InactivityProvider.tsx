'use client';

import { useState, useCallback } from 'react';
import { useInactivityTimeout } from '@/hooks/useInactivityTimeout';
import { AlertTriangle, Clock, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface InactivityProviderProps {
  children: React.ReactNode;
  timeoutMinutes?: number;
  warningMinutes?: number;
}

export function InactivityProvider({
  children,
  timeoutMinutes = 30,
  warningMinutes = 5,
}: InactivityProviderProps) {
  const [showWarning, setShowWarning] = useState(false);

  const handleWarning = useCallback(() => {
    setShowWarning(true);
  }, []);

  const handleTimeout = useCallback(() => {
    setShowWarning(false);
  }, []);

  const { extendSession } = useInactivityTimeout({
    timeoutMinutes,
    warningMinutes,
    onWarning: handleWarning,
    onTimeout: handleTimeout,
  });

  const handleExtend = () => {
    setShowWarning(false);
    extendSession();
  };

  const handleDismiss = () => {
    setShowWarning(false);
  };

  return (
    <>
      {children}

      {/* Inactivity Warning Modal */}
      {showWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden animate-slide-up">
            {/* Header */}
            <div className="bg-warning-50 px-6 py-4 border-b border-warning-100">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-warning-100 rounded-xl">
                  <AlertTriangle className="w-6 h-6 text-warning-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-warning-800">Oturum Zaman Asimi</h3>
                  <p className="text-sm text-warning-600">Inaktiflik tespit edildi</p>
                </div>
                <button
                  onClick={handleDismiss}
                  className="ml-auto p-1 text-warning-400 hover:text-warning-600 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="px-6 py-5">
              <div className="flex items-center gap-3 mb-4">
                <Clock className="w-5 h-5 text-gray-400" />
                <p className="text-gray-600">
                  <span className="font-semibold text-warning-600">{warningMinutes} dakika</span> icinde
                  aktivite olmazsa oturumunuz sonlandirilacak.
                </p>
              </div>
              <p className="text-sm text-gray-500">
                Guvenliginiz icin uzun sure islem yapilmayan oturumlar otomatik olarak kapatilir.
              </p>
            </div>

            {/* Actions */}
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex gap-3">
              <button
                onClick={handleExtend}
                className={cn(
                  'flex-1 flex items-center justify-center gap-2 px-4 py-2.5',
                  'bg-gradient-to-r from-primary-600 to-primary-500 text-white',
                  'rounded-xl font-medium',
                  'hover:from-primary-700 hover:to-primary-600',
                  'transition-all duration-200',
                  'shadow-sm hover:shadow-md'
                )}
              >
                Oturumu Uzat
              </button>
              <button
                onClick={handleDismiss}
                className={cn(
                  'px-4 py-2.5 text-gray-600 font-medium rounded-xl',
                  'hover:bg-gray-100 transition-all duration-200'
                )}
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
