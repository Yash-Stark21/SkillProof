<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    default: null,
  },
})

const skillName = computed(() =>
  String(props.item?.canonical_skill_id || '')
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' '),
)

const lineLabel = computed(() => {
  if (!props.item) return ''
  return props.item.start_line === props.item.end_line
    ? `Line ${props.item.start_line}`
    : `Lines ${props.item.start_line}–${props.item.end_line}`
})
</script>

<template>
  <article v-if="item" class="evidence-detail" aria-labelledby="evidence-detail-title">
    <div class="detail-heading">
      <div>
        <p class="micro-label">Selected finding</p>
        <h2 id="evidence-detail-title">{{ skillName }}</h2>
      </div>
      <span class="eligibility-badge" :class="{ 'is-ineligible': !item.claim_eligible }">
        <span aria-hidden="true">{{ item.claim_eligible ? '✓' : '·' }}</span>
        {{ item.claim_eligible ? 'Claim eligible' : 'Supporting evidence' }}
      </span>
    </div>

    <p class="authority-note">
      Eligibility is the detector’s persisted decision for this evidence item.
    </p>

    <dl class="detail-grid">
      <div class="detail-grid__wide">
        <dt>Source file</dt>
        <dd>{{ item.path }}</dd>
      </div>
      <div>
        <dt>Location</dt>
        <dd>{{ lineLabel }}</dd>
      </div>
      <div>
        <dt>Confidence</dt>
        <dd class="capitalize">{{ item.confidence }}</dd>
      </div>
      <div>
        <dt>Evidence kind</dt>
        <dd class="capitalize">{{ item.evidence_kind.replaceAll('_', ' ') }}</dd>
      </div>
      <div>
        <dt>Coverage</dt>
        <dd class="capitalize">{{ item.coverage_state }}</dd>
      </div>
    </dl>

    <section class="excerpt-section" aria-labelledby="excerpt-title">
      <div class="excerpt-heading">
        <h3 id="excerpt-title">Redacted excerpt</h3>
        <span>{{ lineLabel }}</span>
      </div>
      <pre><code data-testid="evidence-excerpt" v-text="item.redacted_excerpt"></code></pre>
      <p>Rendered as text from the API’s redacted excerpt. Repository code is never executed.</p>
    </section>

    <details class="provenance">
      <summary>View provenance</summary>
      <dl>
        <div>
          <dt>Rule</dt>
          <dd>{{ item.rule_id }}</dd>
        </div>
        <div>
          <dt>Repository</dt>
          <dd>{{ item.repository }}</dd>
        </div>
        <div>
          <dt>Commit SHA</dt>
          <dd>{{ item.commit_sha }}</dd>
        </div>
        <div>
          <dt>Content hash</dt>
          <dd>{{ item.content_hash }}</dd>
        </div>
        <div>
          <dt>Detector</dt>
          <dd>{{ item.detector_version }}</dd>
        </div>
        <div>
          <dt>Contract</dt>
          <dd>{{ item.contract_version }}</dd>
        </div>
      </dl>
    </details>
  </article>

  <div v-else class="detail-placeholder">
    <span aria-hidden="true">↖</span>
    <p>Select a finding to inspect its exact source evidence.</p>
  </div>
</template>
