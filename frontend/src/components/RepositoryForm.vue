<script setup>
defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  busy: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'submit', 'demo'])

function updateValue(event) {
  emit('update:modelValue', event.target.value)
}
</script>

<template>
  <div class="scan-card">
    <div class="scan-card__heading">
      <div>
        <p class="micro-label">Start with one repository</p>
        <h2>Inspect your public work</h2>
      </div>
      <span class="provider-pill"><span aria-hidden="true">●</span> GitHub</span>
    </div>

    <form class="repository-form" @submit.prevent="emit('submit')">
      <label for="repository-url">Public GitHub repository URL</label>
      <div class="repository-input-wrap">
        <span class="repository-input-icon" aria-hidden="true">↗</span>
        <input
          id="repository-url"
          :value="modelValue"
          type="url"
          inputmode="url"
          autocomplete="url"
          placeholder="https://github.com/you/project"
          pattern="https:\/\/github\.com\/[^\/]+\/[^\/#?]+\/?(?:\.git)?"
          aria-describedby="repository-help"
          required
          :disabled="busy"
          @input="updateValue"
        />
        <button
          class="button button--primary scan-submit"
          type="submit"
          :disabled="busy"
          data-testid="scan-submit"
        >
          <span v-if="busy" class="button-spinner" aria-hidden="true"></span>
          {{ busy ? 'Scanning…' : 'Scan repository' }}
        </button>
      </div>
      <p id="repository-help" class="form-help">
        Public repositories only. SkillProof never executes repository code.
      </p>
    </form>

    <div class="demo-row" aria-label="Demo results">
      <span>Backend not running?</span>
      <button
        type="button"
        class="text-button"
        data-testid="demo-complete"
        :disabled="busy"
        @click="emit('demo', 'complete')"
      >
        Complete example
      </button>
      <span aria-hidden="true">·</span>
      <button
        type="button"
        class="text-button"
        data-testid="demo-partial"
        :disabled="busy"
        @click="emit('demo', 'partial')"
      >
        Partial example
      </button>
    </div>
  </div>
</template>
