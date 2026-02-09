'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Zap,
  Bot,
  ShoppingCart,
  FileSpreadsheet,
  Clock,
  Mail,
  Shield,
  ArrowRight,
  CheckCircle,
  Workflow,
  Building2,
  Cog,
  Menu,
  X,
} from 'lucide-react';

const capabilities = [
  {
    icon: ShoppingCart,
    title: 'Portal Otomasyonu',
    description:
      'Tedarikçi ve müşteri portallarına otomatik veri girişi. ERP ve e-ticaret sistemlerinizle entegre çalışır.',
  },
  {
    icon: FileSpreadsheet,
    title: 'Veri İşleme',
    description:
      'Excel, CSV, PDF dosyalarını otomatik okuyun, dönüştürün ve sistemlerinize aktarın.',
  },
  {
    icon: Mail,
    title: 'E-posta Otomasyonu',
    description:
      'Gelen e-postaları izleyin, ekleri çıkarın, içerikleri parse edin ve aksiyonları otomatik tetikleyin.',
  },
  {
    icon: Workflow,
    title: 'Portal & Web Otomasyon',
    description:
      'Web portallarında form doldurma, veri çekme, raporlama ve süreç yönetimi.',
  },
  {
    icon: Building2,
    title: 'ERP Entegrasyonu',
    description:
      'SAP, Logo, Mikro ve diğer ERP sistemleriyle veri alışverişi ve süreç otomasyonu.',
  },
  {
    icon: Cog,
    title: 'Özel RPA Çözümleri',
    description:
      'İşletmenize özel robotik süreç otomasyonu. İhtiyacınıza göre tasarlanır ve geliştirilir.',
  },
];

const stats = [
  { value: '7/24', label: 'Kesintisiz Çalışma' },
  { value: '%99.9', label: 'Uptime Garantisi' },
  { value: '<1dk', label: 'Ortalama İşlem Süresi' },
];

const steps = [
  {
    number: '01',
    title: 'Analiz',
    description: 'İş süreçlerinizi birlikte analiz ediyor, otomasyona uygun adımları belirliyoruz.',
  },
  {
    number: '02',
    title: 'Geliştirme',
    description: 'İşletmenize özel robot yazılımları geliştiriyor, mevcut sistemlerinize entegre ediyoruz.',
  },
  {
    number: '03',
    title: 'Devreye Alma',
    description: 'Robotlarınızı canlıya alıyor, gerçek zamanlı izleme paneli ile takibinize sunuyoruz.',
  },
  {
    number: '04',
    title: 'Sürekli Destek',
    description: 'Sistemlerinizi 7/24 izliyor, değişikliklere hızlıca uyum sağlıyoruz.',
  },
];

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100/80">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <span className="font-bold text-xl text-gray-900">KolayRobot</span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#capabilities" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              Hizmetler
            </a>
            <a href="#how-it-works" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              Nasıl Çalışır
            </a>
            <a href="#contact" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              İletişim
            </a>
            <Link
              href="/login"
              className="px-5 py-2.5 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-xl font-semibold text-sm hover:from-primary-700 hover:to-primary-600 transition-all duration-200 shadow-lg shadow-primary-500/25"
            >
              Giriş Yap
            </Link>
          </nav>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-gray-100 shadow-lg">
            <div className="max-w-6xl mx-auto px-6 py-4 flex flex-col gap-3">
              <a
                href="#capabilities"
                onClick={() => setMobileMenuOpen(false)}
                className="text-sm font-medium text-gray-600 hover:text-gray-900 py-2 transition-colors"
              >
                Hizmetler
              </a>
              <a
                href="#how-it-works"
                onClick={() => setMobileMenuOpen(false)}
                className="text-sm font-medium text-gray-600 hover:text-gray-900 py-2 transition-colors"
              >
                Nasıl Çalışır
              </a>
              <a
                href="#contact"
                onClick={() => setMobileMenuOpen(false)}
                className="text-sm font-medium text-gray-600 hover:text-gray-900 py-2 transition-colors"
              >
                İletişim
              </a>
              <Link
                href="/login"
                className="mt-2 px-5 py-3 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-xl font-semibold text-sm text-center hover:from-primary-700 hover:to-primary-600 transition-all duration-200 shadow-lg shadow-primary-500/25"
              >
                Giriş Yap
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden pt-16">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-primary-50/30" />
        <div className="absolute top-20 right-0 w-[600px] h-[600px] bg-primary-100/30 rounded-full -translate-y-1/3 translate-x-1/4 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-primary-100/20 rounded-full translate-y-1/2 -translate-x-1/4 blur-3xl" />

        <div className="relative max-w-6xl mx-auto px-6 py-24 lg:py-36">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-6">
                <Bot className="w-4 h-4" />
                Robotik Süreç Otomasyonu (RPA)
              </div>
              <h1 className="text-4xl lg:text-5xl xl:text-6xl font-bold text-gray-900 leading-[1.1] mb-6">
                İşletmenize Özel
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-400"> Robot Yazılımlar </span>
              </h1>
              <p className="text-lg text-gray-600 mb-8 leading-relaxed max-w-lg">
                Tekrarlayan manuel işlemlerinizi otomatikleştirin. Sipariş girişinden veri aktarımına, e-posta yönetiminden portal otomasyonuna kadar her süreci robotlarımıza bırakın.
              </p>
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                <a
                  href="#contact"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-xl font-semibold hover:from-primary-700 hover:to-primary-600 transition-all duration-200 shadow-lg shadow-primary-500/25 hover:shadow-xl hover:shadow-primary-500/30"
                >
                  Ücretsiz Analiz İsteyin
                  <ArrowRight className="w-5 h-5" />
                </a>
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 px-8 py-4 border border-gray-200 text-gray-700 rounded-xl font-semibold hover:border-primary-200 hover:text-primary-700 transition-all duration-200"
                >
                  Müşteri Girişi
                </Link>
              </div>
            </div>

            {/* Hero Visual - Robot Dashboard Preview */}
            <div className="hidden lg:block">
              <div className="relative">
                <div className="bg-white rounded-3xl shadow-2xl shadow-primary-500/10 border border-gray-100 p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center">
                      <Bot className="w-7 h-7 text-white" />
                    </div>
                    <div>
                      <p className="font-bold text-gray-900">KolayRobot</p>
                      <p className="text-sm text-gray-500">Otomasyon Durumu</p>
                    </div>
                    <div className="ml-auto flex items-center gap-2">
                      <span className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-sm font-medium text-green-600">Aktif</span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {[
                      { label: 'Sipariş Robotu', status: 'Çalışıyor', color: 'bg-green-500' },
                      { label: 'E-posta İzleyici', status: 'Çalışıyor', color: 'bg-green-500' },
                      { label: 'Veri Aktarım', status: 'Hazır', color: 'bg-blue-500' },
                    ].map((item) => (
                      <div key={item.label} className="flex items-center justify-between py-3 border-b border-gray-50 last:border-0">
                        <div className="flex items-center gap-3">
                          <span className={`w-2 h-2 rounded-full ${item.color}`} />
                          <span className="text-sm font-medium text-gray-700">{item.label}</span>
                        </div>
                        <span className="text-xs font-medium text-gray-500 bg-gray-50 px-3 py-1 rounded-full">{item.status}</span>
                      </div>
                    ))}
                  </div>

                  <div className="mt-6 grid grid-cols-3 gap-4">
                    {stats.map((stat) => (
                      <div key={stat.label} className="text-center">
                        <p className="text-2xl font-bold text-primary-600">{stat.value}</p>
                        <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Floating badge */}
                <div className="absolute -bottom-4 -left-4 bg-white rounded-2xl shadow-lg border border-gray-100 px-4 py-3 flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">Otomatik Tamamlandı</p>
                    <p className="text-xs text-gray-500">12 sipariş portala girildi</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Capabilities */}
      <section id="capabilities" className="py-24 bg-gray-50 scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-4">
              <Cog className="w-4 h-4" />
              Hizmetlerimiz
            </div>
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Ne Yapabiliriz?
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto text-lg">
              İşletmenizin tüm tekrarlayan süreçleri için özel RPA çözümleri geliştiriyoruz.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {capabilities.map((item) => (
              <div
                key={item.title}
                className="group bg-white p-8 rounded-2xl border border-gray-100 hover:shadow-xl hover:border-primary-100 hover:-translate-y-1 transition-all duration-300"
              >
                <div className="w-14 h-14 bg-primary-50 group-hover:bg-primary-100 rounded-2xl flex items-center justify-center mb-5 transition-colors">
                  <item.icon className="w-7 h-7 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-gray-600 leading-relaxed">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="py-24 scroll-mt-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-4">
              <Workflow className="w-4 h-4" />
              Süreç
            </div>
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              Nasıl Çalışır?
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto text-lg">
              4 adımda işletmenize özel otomasyon çözümünüz hazır.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div key={step.number} className="relative">
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-10 left-[calc(50%+2rem)] w-[calc(100%-4rem)] h-px bg-gradient-to-r from-primary-200 to-primary-100" />
                )}
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-600 rounded-3xl text-white font-bold text-2xl mb-5 shadow-lg shadow-primary-500/25">
                    {step.number}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA / Advantages */}
      <section className="py-24 bg-gradient-to-br from-primary-600 via-primary-500 to-primary-700 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-white/5 rounded-full -translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-white/5 rounded-full translate-x-1/3 translate-y-1/3" />

        <div className="relative max-w-6xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl lg:text-4xl font-bold text-white mb-6">
                Manuel İşlemlerden Kurtulun
              </h2>
              <p className="text-primary-100 text-lg mb-8 leading-relaxed">
                Çalışanlarınız tekrarlayan işlemler yerine katma değerli işlere odaklansın. Robotlarımız 7/24 çalışır, hata yapmaz, yorulmaz.
              </p>
              <div className="space-y-4">
                {[
                  'Zaman tasarrufu - saatler süren işlemler dakikalara iner',
                  'Sıfır hata oranı - insan kaynaklı hatalar ortadan kalkar',
                  'Gerçek zamanlı takip - her işlem anlık izlenir ve raporlanır',
                  'Ölçeklenebilir - yeni süreçler kolayca eklenebilir',
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-primary-200 flex-shrink-0 mt-0.5" />
                    <span className="text-white/90">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="text-center lg:text-right">
              <div className="inline-block bg-white/10 backdrop-blur-sm rounded-3xl p-8 border border-white/20">
                <Shield className="w-16 h-16 text-white mx-auto mb-4" />
                <p className="text-5xl font-bold text-white mb-2">%80</p>
                <p className="text-primary-100 text-lg">Daha Az Manuel İş Yükü</p>
                <div className="mt-6 pt-6 border-t border-white/20">
                  <p className="text-3xl font-bold text-white mb-1">10x</p>
                  <p className="text-primary-200">Daha Hızlı İşlem</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact */}
      <section id="contact" className="py-24 bg-gray-50 scroll-mt-16">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
            İşletmenize Özel Çözüm İçin
          </h2>
          <p className="text-gray-600 text-lg mb-10">
            Otomasyona uygun süreçlerinizi birlikte belirleyelim. Ücretsiz analiz ve teklif için bize ulaşın.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <a
              href="mailto:info@dorufinansal.com"
              className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-xl font-semibold hover:from-primary-700 hover:to-primary-600 transition-all duration-200 shadow-lg shadow-primary-500/25"
            >
              <Mail className="w-5 h-5" />
              info@dorufinansal.com
            </a>
          </div>
          <p className="text-gray-400 text-sm mt-6">Doru Finansal Teknoloji</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 bg-white">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-gray-900">KolayRobot</span>
          </div>
          <p className="text-sm text-gray-400">
            &copy; {new Date().getFullYear()} Doru Finansal. Tüm hakları saklıdır.
          </p>
        </div>
      </footer>
    </div>
  );
}
