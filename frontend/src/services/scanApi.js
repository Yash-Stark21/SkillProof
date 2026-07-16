const DEFAULT_RETRY_AFTER_MS = 2000
const MIN_RETRY_AFTER_MS = 100
const MAX_RETRY_AFTER_MS = 60000

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '')

const FALLBACK_MESSAGES = {
  400: 'The request could not be understood. Check the repository URL and try again.',
  404: 'The requested scan could not be found.',
  409: 'The scan is not ready for that action yet.',
  422: 'Enter a public github.com repository URL.',
  429: 'Too many requests were made. Wait a moment and try again.',
  500: 'SkillProof could not complete the request.',
  503: 'SkillProof is not ready yet. Try again shortly.',
}

export class ApiError extends Error {
  constructor({ code, message, requestId, status }) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.requestId = requestId
    this.status = status
  }
}

function parseRetryAfter(value) {
  if (!value) return DEFAULT_RETRY_AFTER_MS

  const seconds = Number(value)
  let retryAfterMs

  if (Number.isFinite(seconds)) {
    retryAfterMs = seconds * 1000
  } else {
    const retryDate = Date.parse(value)
    retryAfterMs = Number.isNaN(retryDate) ? DEFAULT_RETRY_AFTER_MS : retryDate - Date.now()
  }

  return Math.min(Math.max(retryAfterMs, MIN_RETRY_AFTER_MS), MAX_RETRY_AFTER_MS)
}

async function parseBody(response) {
  const text = await response.text()
  if (!text) return null

  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

async function request(path, options = {}) {
  let response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError({
      code: 'NETWORK_ERROR',
      message: 'We could not reach SkillProof. Check your connection and try again.',
      requestId: null,
      status: 0,
    })
  }

  const body = await parseBody(response)
  const requestId = body?.request_id || response.headers.get('X-Request-ID') || null

  if (!response.ok) {
    throw new ApiError({
      code: typeof body?.code === 'string' ? body.code : 'REQUEST_FAILED',
      message:
        typeof body?.message === 'string'
          ? body.message
          : FALLBACK_MESSAGES[response.status] || 'The request could not be completed.',
      requestId,
      status: response.status,
    })
  }

  return {
    data: body,
    requestId,
    retryAfterMs: parseRetryAfter(response.headers.get('Retry-After')),
  }
}

export function startScan(repositoryUrl) {
  return request('/scans', {
    method: 'POST',
    body: JSON.stringify({ repository_url: repositoryUrl }),
  })
}

export function getScan(scanId) {
  return request(`/scans/${encodeURIComponent(scanId)}`)
}

export function getEvidence(scanId, cursor = null) {
  const query = new URLSearchParams({ limit: '100' })
  if (cursor) query.set('cursor', cursor)

  return request(`/scans/${encodeURIComponent(scanId)}/evidence?${query.toString()}`)
}
