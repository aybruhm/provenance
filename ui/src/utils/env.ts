import { env } from '$env/dynamic/public';

class EnvUtils {
	private static instance: EnvUtils;
	private baseUrl: string;

	private constructor() {
		const baseUrl = env.PUBLIC_API_BASE_URL || 'http://localhost:4587/api/v1';
		this.baseUrl = baseUrl;
	}

	public static getInstance(): EnvUtils {
		if (!EnvUtils.instance) {
			EnvUtils.instance = new EnvUtils();
		}
		return EnvUtils.instance;
	}

	public getBaseUrl(): string {
		return this.baseUrl;
	}
}

export const envUtils = EnvUtils.getInstance();
