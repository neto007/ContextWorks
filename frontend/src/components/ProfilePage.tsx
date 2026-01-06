import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock, User, LogOut, ArrowLeft, AlertCircle, CheckCircle } from 'lucide-react';

const ProfilePage: React.FC = () => {
    const { user, logout, updatePassword } = useAuth();
    const navigate = useNavigate();

    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const handleUpdatePassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (newPassword !== confirmPassword) {
            setError("New passwords don't match");
            return;
        }

        if (newPassword.length < 6) {
            setError("Password must be at least 6 characters");
            return;
        }

        setIsLoading(true);

        try {
            await updatePassword(currentPassword, newPassword);
            setSuccess('Password updated successfully');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to update password');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-[#050101] text-[#f8f8f2] font-['JetBrains_Mono']">
            {/* Grid Background Effect */}
            <div
                className="absolute inset-0 pointer-events-none"
                style={{
                    backgroundImage: 'radial-gradient(rgba(189, 147, 249, 0.05) 1px, transparent 1px)',
                    backgroundSize: '40px 40px'
                }}
            />

            <div className="w-full max-w-2xl p-8 relative z-10">
                <div className="mb-4">
                    <button
                        onClick={() => navigate('/')}
                        className="flex items-center text-[#6272a4] hover:text-[#f8f8f2] transition-colors mb-4"
                    >
                        <ArrowLeft size={16} className="mr-2" /> Back to Dashboard
                    </button>
                </div>

                <div className="mb-8 flex items-center justify-between animate-fade-in-down">
                    <div>
                        <div className="flex items-center gap-4 mb-2">
                            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[#50fa7b] to-[#8be9fd] shadow-[0_0_20px_rgba(80,250,123,0.3)]">
                                <User className="w-6 h-6 text-[#282a36]" />
                            </div>
                            <div>
                                <h2 className="text-3xl font-bold tracking-tight">Profile Settings</h2>
                                <p className="text-[#6272a4]">{user?.email}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid gap-6">
                    {/* Security Section */}
                    <div className="bg-[#1a1b26]/80 backdrop-blur-xl rounded-xl border border-[#bd93f9]/20 p-8 shadow-2xl animate-fade-in-up">
                        <div className="flex items-center gap-2 mb-6 text-[#bd93f9]">
                            <Shield size={20} />
                            <h3 className="text-xl font-bold">Security</h3>
                        </div>

                        {error && (
                            <div className="mb-6 bg-[#ff5555]/10 border border-[#ff5555]/20 text-[#ff5555] px-4 py-3 rounded-lg flex items-center gap-2 text-sm">
                                <AlertCircle size={16} />
                                {error}
                            </div>
                        )}

                        {success && (
                            <div className="mb-6 bg-[#50fa7b]/10 border border-[#50fa7b]/20 text-[#50fa7b] px-4 py-3 rounded-lg flex items-center gap-2 text-sm">
                                <CheckCircle size={16} />
                                {success}
                            </div>
                        )}

                        <form onSubmit={handleUpdatePassword} className="space-y-4">
                            {/* Hidden username field for password manager accessibility */}
                            <input
                                type="text"
                                name="username"
                                value={user?.email || ''}
                                autoComplete="username"
                                className="hidden"
                                readOnly
                            />
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-[#f8f8f2] ml-1">Current Password</label>
                                <div className="relative group">
                                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6272a4] group-focus-within:text-[#bd93f9] transition-colors" size={18} />
                                    <input
                                        type="password"
                                        autoComplete="current-password"
                                        value={currentPassword}
                                        onChange={(e) => setCurrentPassword(e.target.value)}
                                        className="w-full bg-[#050101] border border-[#6272a4]/30 rounded-lg px-4 py-3 pl-10 text-[#f8f8f2] placeholder-[#6272a4] focus:outline-none focus:border-[#bd93f9] focus:ring-1 focus:ring-[#bd93f9] transition-all"
                                        placeholder="••••••••"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-[#f8f8f2] ml-1">New Password</label>
                                    <div className="relative group">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6272a4] group-focus-within:text-[#bd93f9] transition-colors" size={18} />
                                        <input
                                            type="password"
                                            autoComplete="new-password"
                                            value={newPassword}
                                            onChange={(e) => setNewPassword(e.target.value)}
                                            className="w-full bg-[#050101] border border-[#6272a4]/30 rounded-lg px-4 py-3 pl-10 text-[#f8f8f2] placeholder-[#6272a4] focus:outline-none focus:border-[#bd93f9] focus:ring-1 focus:ring-[#bd93f9] transition-all"
                                            placeholder="••••••••"
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-[#f8f8f2] ml-1">Confirm New Password</label>
                                    <div className="relative group">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6272a4] group-focus-within:text-[#bd93f9] transition-colors" size={18} />
                                        <input
                                            type="password"
                                            autoComplete="new-password"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            className="w-full bg-[#050101] border border-[#6272a4]/30 rounded-lg px-4 py-3 pl-10 text-[#f8f8f2] placeholder-[#6272a4] focus:outline-none focus:border-[#bd93f9] focus:ring-1 focus:ring-[#bd93f9] transition-all"
                                            placeholder="••••••••"
                                            required
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="pt-2 flex justify-end">
                                <button
                                    type="submit"
                                    disabled={isLoading}
                                    className="px-6 py-2.5 bg-[#bd93f9] text-[#282a36] font-bold rounded-lg hover:bg-[#ff79c6] hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-[#bd93f9]/20"
                                >
                                    {isLoading ? 'Updating...' : 'Update Password'}
                                </button>
                            </div>
                        </form>
                    </div>

                    {/* Account Actions */}
                    <div className="bg-[#1a1b26]/80 backdrop-blur-xl rounded-xl border border-[#ff5555]/20 p-8 shadow-2xl animate-fade-in-up md:col-span-2">
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-xl font-bold text-[#f8f8f2]">Session Management</h3>
                                <p className="text-[#6272a4] text-sm mt-1">Sign out of your current session</p>
                            </div>
                            <button
                                onClick={handleLogout}
                                className="flex items-center gap-2 px-6 py-2.5 bg-[#ff5555]/10 border border-[#ff5555]/50 text-[#ff5555] font-bold rounded-lg hover:bg-[#ff5555] hover:text-white hover:-translate-y-0.5 transition-all duration-200"
                            >
                                <LogOut size={18} />
                                Sign Out
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;
