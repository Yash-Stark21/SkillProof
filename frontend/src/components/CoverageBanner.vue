<script setup>
import { computed } from 'vue'

const props = defineProps({
  coverage: {
    type: Object,
    required: true,
  },
})

const reasonLabels = {
  github_tree_truncated: 'GitHub returned a truncated file tree',
  request_limit_reached: 'The GitHub request limit was reached',
  tree_entry_limit_reached: 'The tree-entry limit was reached',
  file_count_limit_reached: 'The eligible-file count limit was reached',
  total_byte_limit_reached: 'The total inspection byte limit was reached',
  eligible_file_too_large: 'At least one eligible file was too large to inspect',
  eligible_file_fetch_failed: 'At least one eligible file could not be fetched',
  github_rate_limit_reached: 'GitHub rate-limited the scan',
  upstream_timeout_after_partial_result: 'The upstream request timed out after partial results',
}

const isPartial = computed(() => props.coverage.state === 'partial')
const isComplete = computed(() => props.coverage.state === 'complete')
const isUnknown = computed(() => !isPartial.value && !isComplete.value)

function reasonLabel(reason) {
  return reasonLabels[reason] || String(reason).replaceAll('_', ' ')
}
</script>

<template>
  <section
    class="coverage-banner"
    :class="{
      'coverage-banner--partial': isPartial,
      'coverage-banner--complete': isComplete,
      'coverage-banner--unknown': isUnknown,
    }"
    :aria-label="
      isPartial ? 'Partial coverage warning' : isComplete ? 'Complete coverage' : 'Unknown coverage'
    "
  >
    <div class="coverage-banner__icon" aria-hidden="true">
      {{ isPartial ? '!' : isComplete ? '✓' : '?' }}
    </div>
    <div class="coverage-banner__body">
      <div class="coverage-banner__heading">
        <div>
          <p class="micro-label">Coverage</p>
          <h2>
            {{ isPartial ? 'Partial coverage' : isComplete ? 'Complete coverage' : 'Unknown coverage' }}
          </h2>
        </div>
        <span class="coverage-state">{{ coverage.state }}</span>
      </div>

      <template v-if="isPartial">
        <p>
          Results are usable, but some eligible files were not inspected. Unobserved skills are
          not labeled missing.
        </p>
        <ul class="coverage-reasons">
          <li v-for="reason in coverage.reasons || []" :key="reason">
            <span>{{ reasonLabel(reason) }}</span>
            <code>{{ reason }}</code>
          </li>
        </ul>
      </template>
      <p v-else-if="isComplete">
        Every eligible file within the published scan policy was inspected for this commit.
      </p>
      <p v-else>
        The API returned a newer coverage state, “{{ coverage.state }}”. Findings remain
        inspectable, but SkillProof will not infer what that state means.
      </p>

      <dl class="coverage-stats">
        <div>
          <dt>Discovered</dt>
          <dd>{{ coverage.files_discovered ?? '—' }}</dd>
        </div>
        <div>
          <dt>Inspected</dt>
          <dd>{{ coverage.files_inspected ?? '—' }}</dd>
        </div>
        <div>
          <dt>Policy-skipped</dt>
          <dd>{{ coverage.files_skipped_by_policy ?? '—' }}</dd>
        </div>
      </dl>
    </div>
  </section>
</template>
