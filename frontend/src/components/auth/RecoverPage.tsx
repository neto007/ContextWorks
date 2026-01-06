import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import { Shield, Mail, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';

export const RecoverPage: React.FC = () => {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { recover } = useAuth();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setIsLoading(true);

        try {
            await recover(email);
            setMessage('If an account exists for this email, you will receive a recovery link shortly.');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to send recovery request');
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

            <div className="w-full max-w-md p-8 relative z-10">
                <div className="mb-8 text-center animate-fade-in-down">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-[#50fa7b] to-[#8be9fd] mb-6 shadow-[0_0_20px_rgba(80,250,123,0.3)]">
                        <Shield className="w-8 h-8 text-[#282a36]" />
                    </div>
                    <h2 className="text-3xl font-bold mb-2 tracking-tight">Recovery</h2>
                    <p className="text-[#6272a4]">Reset your password securely</p>
                </div>

                <div className="bg-[#1a1b26]/80 backdrop-blur-xl rounded-xl border border-[#bd93f9]/20 p-8 shadow-2xl animate-fade-in-up">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="bg-[#ff5555]/10 border border-[#ff5555]/20 text-[#ff5555] px-4 py-3 rounded-lg flex items-center gap-2 text-sm">
                                <AlertCircle size={16} />
                                {error}
                            </div>
                        )}
                        {message && (
                            <div className="bg-[#50fa7b]/10 border border-[#50fa7b]/20 text-[#50fa7b] px-4 py-3 rounded-lg flex items-center gap-2 text-sm">
                                <CheckCircle size={16} />
                                {message}
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-[#f8f8f2] ml-1">Email</label>
                            <div className="relative group">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6272a4] group-focus-within:text-[#bd93f9] transition-colors" size={18} />
                                <input
                                    id="email"
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full bg-[#050101] border border-[#6272a4]/30 rounded-lg px-4 py-3 pl-10 text-[#f8f8f2] placeholder-[#6272a4] focus:outline-none focus:border-[#bd93f9] focus:ring-1 focus:ring-[#bd93f9] transition-all"
                                    placeholder="name@company.com"
                                    required
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-gradient-to-r from-[#50fa7b] to-[#8be9fd] text-[#282a36] font-bold py-3 rounded-lg hover:shadow-[0_0_20px_rgba(80,250,123,0.3)] hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 group"
                        >
                            {isLoading ? (
                                <div className="w-5 h-5 border-2 border-[#282a36] border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <>
                                    Send Recovery Link <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>
                </div>

                <p className="mt-8 text-center text-[#6272a4] text-sm">
                    Remember your password?{' '}
                    <Link to="/login" className="text-[#bd93f9] hover:text-[#ff79c6] font-medium transition-colors">
                        Back to login
                    </Link>
                </p>
            </div>
        </div>
    );
};
export default RecoverPage;
