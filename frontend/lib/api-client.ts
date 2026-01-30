/**
 * API Client with timeout support
 */

const DEFAULT_TIMEOUT = 30000; // 30 seconds
const API_BASE_URL =
  typeof window === "undefined"
    ? process.env.API_BASE_URL
    : process.env.NEXT_PUBLIC_API_BASE_URL;

if (!API_BASE_URL) {
  throw new Error("API_BASE_URL is not defined");
}

export class TimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TimeoutError";
  }
}

interface FetchOptions extends RequestInit {
  timeout?: number;
}

/**
 * Fetch with timeout support
 * @param url - The URL to fetch
 * @param options - Fetch options including optional timeout in milliseconds
 * @returns Promise with the fetch response
 * @throws TimeoutError if request exceeds timeout
 */
export async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = DEFAULT_TIMEOUT, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new TimeoutError(
        `Request timed out after ${timeout}ms`
      );
    }
    throw error;
  }
}

/**
 * API Client for backend requests
 */
export const apiClient = {
  /**
   * GET request to backend
   */
  async get<T>(
    endpoint: string,
    options: FetchOptions = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetchWithTimeout(url, {
      method: "GET",
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * POST request to backend
   */
  async post<T>(
    endpoint: string,
    data?: unknown,
    options: FetchOptions = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetchWithTimeout(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },
};

/**
 * Helper to check if an error is a timeout error
 */
export function isTimeoutError(error: unknown): error is TimeoutError {
  return error instanceof TimeoutError;
}

