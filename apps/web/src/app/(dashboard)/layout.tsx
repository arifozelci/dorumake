'use client';

import { Sidebar } from '@/components/Sidebar';
import { AuthGuard } from '@/components/AuthGuard';
import { InactivityProvider } from '@/components/InactivityProvider';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <InactivityProvider timeoutMinutes={30} warningMinutes={5}>
        <div className="flex min-h-screen bg-gray-50">
          <Sidebar />
          <main className="flex-1">{children}</main>
        </div>
      </InactivityProvider>
    </AuthGuard>
  );
}
