import { useState, useEffect } from 'react';
import { TestTube, Save, AlertCircle, CheckCircle } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { useToast } from './Toast';

interface RegistryConfig {
    type: 'dockerhub' | 'ecr' | 'gcr' | 'local';
    url?: string;
    username?: string;
    password?: string;
    namespace?: string;
    use_local_fallback: boolean;
}

const RegistrySettings = () => {
    const [registryType, setRegistryType] = useState<'dockerhub' | 'ecr' | 'gcr' | 'local'>('local');
    const [url, setUrl] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [namespace, setNamespace] = useState('');
    const [useLocalFallback, setUseLocalFallback] = useState(true);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<{ status: string; message: string } | null>(null);
    const toast = useToast();

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/settings/registry');
            if (res.ok) {
                const config: RegistryConfig = await res.json();
                setRegistryType(config.type || 'local');
                setUrl(config.url || '');
                setUsername(config.username || '');
                // Password is masked in response, don't update
                setNamespace(config.namespace || '');
                setUseLocalFallback(config.use_local_fallback !== false);
            }
        } catch (err) {
            console.error('Failed to load registry config:', err);
            toast.error('Failed to load configuration');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setTestResult(null);

        try {
            const config: RegistryConfig = {
                type: registryType,
                url: registryType !== 'local' ? url : undefined,
                username: registryType !== 'local' ? username : undefined,
                password: registryType !== 'local' && password ? password : undefined,
                namespace: registryType !== 'local' ? namespace : undefined,
                use_local_fallback: useLocalFallback
            };

            const res = await fetch('/api/settings/registry', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (res.ok) {
                toast.success('Registry configuration saved successfully!');
            } else {
                const error = await res.json();
                toast.error(`Failed to save: ${error.detail || 'Unknown error'}`);
            }
        } catch (err) {
            console.error('Failed to save registry config:', err);
            toast.error('Failed to save configuration');
        } finally {
            setSaving(false);
        }
    };

    const handleTest = async () => {
        setTesting(true);
        setTestResult(null);

        try {
            const config: RegistryConfig = {
                type: registryType,
                url: url || undefined,
                username: username || undefined,
                password: password || undefined,
                namespace: namespace || undefined,
                use_local_fallback: useLocalFallback
            };

            const res = await fetch('/api/settings/registry/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config })
            });

            if (res.ok) {
                const result = await res.json();
                setTestResult(result);

                if (result.status === 'success') {
                    toast.success(result.message);
                } else {
                    toast.error(result.message);
                }
            } else {
                const error = await res.json();
                setTestResult({ status: 'failed', message: error.detail || 'Test failed' });
                toast.error('Connection test failed');
            }
        } catch (err) {
            console.error('Failed to test registry:', err);
            setTestResult({ status: 'failed', message: String(err) });
            toast.error('Failed to test connection');
        } finally {
            setTesting(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-[#8be9fd] font-mono">Loading configuration...</div>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto p-8 space-y-6">
            <div className="bg-[#1a1b26] rounded-lg border border-[#282a36] p-6">
                <h2 className="text-2xl font-bold text-white mb-2">Docker Registry Configuration</h2>
                <p className="text-[#6272a4] text-sm mb-6">
                    Configure where Docker images are pushed after building
                </p>

                {/* Registry Type */}
                <div className="mb-6">
                    <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                        Registry Type
                    </label>
                    <select
                        value={registryType}
                        onChange={(e) => setRegistryType(e.target.value as 'dockerhub' | 'ecr' | 'gcr' | 'local')}
                        className="w-full bg-[#0b0b11] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                    >
                        <option value="local">Local (Minikube/Kind)</option>
                        <option value="dockerhub">Docker Hub</option>
                        <option value="ecr">AWS ECR</option>
                        <option value="gcr">Google GCR</option>
                    </select>
                </div>

                {/* Configuration for non-local registries */}
                {registryType !== 'local' && (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                            <div>
                                <label className="block text-sm font-mono text-[#6272a4] mb-2">
                                    Registry URL
                                </label>
                                <input
                                    type="text"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    className="w-full bg-[#0b0b11] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                    placeholder={registryType === 'dockerhub' ? 'docker.io' : 'registry.example.com'}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-mono text-[#6272a4] mb-2">
                                    Namespace/Org
                                </label>
                                <input
                                    type="text"
                                    value={namespace}
                                    onChange={(e) => setNamespace(e.target.value)}
                                    className="w-full bg-[#0b0b11] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                    placeholder="myorganization"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                            <div>
                                <label className="block text-sm font-mono text-[#6272a4] mb-2">
                                    Username
                                </label>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="w-full bg-[#0b0b11] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                    placeholder="username"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-mono text-[#6272a4] mb-2">
                                    Password/Token
                                </label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full bg-[#0b0b11] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                    placeholder="Enter new password/token"
                                />
                            </div>
                        </div>

                        <div className="flex items-center gap-3 mb-6 bg-[#0b0b11] border border-[#282a36] rounded p-4">
                            <input
                                type="checkbox"
                                id="fallback"
                                checked={useLocalFallback}
                                onChange={(e) => setUseLocalFallback(e.target.checked)}
                                className="w-4 h-4"
                            />
                            <label htmlFor="fallback" className="text-sm text-[#f8f8f2] font-mono cursor-pointer">
                                Fallback to local registry if push fails
                            </label>
                        </div>
                    </>
                )}

                {/* Test Result */}
                {testResult && (
                    <div
                        className={`mb-6 p-4 rounded flex items-start gap-3 ${testResult.status === 'success'
                            ? 'bg-[#50fa7b]/10 border border-[#50fa7b]/30'
                            : 'bg-[#ff5555]/10 border border-[#ff5555]/30'
                            }`}
                    >
                        {testResult.status === 'success' ? (
                            <CheckCircle size={20} className="text-[#50fa7b] flex-shrink-0 mt-0.5" />
                        ) : (
                            <AlertCircle size={20} className="text-[#ff5555] flex-shrink-0 mt-0.5" />
                        )}
                        <div>
                            <p
                                className={`font-mono text-sm ${testResult.status === 'success' ? 'text-[#50fa7b]' : 'text-[#ff5555]'
                                    }`}
                            >
                                {testResult.message}
                            </p>
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div className="flex gap-3">
                    <Button
                        onClick={handleTest}
                        disabled={testing || saving}
                        className="flex items-center gap-2 bg-[#ffb86c] hover:bg-[#ffb86c]/90 text-[#282a36] font-bold"
                    >
                        <TestTube size={16} />
                        {testing ? 'Testing...' : 'Test Connection'}
                    </Button>

                    <Button
                        onClick={handleSave}
                        disabled={saving || testing}
                        className="flex items-center gap-2 bg-[#8be9fd] hover:bg-[#8be9fd]/90 text-[#282a36] font-bold"
                    >
                        <Save size={16} />
                        {saving ? 'Saving...' : 'Save Configuration'}
                    </Button>
                </div>
            </div>

            {/* Info Box */}
            <div className="bg-[#8be9fd]/10 border border-[#8be9fd]/30 rounded p-4">
                <p className="text-sm text-[#8be9fd] font-mono">
                    💡 <strong>Info:</strong> After building Docker images for tools, they will be automatically
                    pushed to the configured registry. For local development, use "Local (Minikube/Kind)" mode.
                </p>
            </div>
        </div>
    );
};

export default RegistrySettings;
