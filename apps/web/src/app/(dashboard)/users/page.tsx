'use client';

import { useState } from 'react';
import { Header } from '@/components';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatDate } from '@/lib/utils';
import { authService } from '@/lib/auth';
import { RefreshCw, Plus, Edit2, Trash2, Key, Mail, UserCheck, UserX, Shield, User } from 'lucide-react';

interface UserData {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  receive_notifications: boolean;
  created_at: string;
}

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<UserData | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'user'
  });

  const { data: users, isLoading, refetch } = useQuery<UserData[]>({
    queryKey: ['users'],
    queryFn: async () => {
      const token = authService.getToken();
      const res = await fetch('/api/users', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch users');
      return res.json();
    }
  });

  const createUser = useMutation({
    mutationFn: async (data: typeof formData) => {
      const token = authService.getToken();
      const res = await fetch('/api/users/create-with-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(data)
      });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowModal(false);
      resetForm();
      alert('Kullanici olusturuldu ve e-posta gonderildi');
    }
  });

  const updateUser = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<UserData> }) => {
      const token = authService.getToken();
      const res = await fetch(`/api/users/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(data)
      });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowModal(false);
      setEditingUser(null);
      resetForm();
    }
  });

  const deleteUser = useMutation({
    mutationFn: async (id: number) => {
      const token = authService.getToken();
      const res = await fetch(`/api/users/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] })
  });

  const resetPassword = useMutation({
    mutationFn: async (id: number) => {
      const token = authService.getToken();
      const res = await fetch(`/api/users/${id}/reset-password`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    onSuccess: () => alert('Sifre sifirlandi ve e-posta gonderildi')
  });

  const resetForm = () => setFormData({ username: '', email: '', password: '', full_name: '', role: 'user' });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingUser) {
      updateUser.mutate({ id: editingUser.id, data: { email: formData.email, full_name: formData.full_name, role: formData.role } });
    } else {
      createUser.mutate(formData);
    }
  };

  const openEditModal = (user: UserData) => {
    setEditingUser(user);
    setFormData({ username: user.username, email: user.email, password: '', full_name: user.full_name, role: user.role });
    setShowModal(true);
  };

  return (
    <div>
      <Header title="Kullanici Yonetimi" subtitle="Sistem kullanicilarini yonetin" />
      <div className="p-6">
        <div className="flex justify-between mb-6">
          <button onClick={() => refetch()} className="btn btn-secondary">
            <RefreshCw className="w-4 h-4 mr-2" /> Yenile
          </button>
          <button onClick={() => { resetForm(); setEditingUser(null); setShowModal(true); }} className="btn btn-primary">
            <Plus className="w-4 h-4 mr-2" /> Yeni Kullanici
          </button>
        </div>

        <div className="card overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left p-4">Kullanici</th>
                <th className="text-left p-4">E-posta</th>
                <th className="text-left p-4">Rol</th>
                <th className="text-left p-4">Durum</th>
                <th className="text-left p-4">Bildirim</th>
                <th className="text-left p-4">Olusturulma</th>
                <th className="text-right p-4">Islemler</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={7} className="p-8 text-center text-gray-500">Yukleniyor...</td></tr>
              ) : users?.map((user) => (
                <tr key={user.id} className="border-b hover:bg-gray-50">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                        {user.role === 'admin' ? <Shield className="w-4 h-4 text-primary-600" /> : <User className="w-4 h-4 text-gray-600" />}
                      </div>
                      <div>
                        <p className="font-medium">{user.full_name || user.username}</p>
                        <p className="text-sm text-gray-500">@{user.username}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 text-gray-600">{user.email}</td>
                  <td className="p-4">
                    <span className={user.role === 'admin' ? 'badge badge-primary' : 'badge badge-secondary'}>
                      {user.role === 'admin' ? 'Admin' : 'Kullanici'}
                    </span>
                  </td>
                  <td className="p-4">
                    {user.is_active ? (
                      <span className="flex items-center gap-1 text-success-600"><UserCheck className="w-4 h-4" /> Aktif</span>
                    ) : (
                      <span className="flex items-center gap-1 text-danger-600"><UserX className="w-4 h-4" /> Pasif</span>
                    )}
                  </td>
                  <td className="p-4">
                    <Mail className={`w-4 h-4 ${user.receive_notifications ? 'text-primary-600' : 'text-gray-300'}`} />
                  </td>
                  <td className="p-4 text-sm text-gray-500">{formatDate(user.created_at)}</td>
                  <td className="p-4">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => openEditModal(user)} className="p-2 hover:bg-gray-100 rounded" title="Duzenle">
                        <Edit2 className="w-4 h-4 text-gray-600" />
                      </button>
                      <button onClick={() => resetPassword.mutate(user.id)} className="p-2 hover:bg-gray-100 rounded" title="Sifre Sifirla">
                        <Key className="w-4 h-4 text-warning-600" />
                      </button>
                      {user.username !== 'admin' && (
                        <button onClick={() => { if (confirm('Bu kullaniciyi silmek istediginize emin misiniz?')) deleteUser.mutate(user.id); }} className="p-2 hover:bg-gray-100 rounded" title="Sil">
                          <Trash2 className="w-4 h-4 text-danger-600" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4">{editingUser ? 'Kullanici Duzenle' : 'Yeni Kullanici'}</h2>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                {!editingUser && (
                  <div>
                    <label className="block text-sm font-medium mb-1">Kullanici Adi</label>
                    <input type="text" className="input w-full" value={formData.username} onChange={(e) => setFormData({ ...formData, username: e.target.value })} required />
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium mb-1">Ad Soyad</label>
                  <input type="text" className="input w-full" value={formData.full_name} onChange={(e) => setFormData({ ...formData, full_name: e.target.value })} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">E-posta</label>
                  <input type="email" className="input w-full" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} required />
                </div>
                {!editingUser && (
                  <div>
                    <label className="block text-sm font-medium mb-1">Sifre (bos birakilirsa otomatik)</label>
                    <input type="password" className="input w-full" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} />
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium mb-1">Rol</label>
                  <select className="input w-full" value={formData.role} onChange={(e) => setFormData({ ...formData, role: e.target.value })}>
                    <option value="user">Kullanici</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => { setShowModal(false); setEditingUser(null); resetForm(); }} className="btn btn-secondary">Iptal</button>
                <button type="submit" className="btn btn-primary">{editingUser ? 'Guncelle' : 'Olustur'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
