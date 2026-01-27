'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LogIn, AlertCircle, Loader2, Mail, ArrowLeft, CheckCircle, Lock, User, Zap } from 'lucide-react';
import { authService } from '@/lib/auth';
import { cn } from '@/lib/utils';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Forgot password states
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotSuccess, setForgotSuccess] = useState(false);
  const [forgotError, setForgotError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.login({ username, password });
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Giriş başarısız');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotError('');
    setForgotLoading(true);

    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'İşlem başarısız');
      }

      setForgotSuccess(true);
    } catch (err) {
      setForgotError(err instanceof Error ? err.message : 'İşlem başarısız');
    } finally {
      setForgotLoading(false);
    }
  };

  const resetForgotPassword = () => {
    setShowForgotPassword(false);
    setForgotEmail('');
    setForgotSuccess(false);
    setForgotError('');
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 via-primary-500 to-primary-700 relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-96 h-96 bg-white/10 rounded-full -translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 right-0 w-80 h-80 bg-white/10 rounded-full translate-x-1/3 translate-y-1/3" />
        <div className="absolute top-1/2 left-1/4 w-64 h-64 bg-white/5 rounded-full" />

        <div className="relative z-10 flex flex-col justify-center px-12 lg:px-16">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center">
              <Zap className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">DoruMake</h1>
              <p className="text-primary-100">Sipariş Otomasyon Sistemi</p>
            </div>
          </div>

          <h2 className="text-4xl font-bold text-white mb-4 leading-tight">
            Siparişlerinizi<br />
            Otomatik Yönetin
          </h2>
          <p className="text-primary-100 text-lg max-w-md">
            Tedarikçi portallarına otomatik sipariş girişi yapan güçlü RPA sisteminiz.
            Mann & Hummel ve Mutlu Akü entegrasyonları.
          </p>

          <div className="mt-12 flex items-center gap-8">
            <div>
              <p className="text-3xl font-bold text-white">24/7</p>
              <p className="text-primary-200 text-sm">Kesintisiz Çalışma</p>
            </div>
            <div className="w-px h-12 bg-white/20" />
            <div>
              <p className="text-3xl font-bold text-white">%99</p>
              <p className="text-primary-200 text-sm">Başarı Oranı</p>
            </div>
            <div className="w-px h-12 bg-white/20" />
            <div>
              <p className="text-3xl font-bold text-white">2</p>
              <p className="text-primary-200 text-sm">Tedarikçi</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-6 bg-gray-50">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl mb-4 shadow-lg shadow-primary-500/30">
              <Zap className="w-9 h-9 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">DoruMake</h1>
            <p className="text-gray-500 mt-1">Sipariş Otomasyon Sistemi</p>
          </div>

          {/* Login Card */}
          <div className="bg-white rounded-2xl shadow-xl shadow-gray-200/50 border border-gray-100 p-8">
            {!showForgotPassword ? (
              <>
                <div className="mb-8">
                  <h2 className="text-2xl font-bold text-gray-900">Hoş Geldiniz</h2>
                  <p className="text-gray-500 mt-1">Devam etmek için giriş yapın</p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-danger-50 border border-danger-100 rounded-xl flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-danger-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-danger-700">Giriş Hatası</p>
                      <p className="text-sm text-danger-600 mt-0.5">{error}</p>
                    </div>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div>
                    <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                      Kullanıcı Adı
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <User className="w-5 h-5 text-gray-400" />
                      </div>
                      <input
                        id="username"
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className={cn(
                          'w-full pl-12 pr-4 py-3 border rounded-xl',
                          'text-gray-900 placeholder-gray-400',
                          'transition-all duration-200',
                          'focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500',
                          'hover:border-gray-300',
                          error ? 'border-danger-300' : 'border-gray-200'
                        )}
                        placeholder="admin"
                        required
                        autoComplete="username"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                      Şifre
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <Lock className="w-5 h-5 text-gray-400" />
                      </div>
                      <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className={cn(
                          'w-full pl-12 pr-4 py-3 border rounded-xl',
                          'text-gray-900 placeholder-gray-400',
                          'transition-all duration-200',
                          'focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500',
                          'hover:border-gray-300',
                          error ? 'border-danger-300' : 'border-gray-200'
                        )}
                        placeholder="********"
                        required
                        autoComplete="current-password"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => setShowForgotPassword(true)}
                      className="text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors"
                    >
                      Şifremi Unuttum
                    </button>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className={cn(
                      'w-full flex items-center justify-center gap-2 px-6 py-3.5',
                      'bg-gradient-to-r from-primary-600 to-primary-500 text-white',
                      'rounded-xl font-semibold',
                      'hover:from-primary-700 hover:to-primary-600',
                      'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                      'disabled:opacity-50 disabled:cursor-not-allowed',
                      'transition-all duration-200',
                      'shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30'
                    )}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Giriş yapılıyor...
                      </>
                    ) : (
                      <>
                        <LogIn className="w-5 h-5" />
                        Giriş Yap
                      </>
                    )}
                  </button>
                </form>
              </>
            ) : (
              <>
                {!forgotSuccess ? (
                  <>
                    <div className="flex items-center gap-3 mb-6">
                      <button
                        onClick={resetForgotPassword}
                        className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
                      >
                        <ArrowLeft className="w-5 h-5 text-gray-600" />
                      </button>
                      <div>
                        <h2 className="text-xl font-bold text-gray-900">Şifremi Unuttum</h2>
                        <p className="text-sm text-gray-500">Şifre sıfırlama linki gönderin</p>
                      </div>
                    </div>

                    <p className="text-gray-600 mb-6">
                      E-posta adresinizi girin. Size yeni bir geçici şifre göndereceğiz.
                    </p>

                    {forgotError && (
                      <div className="mb-6 p-4 bg-danger-50 border border-danger-100 rounded-xl flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-danger-500 flex-shrink-0" />
                        <span className="text-sm text-danger-700">{forgotError}</span>
                      </div>
                    )}

                    <form onSubmit={handleForgotPassword} className="space-y-5">
                      <div>
                        <label htmlFor="forgotEmail" className="block text-sm font-medium text-gray-700 mb-2">
                          E-posta Adresi
                        </label>
                        <div className="relative">
                          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <Mail className="w-5 h-5 text-gray-400" />
                          </div>
                          <input
                            id="forgotEmail"
                            type="email"
                            value={forgotEmail}
                            onChange={(e) => setForgotEmail(e.target.value)}
                            className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 hover:border-gray-300"
                            placeholder="ornek@email.com"
                            required
                            autoComplete="email"
                          />
                        </div>
                      </div>

                      <button
                        type="submit"
                        disabled={forgotLoading}
                        className={cn(
                          'w-full flex items-center justify-center gap-2 px-6 py-3.5',
                          'bg-gradient-to-r from-primary-600 to-primary-500 text-white',
                          'rounded-xl font-semibold',
                          'hover:from-primary-700 hover:to-primary-600',
                          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                          'disabled:opacity-50 disabled:cursor-not-allowed',
                          'transition-all duration-200',
                          'shadow-lg shadow-primary-500/25'
                        )}
                      >
                        {forgotLoading ? (
                          <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            Gönderiliyor...
                          </>
                        ) : (
                          <>
                            <Mail className="w-5 h-5" />
                            Şifre Gönder
                          </>
                        )}
                      </button>
                    </form>
                  </>
                ) : (
                  <div className="text-center py-6">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-success-100 rounded-full mb-6">
                      <CheckCircle className="w-10 h-10 text-success-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">E-posta Gönderildi!</h3>
                    <p className="text-gray-600 mb-8">
                      Yeni şifreniz e-posta adresinize gönderildi. Lütfen gelen kutunuzu kontrol edin.
                    </p>
                    <button
                      onClick={resetForgotPassword}
                      className={cn(
                        'w-full flex items-center justify-center gap-2 px-6 py-3.5',
                        'bg-gradient-to-r from-primary-600 to-primary-500 text-white',
                        'rounded-xl font-semibold',
                        'hover:from-primary-700 hover:to-primary-600',
                        'transition-all duration-200',
                        'shadow-lg shadow-primary-500/25'
                      )}
                    >
                      <ArrowLeft className="w-5 h-5" />
                      Girişe Dön
                    </button>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          <p className="text-center text-sm text-gray-400 mt-8">
            DoruMake v1.0.0 - Doru Finansal
          </p>
        </div>
      </div>
    </div>
  );
}
