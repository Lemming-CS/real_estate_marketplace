const jsonHeaders = {
  'Content-Type': 'application/json',
};

export const apiClientConfig = {
  appName: import.meta.env.VITE_APP_NAME ?? 'Electronics Marketplace Admin',
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
};

export class ApiError extends Error {
  constructor(message, status, code, details) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function buildUrl(path, query) {
  const url = new URL(`${apiClientConfig.baseUrl}${path}`);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') {
        return;
      }

      url.searchParams.set(key, String(value));
    });
  }
  return url.toString();
}

export async function apiRequest(path, options = {}) {
  const {
    method = 'GET',
    token,
    query,
    body,
    headers = {},
  } = options;

  const response = await fetch(buildUrl(path, query), {
    method,
    headers: {
      ...(body instanceof FormData ? {} : jsonHeaders),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  });

  const contentType = response.headers.get('content-type') ?? '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();

  if (!response.ok) {
    const error = payload?.error;
    throw new ApiError(
      error?.message ?? `Request failed with status ${response.status}`,
      response.status,
      error?.code ?? 'request_failed',
      error?.details ?? payload?.detail ?? null,
    );
  }

  return payload;
}

export async function apiBlobRequest(path, options = {}) {
  const {
    method = 'GET',
    token,
    query,
    body,
    headers = {},
  } = options;

  const response = await fetch(buildUrl(path, query), {
    method,
    headers: {
      ...(body instanceof FormData ? {} : jsonHeaders),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const contentType = response.headers.get('content-type') ?? '';
    const payload = contentType.includes('application/json')
      ? await response.json()
      : await response.text();
    const error = payload?.error;
    throw new ApiError(
      error?.message ?? `Request failed with status ${response.status}`,
      response.status,
      error?.code ?? 'request_failed',
      error?.details ?? payload?.detail ?? null,
    );
  }

  return response.blob();
}

export function isApiError(error) {
  return error instanceof ApiError;
}
