import { computed, onScopeDispose, ref } from 'vue'
import * as scanApi from '../services/scanApi'
import { createDemoResult } from '../data/demoScan'

const TERMINAL_STATUSES = new Set(['completed', 'failed'])

function safeError(error) {
  if (error instanceof scanApi.ApiError) {
    return {
      code: error.code,
      message: error.message,
      request_id: error.requestId,
    }
  }

  return {
    code: 'UNEXPECTED_ERROR',
    message: 'Something unexpected interrupted the scan. Please try again.',
    request_id: null,
  }
}

export function useRepositoryScan() {
  const repositoryUrl = ref('')
  const scan = ref(null)
  const evidence = ref([])
  const selectedEvidenceId = ref(null)
  const error = ref(null)
  const retryStage = ref(null)
  const isSubmitting = ref(false)
  const isLoadingEvidence = ref(false)
  const source = ref(null)

  let activeRun = 0
  let pollTimer = null

  const selectedEvidence = computed(
    () => evidence.value.find((item) => item.id === selectedEvidenceId.value) || null,
  )

  const isActive = computed(
    () =>
      !error.value &&
      (isSubmitting.value ||
        (scan.value && !TERMINAL_STATUSES.has(scan.value.status)) ||
        isLoadingEvidence.value),
  )

  const hasResult = computed(() => Boolean(scan.value || error.value))

  function clearPoll() {
    if (pollTimer !== null) {
      window.clearTimeout(pollTimer)
      pollTimer = null
    }
  }

  function beginRun() {
    activeRun += 1
    clearPoll()
    return activeRun
  }

  function resetResult() {
    scan.value = null
    evidence.value = []
    selectedEvidenceId.value = null
    error.value = null
    retryStage.value = null
    isLoadingEvidence.value = false
  }

  async function loadEvidence(scanId, run) {
    isLoadingEvidence.value = true
    const allEvidence = []
    const seenCursors = new Set()
    let cursor = null

    try {
      do {
        const response = await scanApi.getEvidence(scanId, cursor)
        if (run !== activeRun) return

        const pageData = Array.isArray(response.data?.data) ? response.data.data : []
        allEvidence.push(...pageData)
        cursor = response.data?.page?.next_cursor || null

        if (cursor && seenCursors.has(cursor)) {
          throw new Error('Repeated evidence cursor')
        }
        if (cursor) seenCursors.add(cursor)
      } while (cursor)

      evidence.value = allEvidence
      selectedEvidenceId.value = allEvidence[0]?.id || null
    } catch (requestError) {
      if (run === activeRun) {
        error.value = safeError(requestError)
        retryStage.value = 'evidence'
      }
    } finally {
      if (run === activeRun) isLoadingEvidence.value = false
    }
  }

  async function pollScan(scanId, run) {
    try {
      const response = await scanApi.getScan(scanId)
      if (run !== activeRun) return
      await acceptScanResponse(response, run)
    } catch (requestError) {
      if (run === activeRun) {
        error.value = safeError(requestError)
        retryStage.value = 'poll'
      }
    }
  }

  function schedulePoll(scanId, retryAfterMs, run) {
    clearPoll()
    pollTimer = window.setTimeout(() => pollScan(scanId, run), retryAfterMs)
  }

  async function acceptScanResponse(response, run) {
    scan.value = response.data

    if (response.data?.status === 'failed') {
      const embeddedError = response.data.error
      error.value = {
        code: embeddedError?.code || 'SCAN_FAILED',
        message:
          embeddedError?.message || 'The repository scan could not be completed. Please try again.',
        request_id: response.requestId,
      }
      retryStage.value = 'submit'
      return
    }

    if (response.data?.status === 'completed') {
      await loadEvidence(response.data.id, run)
      return
    }

    schedulePoll(response.data.id, response.retryAfterMs, run)
  }

  async function submitScan() {
    const run = beginRun()
    resetResult()
    source.value = 'live'
    isSubmitting.value = true

    try {
      const response = await scanApi.startScan(repositoryUrl.value.trim())
      if (run !== activeRun) return
      await acceptScanResponse(response, run)
    } catch (requestError) {
      if (run === activeRun) {
        error.value = safeError(requestError)
        retryStage.value = 'submit'
      }
    } finally {
      if (run === activeRun) isSubmitting.value = false
    }
  }

  function showDemo(coverageState) {
    beginRun()
    resetResult()
    const demo = createDemoResult(coverageState)
    scan.value = demo.scan
    evidence.value = demo.evidence
    selectedEvidenceId.value = demo.evidence[0]?.id || null
    source.value = 'demo'
  }

  function selectEvidence(id) {
    selectedEvidenceId.value = id
  }

  async function retryLastAction() {
    const stage = retryStage.value

    if (!stage || stage === 'submit' || !scan.value?.id) {
      await submitScan()
      return
    }

    error.value = null
    retryStage.value = null
    const run = activeRun

    if (stage === 'evidence') {
      await loadEvidence(scan.value.id, run)
      return
    }

    await pollScan(scan.value.id, run)
  }

  onScopeDispose(() => {
    activeRun += 1
    clearPoll()
  })

  return {
    repositoryUrl,
    scan,
    evidence,
    selectedEvidence,
    error,
    isActive,
    isSubmitting,
    isLoadingEvidence,
    hasResult,
    source,
    submitScan,
    showDemo,
    selectEvidence,
    retryLastAction,
  }
}
