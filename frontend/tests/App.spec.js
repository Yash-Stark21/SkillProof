import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../src/App.vue'

const scanBase = {
  id: '9ec0aa44-ebac-471e-bbeb-82f34ef0fecd',
  repository: {
    provider: 'github',
    identity: 'github:octocat/example',
    owner: 'octocat',
    name: 'example',
    url: 'https://github.com/octocat/example',
  },
  commit_sha: null,
  detector_version: '0.1.0',
  coverage: null,
  error: null,
}

const completedScan = {
  ...scanBase,
  status: 'completed',
  phase: 'complete',
  commit_sha: '0123456789abcdef0123456789abcdef01234567',
  coverage: {
    state: 'complete',
    reasons: [],
    files_discovered: 8,
    files_inspected: 5,
    files_skipped_by_policy: 3,
  },
}

const evidenceItem = {
  id: 'evidence-1',
  contract_version: '0.1',
  canonical_skill_id: 'fastapi',
  rule_id: 'python.fastapi.route_decorator',
  detector_version: '0.1.0',
  repository: 'github:octocat/example',
  commit_sha: completedScan.commit_sha,
  path: 'app/main.py',
  content_hash: 'ef12e4c75a1dbc72c641ca357a9a983339b5557dc0fb14f17c58366e54231c0c',
  start_line: 12,
  end_line: 14,
  redacted_excerpt: '@app.get("/health")\nasync def health():\n    return {"status": "ok"}',
  evidence_kind: 'route',
  confidence: 'high',
  coverage_state: 'complete',
  claim_eligible: true,
}

const secondEvidenceItem = {
  ...evidenceItem,
  id: 'evidence-2',
  canonical_skill_id: 'pytest',
  rule_id: 'python.pytest.test_function',
  path: 'tests/test_main.py',
  start_line: 8,
  end_line: 11,
  redacted_excerpt: 'def test_health(client):\n    assert client.get("/health").status_code == 200',
  evidence_kind: 'test',
}

function mockResponse(body, { status = 200, retryAfter = null, requestId = 'req_test' } = {}) {
  const normalizedHeaders = {
    'retry-after': retryAfter,
    'x-request-id': requestId,
  }

  return {
    ok: status >= 200 && status < 300,
    status,
    headers: {
      get(name) {
        return normalizedHeaders[name.toLowerCase()] ?? null
      },
    },
    text: () => Promise.resolve(body === null ? '' : JSON.stringify(body)),
  }
}

describe('repository scan journey', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    globalThis.fetch = vi.fn()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('submits once, honors Retry-After polling, and loads completed evidence', async () => {
    globalThis.fetch
      .mockResolvedValueOnce(
        mockResponse({ ...scanBase, status: 'queued', phase: 'queued' }, { status: 202, retryAfter: '0' }),
      )
      .mockResolvedValueOnce(
        mockResponse(
          { ...scanBase, status: 'running', phase: 'detecting' },
          { retryAfter: '0' },
        ),
      )
      .mockResolvedValueOnce(mockResponse(completedScan))
      .mockResolvedValueOnce(
        mockResponse({
          data: [evidenceItem],
          page: { next_cursor: 'cursor-2', limit: 100 },
          scan: { id: completedScan.id, status: 'completed', coverage: completedScan.coverage },
        }),
      )
      .mockResolvedValueOnce(
        mockResponse({
          data: [secondEvidenceItem],
          page: { next_cursor: null, limit: 100 },
          scan: { id: completedScan.id, status: 'completed', coverage: completedScan.coverage },
        }),
      )

    const wrapper = mount(App)
    await wrapper.find('#repository-url').setValue('https://github.com/octocat/example')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(globalThis.fetch).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('Waiting for a scan slot')
    expect(wrapper.get('[data-testid="scan-submit"]').attributes('disabled')).toBeDefined()

    await vi.advanceTimersByTimeAsync(100)
    await flushPromises()
    expect(wrapper.text()).toContain('Detecting evidence with versioned rules')

    await vi.advanceTimersByTimeAsync(100)
    await flushPromises()

    expect(globalThis.fetch).toHaveBeenCalledTimes(5)
    expect(wrapper.text()).toContain('Complete coverage')
    expect(wrapper.text()).toContain('Fastapi')
    expect(wrapper.text()).toContain('2 findings')
    expect(wrapper.text()).toContain('Scan complete with 2 findings. Coverage: complete.')
    expect(wrapper.text()).toContain('app/main.py')
    expect(wrapper.get('[data-testid="evidence-excerpt"]').text()).toContain('@app.get')
    expect(globalThis.fetch.mock.calls[4][0]).toContain('cursor=cursor-2')

    const postOptions = globalThis.fetch.mock.calls[0][1]
    expect(JSON.parse(postOptions.body)).toEqual({
      repository_url: 'https://github.com/octocat/example',
    })
  })

  it('makes partial coverage unmistakable without asserting missing skills', async () => {
    const wrapper = mount(App)
    await wrapper.get('[data-testid="demo-partial"]').trigger('click')

    expect(wrapper.text()).toContain('Sample data')
    expect(wrapper.text()).toContain('Partial coverage')
    expect(wrapper.text()).toContain('Unobserved skills are not labeled missing')
    expect(wrapper.text()).toContain('file_count_limit_reached')
    expect(wrapper.text()).toContain('eligible_file_too_large')
    expect(globalThis.fetch).not.toHaveBeenCalled()
  })

  it('shows only the safe API error and its request ID', async () => {
    globalThis.fetch.mockResolvedValueOnce(
      mockResponse(
        {
          code: 'VALIDATION_ERROR',
          message: 'Only public github.com repository URLs are supported.',
          details: { internal_debug: 'must not be rendered' },
          request_id: 'req_01SAFE',
        },
        { status: 422 },
      ),
    )

    const wrapper = mount(App)
    await wrapper.find('#repository-url').setValue('https://github.com/octocat/example')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('Only public github.com repository URLs are supported.')
    expect(wrapper.text()).toContain('req_01SAFE')
    expect(wrapper.text()).not.toContain('must not be rendered')
  })

  it('re-enables retry when polling fails after a scan was queued', async () => {
    globalThis.fetch
      .mockResolvedValueOnce(
        mockResponse(
          { ...scanBase, status: 'queued', phase: 'queued' },
          { status: 202, retryAfter: '0' },
        ),
      )
      .mockResolvedValueOnce(
        mockResponse(
          {
            code: 'NOT_READY',
            message: 'SkillProof is still getting ready. Try again shortly.',
            request_id: 'req_poll_retry',
          },
          { status: 503 },
        ),
      )
      .mockResolvedValueOnce(
        mockResponse(
          { ...scanBase, status: 'running', phase: 'detecting' },
          { retryAfter: '10' },
        ),
      )

    const wrapper = mount(App)
    await wrapper.find('#repository-url').setValue('https://github.com/octocat/example')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    await vi.advanceTimersByTimeAsync(100)
    await flushPromises()

    expect(wrapper.text()).toContain('req_poll_retry')
    expect(wrapper.text()).toContain('Try again')
    expect(wrapper.get('[data-testid="scan-submit"]').attributes('disabled')).toBeUndefined()

    await wrapper.get('[data-testid="error-retry"]').trigger('click')
    await flushPromises()

    expect(globalThis.fetch).toHaveBeenCalledTimes(3)
    expect(globalThis.fetch.mock.calls[2][0]).toContain(`/scans/${scanBase.id}`)
    expect(globalThis.fetch.mock.calls[2][1]?.method).not.toBe('POST')
    expect(wrapper.text()).toContain('Detecting evidence with versioned rules')
  })
})
