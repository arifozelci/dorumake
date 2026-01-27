'use client';

import { useState } from 'react';
import { Header } from '@/components';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatDate } from '@/lib/utils';
import { authService } from '@/lib/auth';
import { RefreshCw, Edit2, Mail, Check, X, Save } from 'lucide-react';

interface Template {
  id: number;
  name: string;
  subject: string;
  body: string;
  description: string;
  variables: string[];
  is_active: boolean;
  updated_at: string;
}

export default function TemplatesPage() {
  const queryClient = useQueryClient();
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [formData, setFormData] = useState({ subject: '', body: '', description: '' });

  const { data: templates, isLoading, refetch } = useQuery<Template[]>({
    queryKey: ['templates'],
    queryFn: async () => {
      const token = authService.getToken();
      const res = await fetch('/api/templates', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch templates');
      return res.json();
    }
  });

  const updateTemplate = useMutation({
    mutationFn: async ({ name, data }: { name: string; data: Partial<Template> }) => {
      const token = authService.getToken();
      const res = await fetch(`/api/templates/${name}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(data)
      });
      if (!res.ok) throw new Error('Failed to update template');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setEditingTemplate(null);
      alert('Şablon güncellendi');
    }
  });

  const openEditModal = (template: Template) => {
    setEditingTemplate(template);
    setFormData({ subject: template.subject, body: template.body, description: template.description });
  };

  const handleSave = () => {
    if (!editingTemplate) return;
    updateTemplate.mutate({ name: editingTemplate.name, data: formData });
  };

  const templateLabels: Record<string, string> = {
    'new_user': 'Yeni Kullanıcı',
    'password_reset': 'Şifre Sıfırlama',
    'password_changed': 'Şifre Değişikliği',
    'order_error': 'Sipariş Hatası',
    'order_completed': 'Sipariş Tamamlandı',
    'system_alert': 'Sistem Uyarısı'
  };

  return (
    <div>
      <Header title="E-posta Şablonları" subtitle="Bildirim e-posta şablonlarını yönetin" />

      <div className="p-6">
        <div className="flex justify-between mb-6">
          <button onClick={() => refetch()} className="btn btn-secondary">
            <RefreshCw className="w-4 h-4 mr-2" /> Yenile
          </button>
        </div>

        {editingTemplate ? (
          <div className="card p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">
                Şablon Düzenle: {templateLabels[editingTemplate.name] || editingTemplate.name}
              </h2>
              <div className="flex gap-2">
                <button onClick={() => setEditingTemplate(null)} className="btn btn-secondary">
                  <X className="w-4 h-4 mr-2" /> İptal
                </button>
                <button onClick={handleSave} className="btn btn-primary">
                  <Save className="w-4 h-4 mr-2" /> Kaydet
                </button>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Konu</label>
                <input
                  type="text"
                  className="input w-full"
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Açıklama</label>
                <input
                  type="text"
                  className="input w-full"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">İçerik</label>
                <textarea
                  className="input w-full h-64 font-mono text-sm"
                  value={formData.body}
                  onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                />
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <p className="text-sm font-medium mb-2">Kullanılabilir Değişkenler:</p>
                <div className="flex flex-wrap gap-2">
                  {editingTemplate.variables.map((v) => (
                    <code key={v} className="bg-gray-200 px-2 py-1 rounded text-sm">{'{' + v + '}'}</code>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {isLoading ? (
              <div className="col-span-2 text-center py-8 text-gray-500">Yükleniyor...</div>
            ) : templates?.map((template) => (
              <div key={template.id} className="card p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                      <Mail className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                      <h3 className="font-medium">{templateLabels[template.name] || template.name}</h3>
                      <p className="text-sm text-gray-500">{template.description}</p>
                    </div>
                  </div>
                  <button onClick={() => openEditModal(template)} className="p-2 hover:bg-gray-100 rounded">
                    <Edit2 className="w-4 h-4 text-gray-600" />
                  </button>
                </div>
                <div className="mt-3 pt-3 border-t">
                  <p className="text-sm text-gray-600 truncate">
                    <strong>Konu:</strong> {template.subject}
                  </p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-400">Son güncelleme: {formatDate(template.updated_at)}</span>
                    {template.is_active ? (
                      <span className="flex items-center gap-1 text-xs text-success-600"><Check className="w-3 h-3" /> Aktif</span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-gray-400"><X className="w-3 h-3" /> Pasif</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
