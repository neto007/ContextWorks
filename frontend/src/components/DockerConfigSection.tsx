import React from 'react';
import type { DockerMode } from '../types/tool';

interface DockerConfigSectionProps {
    dockerMode: DockerMode;
    setDockerMode: (mode: DockerMode) => void;
    preexistingImage: string;
    setPreexistingImage: (image: string) => void;
    baseImage: string;
    setBaseImage: (image: string) => void;
    aptPackages: string[];
    setAptPackages: (packages: string[]) => void;
    pipPackages: string[];
    setPipPackages: (packages: string[]) => void;
    cpuRequest: string;
    setCpuRequest: (val: string) => void;
    cpuLimit: string;
    setCpuLimit: (val: string) => void;
    memoryRequest: string;
    setMemoryRequest: (val: string) => void;
    memoryLimit: string;
    setMemoryLimit: (val: string) => void;
}

const DockerConfigSection: React.FC<DockerConfigSectionProps> = ({
    dockerMode, setDockerMode,
    preexistingImage, setPreexistingImage,
    baseImage, setBaseImage,
    aptPackages, setAptPackages,
    pipPackages, setPipPackages,
    cpuRequest, setCpuRequest,
    cpuLimit, setCpuLimit,
    memoryRequest, setMemoryRequest,
    memoryLimit, setMemoryLimit
}) => {
    return (
        <div className="space-y-6">
            <div>
                <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                    Docker Mode
                </label>
                <select
                    value={dockerMode}
                    onChange={(e) => setDockerMode(e.target.value as DockerMode)}
                    className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                >
                    <option value="auto">Auto (Python 3.11 slim)</option>
                    <option value="preexisting">Use Pre-existing Image</option>
                    <option value="custom">Build Custom Image</option>
                </select>
            </div>

            {dockerMode === 'preexisting' && (
                <div>
                    <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                        Docker Image
                    </label>
                    <input
                        type="text"
                        value={preexistingImage}
                        onChange={(e) => setPreexistingImage(e.target.value)}
                        className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                        placeholder="instrumentisto/nmap:latest"
                    />
                </div>
            )}

            {dockerMode === 'custom' && (
                <>
                    <div>
                        <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                            Base Image
                        </label>
                        <select
                            value={baseImage}
                            onChange={(e) => setBaseImage(e.target.value)}
                            className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                        >
                            <option value="python:3.11-slim">Python 3.11 Slim</option>
                            <option value="python:3.12-slim">Python 3.12 Slim</option>
                            <option value="python:3.10-slim">Python 3.10 Slim</option>
                            <option value="ubuntu:22.04">Ubuntu 22.04</option>
                            <option value="alpine:latest">Alpine Latest</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                            APT Packages (one per line)
                        </label>
                        <textarea
                            value={aptPackages.join('\n')}
                            onChange={(e) => setAptPackages(e.target.value.split('\n'))}
                            className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd] resize-none"
                            rows={4}
                            placeholder="nmap&#10;curl&#10;wget"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                            PIP Packages (one per line)
                        </label>
                        <textarea
                            value={pipPackages.join('\n')}
                            onChange={(e) => setPipPackages(e.target.value.split('\n'))}
                            className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd] resize-none"
                            rows={4}
                            placeholder="requests&#10;beautifulsoup4&#10;python-nmap"
                        />
                    </div>
                </>
            )}

            {dockerMode !== 'auto' && (
                <>
                    <h4 className="text-sm font-mono text-[#8be9fd] uppercase mt-6 mb-3">
                        Kubernetes Resources
                    </h4>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-mono text-[#6272a4] mb-2">
                                CPU Request
                            </label>
                            <input
                                type="text"
                                value={cpuRequest}
                                onChange={(e) => setCpuRequest(e.target.value)}
                                className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                placeholder="100m"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-mono text-[#6272a4] mb-2">
                                CPU Limit
                            </label>
                            <input
                                type="text"
                                value={cpuLimit}
                                onChange={(e) => setCpuLimit(e.target.value)}
                                className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                placeholder="1000m"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-mono text-[#6272a4] mb-2">
                                Memory Request
                            </label>
                            <input
                                type="text"
                                value={memoryRequest}
                                onChange={(e) => setMemoryRequest(e.target.value)}
                                className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                placeholder="256Mi"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-mono text-[#6272a4] mb-2">
                                Memory Limit
                            </label>
                            <input
                                type="text"
                                value={memoryLimit}
                                onChange={(e) => setMemoryLimit(e.target.value)}
                                className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                placeholder="1024Mi"
                            />
                        </div>
                    </div>

                    <div className="bg-[#8be9fd]/10 border border-[#8be9fd]/30 rounded p-4">
                        <p className="text-sm text-[#8be9fd] font-mono">
                            💡 <strong>Dica:</strong> Recursos padrão são 100m CPU / 256Mi RAM. Para ferramentas pesadas como Nmap, considere 500m+ CPU e 512Mi+ RAM.
                        </p>
                    </div>
                </>
            )}
        </div>
    );
};

export default DockerConfigSection;
