<script setup>
defineProps({
  error: {
    type: Object,
    required: true,
  },
  canRetry: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['retry'])
</script>

<template>
  <section class="error-panel" role="alert" aria-labelledby="scan-error-title">
    <div class="error-panel__icon" aria-hidden="true">!</div>
    <div>
      <p class="micro-label">{{ error.code || 'SCAN_ERROR' }}</p>
      <h2 id="scan-error-title">We couldn’t finish that scan</h2>
      <p>{{ error.message }}</p>
      <p v-if="error.request_id" class="request-id">
        Request ID: <code>{{ error.request_id }}</code>
      </p>
      <button
        v-if="canRetry"
        type="button"
        class="button button--dark"
        data-testid="error-retry"
        @click="$emit('retry')"
      >
        Try again
      </button>
    </div>
  </section>
</template>
