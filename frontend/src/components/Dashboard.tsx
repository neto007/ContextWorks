import { useState, useEffect, Suspense, lazy } from 'react';
import { useNavigate, useParams, Routes, Route } from 'react-router-dom';
import AppSidebar from './Sidebar';

// Lazy load heavy components
const HistoryPage = lazy(() => import('./HistoryPage'));
const MCPManager = lazy(() => import('./MCPManager'));
const WorkspaceManager = lazy(() => import('./WorkspaceManager'));
const ToolRunner = lazy(() => import('./ToolRunner'));
const ToolList = lazy(() => import('./ToolList'));
const Overview = lazy(() => import('./Overview'));
const RegistrySettings = lazy(() => import('./RegistrySettings'));

interface Tool {
    id: string;
    name: string;
    path: string;
    yaml_path: string;
    category: string;
    description?: string;
    has_logo?: boolean;
}

interface Workspace {
    name: string;
    has_logo: boolean;
    tool_count: number;
    description: string;
}

function Dashboard() {
    const [tools, setTools] = useState<Record<string, Tool[]>>({});
    const [categories, setCategories] = useState<Workspace[]>([]);
    const navigate = useNavigate();
    const { category } = useParams<{ category?: string }>();

    const refreshData = async () => {
        try {
            // Fetch tools with cache busting
            const toolsRes = await fetch(`/api/tools?t=${Date.now()}`);
            const toolsData = await toolsRes.json();
            setTools(toolsData);

            // Fetch workspaces (categories) directly to include empty ones
            const workspacesRes = await fetch(`/api/workspaces?t=${Date.now()}`);
            const workspacesData = await workspacesRes.json();

            // Store full workspace objects
            setCategories(workspacesData);
        } catch (err) {
            console.error('Failed to fetch data:', err);
        }
    };

    useEffect(() => {
        refreshData();
    }, []);

    const handleSelectCategory = (cat: string) => {
        if (cat === 'overview') {
            navigate('/');
        } else if (cat === 'history') {
            navigate('/history');
        } else if (cat === 'workspaces') {
            navigate('/workspaces');
        } else if (cat === 'mcp-servers') {
            navigate('/mcp-servers');
        } else if (cat === 'settings') {
            navigate('/settings');
        } else {
            navigate(`/workspace/${cat}`);
        }
    };

    const LoadingFallback = () => (
        <div className="flex items-center justify-center h-full text-[#6272a4] animate-pulse">
            <div className="animate-spin mr-2">⚙️</div> Loading...
        </div>
    );

    // Wrapper components that use useParams internally
    const ToolListWrapper = () => {
        const { category } = useParams<{ category: string }>();
        const navigate = useNavigate();

        return (
            <div className="h-full animate-fade-in">
                <ToolList
                    tools={tools[category || ''] || []}
                    onSelectTool={(selectedToolId) => {
                        // selectedToolId pode ser "Network/nmap_scan" ou "nmap_scan"
                        // Queremos apenas o nome sem categoria
                        const toolName = selectedToolId.split('/').pop() || selectedToolId;
                        navigate(`/workspace/${category}/tool/${toolName}`);
                    }}
                />
            </div>
        );
    };

    const ToolRunnerWrapper = () => {
        const { category, toolId } = useParams<{ category: string; toolId: string }>();
        const navigate = useNavigate();
        const [fullToolDetails, setFullToolDetails] = useState<any | null>(null);

        useEffect(() => {
            if (!category || !toolId) {
                setFullToolDetails(null);
                return;
            }

            // toolId já contém formato "category/toolname", então pegamos apenas o toolname
            const toolName = toolId.split('/').pop() || toolId;

            fetch(`/api/tools/${category}/${toolName}`)
                .then(res => res.json())
                .then(data => setFullToolDetails(data))
                .catch(err => console.error('Failed to fetch tool details:', err));
        }, [category, toolId]);

        if (!fullToolDetails) {
            return <LoadingFallback />;
        }

        return (
            <div className="h-full animate-slide-in-right">
                <ToolRunner
                    tool={fullToolDetails}
                    onBack={() => navigate(`/workspace/${category}`)}
                />
            </div>
        );
    };

    return (
        <div className="flex h-screen w-screen bg-dracula-bg overflow-hidden relative">
            <AppSidebar
                categories={categories}
                selectedCategory={category || null}
                onSelectCategory={handleSelectCategory}
            />
            <main className="flex-1 overflow-y-auto custom-scrollbar relative">
                <div className="p-10 relative z-10 w-full h-full">
                    <Suspense fallback={<LoadingFallback />}>
                        <Routes>
                            {/* Overview */}
                            <Route index element={
                                <div className="h-full animate-fade-in">
                                    <Overview />
                                </div>
                            } />

                            {/* History */}
                            <Route path="history" element={
                                <div className="h-full animate-fade-in">
                                    <HistoryPage />
                                </div>
                            } />

                            {/* Workspaces Manager */}
                            <Route path="workspaces" element={
                                <div className="h-full animate-fade-in">
                                    <WorkspaceManager onRefreshWorkspaces={refreshData} />
                                </div>
                            } />

                            {/* MCP Servers */}
                            <Route path="mcp-servers" element={
                                <div className="h-full animate-fade-in">
                                    <MCPManager />
                                </div>
                            } />

                            {/* Settings */}
                            <Route path="settings" element={
                                <div className="h-full animate-fade-in">
                                    <RegistrySettings />
                                </div>
                            } />

                            {/* Workspace Tool List */}
                            <Route path="workspace/:category" element={<ToolListWrapper />} />

                            {/* Tool Runner */}
                            <Route path="workspace/:category/tool/:toolId" element={<ToolRunnerWrapper />} />
                        </Routes>
                    </Suspense>
                </div>

                {/* Background Grid */}
                <div
                    className="fixed inset-0 pointer-events-none z-0 opacity-10"
                    style={{
                        backgroundImage: `
              linear-gradient(rgba(139, 233, 253, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(139, 233, 253, 0.1) 1px, transparent 1px)
            `,
                        backgroundSize: '40px 40px'
                    }}
                />

                {/* Gradient Overlay */}
                <div
                    className="fixed inset-0 pointer-events-none z-0"
                    style={{
                        background: 'radial-gradient(circle at 50% 0%, rgba(139, 233, 253, 0.05) 0%, transparent 50%)'
                    }}
                />
            </main>
        </div>
    );
}

export default Dashboard;
