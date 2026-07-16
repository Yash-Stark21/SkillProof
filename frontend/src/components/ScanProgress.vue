<script setup>
import { computed } from 'vue'

const props = defineProps({
  scan: {
    type: Object,
    default: null,
  },
  submitting: {
    type: Boolean,
    default: false,
  },
  loadingEvidence: {
    type: Boolean,
    default: false,
  },
})

const stages = [
  { phase: 'queued', label: 'Queued' },
  { phase: 'resolving_repository', label: 'Resolve' },
  { phase: 'enumerating_tree', label: 'Inventory' },
  { phase: 'fetching_files', label: 'Inspect' },
  { phase: 'detecting', label: 'Detect' },
  { phase: 'persisting', label: 'Save' },
  { phase: 'complete', label: 'Complete' },
]

const currentPhase = computed(() => {
  if (props.loadingEvidence) return 'complete'
  if (props.submitting && !props.scan) return 'queued'
  return props.scan?.phase || props.scan?.status || 'queued'
})

const currentIndex = computed(() => {
  const index = stages.findIndex((stage) => stage.phase === currentPhase.value)
  return index === -1 ? 0 : index
})

const readablePhase = computed(() => {
  if (props.loadingEvidence) return 'Loading the evidence ledger'
  const match = stages.find((stage) => stage.phase === currentPhase.value)
  if (match) {
    const messages = {
      queued: 'Waiting for a scan slot',
      resolving_repository: 'Resolving repository and commit',
      enumerating_tree: 'Building a safe file inventory',
      fetching_files: 'Inspecting eligible files',
      detecting: 'Detecting evidence with versioned rules',
      persisting: 'Saving the evidence ledger',
      complete: 'Scan complete',
    }
    return messages[match.phase]
  }

  return `Scan status: ${String(currentPhase.value).replaceAll('_', ' ')}`
})
</script>

<template>
  <section class="progress-card" aria-live="polite" aria-atomic="true">
    <div class="progress-card__copy">
      <span class="status-orbit" aria-hidden="true"><span></span></span>
      <div>
        <p class="micro-label">Repository scan in progress</p>
        <h2>{{ readablePhase }}</h2>
        <p>Results stay pinned to one commit so every finding remains reviewable.</p>
      </div>
    </div>

    <ol class="progress-steps" aria-label="Scan progress">
      <li
        v-for="(stage, index) in stages"
        :key="stage.phase"
        :class="{
          'is-complete': index < currentIndex,
          'is-current': index === currentIndex,
        }"
        :aria-current="index === currentIndex ? 'step' : undefined"
      >
        <span class="progress-steps__marker" aria-hidden="true">
          {{ index < currentIndex ? '✓' : index + 1 }}
        </span>
        <span>{{ stage.label }}</span>
      </li>
    </ol>
  </section>
</template>
