export interface Argument {
    name: string;
    type: 'str' | 'int' | 'bool' | 'file';
    description: string;
    required: boolean;
    default?: string;
}

export type DockerMode = 'auto' | 'preexisting' | 'custom';

export interface ResourceLimit {
    cpu: string;
    memory: string;
}

export interface ToolResources {
    requests?: ResourceLimit;
    limits?: ResourceLimit;
}

export interface DockerConfig {
    docker_mode?: DockerMode;
    image?: string;
    base_image?: string;
    apt_packages?: string[];
    pip_packages?: string[];
    resources?: ToolResources;
}

export interface BuildResult {
    status: 'pending' | 'success' | 'failed' | 'running';
    job_id?: string;
    message?: string;
}

export interface Tool {
    id: string;
    name: string;
    category: string;
    description?: string;
    script_code?: string;
    arguments?: Argument[];
    docker?: DockerConfig;
    resources?: ToolResources;
    build_result?: BuildResult;
    has_logo?: boolean;
    created_at?: string;
}
