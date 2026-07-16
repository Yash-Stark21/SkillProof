<script setup>
defineProps({
  evidence: {
    type: Array,
    required: true,
  },
  selectedId: {
    type: String,
    default: null,
  },
  coverageState: {
    type: String,
    default: 'complete',
  },
})

const emit = defineEmits(['select'])

function skillName(skillId) {
  return String(skillId)
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function lineLabel(item) {
  return item.start_line === item.end_line
    ? `Line ${item.start_line}`
    : `Lines ${item.start_line}–${item.end_line}`
}
</script>

<template>
  <section class="evidence-list-panel" aria-labelledby="evidence-list-title">
    <div class="panel-heading">
      <div>
        <p class="micro-label">Evidence ledger</p>
        <h2 id="evidence-list-title">{{ evidence.length }} findings</h2>
      </div>
      <span class="panel-count" aria-hidden="true">{{ evidence.length }}</span>
    </div>

    <ul v-if="evidence.length" class="evidence-list">
      <li v-for="item in evidence" :key="item.id">
        <button
          type="button"
          class="evidence-row"
          :class="{ 'is-selected': item.id === selectedId }"
          :aria-pressed="item.id === selectedId"
          @click="emit('select', item.id)"
        >
          <span class="evidence-row__topline">
            <span class="skill-monogram" aria-hidden="true">
              {{ String(item.canonical_skill_id).charAt(0).toUpperCase() }}
            </span>
            <span class="evidence-row__title">
              <strong>{{ skillName(item.canonical_skill_id) }}</strong>
              <span>{{ item.evidence_kind.replaceAll('_', ' ') }}</span>
            </span>
            <span class="confidence-badge" :data-confidence="item.confidence">
              {{ item.confidence }}
            </span>
          </span>
          <span class="evidence-row__path">{{ item.path }}</span>
          <span class="evidence-row__footer">
            <span>{{ lineLabel(item) }}</span>
            <span>{{ item.claim_eligible ? 'Claim eligible' : 'Supporting only' }}</span>
            <span aria-hidden="true">→</span>
          </span>
        </button>
      </li>
    </ul>

    <div v-else class="empty-evidence">
      <span aria-hidden="true">∅</span>
      <h3>No evidence found</h3>
      <p v-if="coverageState !== 'complete'">
        None was observed in inspected files. Coverage is not confirmed complete, so other files
        may contain evidence.
      </p>
      <p v-else>No detector evidence was found in the eligible files for this commit.</p>
    </div>
  </section>
</template>
