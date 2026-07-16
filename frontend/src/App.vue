<script setup>
import { computed } from 'vue'
import CoverageBanner from './components/CoverageBanner.vue'
import ErrorPanel from './components/ErrorPanel.vue'
import EvidenceDetail from './components/EvidenceDetail.vue'
import EvidenceList from './components/EvidenceList.vue'
import RepositoryForm from './components/RepositoryForm.vue'
import ScanProgress from './components/ScanProgress.vue'
import { useRepositoryScan } from './composables/useRepositoryScan'

const {
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
} = useRepositoryScan()

const resultAnnouncement = computed(() => {
  if (scan.value?.status !== 'completed' || isLoadingEvidence.value || error.value) return ''

  const coverage = scan.value.coverage?.state || 'unknown'
  const findingLabel = evidence.value.length === 1 ? 'finding' : 'findings'
  return `Scan complete with ${evidence.value.length} ${findingLabel}. Coverage: ${coverage}.`
})
</script>

<template>
  <a class="skip-link" href="#main-content">Skip to main content</a>

  <header class="site-header">
    <a class="brand" href="#main-content" aria-label="SkillProof home">
      <span class="brand-mark" aria-hidden="true">
        <span></span><span></span><span></span>
      </span>
      <span>Skill<span>Proof</span></span>
    </a>
    <div class="header-meta">
      <span class="header-status"><span aria-hidden="true"></span> Evidence contract 0.1</span>
      <span class="header-separator" aria-hidden="true"></span>
      <span>Public repos</span>
    </div>
  </header>

  <main id="main-content">
    <p class="sr-only" aria-live="polite" aria-atomic="true">{{ resultAnnouncement }}</p>
    <section class="hero" :class="{ 'hero--compact': hasResult }">
      <div class="hero-grid page-shell">
        <div class="hero-copy">
          <p class="eyebrow"><span aria-hidden="true"></span> Evidence, not guesswork</p>
          <h1>Turn public work into <em>proof you can inspect.</em></h1>
          <p class="hero-intro">
            SkillProof traces detected skills back to an exact commit, file, line, and redacted
            excerpt—so every claim starts with evidence.
          </p>
          <ul class="hero-points" aria-label="SkillProof safeguards">
            <li><span aria-hidden="true">✓</span> Read-only inspection</li>
            <li><span aria-hidden="true">✓</span> Commit-pinned results</li>
            <li><span aria-hidden="true">✓</span> No repository code execution</li>
          </ul>
        </div>

        <RepositoryForm
          v-model="repositoryUrl"
          :busy="isActive"
          @submit="submitScan"
          @demo="showDemo"
        />
      </div>
      <div class="hero-grid-pattern" aria-hidden="true"></div>
    </section>

    <section v-if="hasResult" class="results-section page-shell">
      <div v-if="scan" class="result-context">
        <div>
          <div class="result-context__label">
            <span v-if="source === 'demo'" class="demo-badge">Sample data</span>
            <span>{{ scan.repository?.provider || 'Repository' }}</span>
          </div>
          <h2>{{ scan.repository?.owner }}/{{ scan.repository?.name }}</h2>
        </div>
        <dl v-if="scan.commit_sha" class="scan-summary">
          <div>
            <dt>Commit</dt>
            <dd :title="scan.commit_sha">{{ scan.commit_sha.slice(0, 9) }}</dd>
          </div>
          <div>
            <dt>Detector</dt>
            <dd>v{{ scan.detector_version || 'unknown' }}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd class="capitalize">{{ scan.status }}</dd>
          </div>
        </dl>
      </div>

      <ErrorPanel
        v-if="error"
        :error="error"
        :can-retry="Boolean(repositoryUrl) && !isActive"
        @retry="retryLastAction"
      />

      <ScanProgress
        v-else-if="!scan || scan.status !== 'completed' || isLoadingEvidence"
        :scan="scan"
        :submitting="isSubmitting"
        :loading-evidence="isLoadingEvidence"
      />

      <template v-else>
        <CoverageBanner v-if="scan.coverage" :coverage="scan.coverage" />

        <div class="evidence-workspace">
          <EvidenceList
            :evidence="evidence"
            :selected-id="selectedEvidence?.id || null"
            :coverage-state="scan.coverage?.state || 'complete'"
            @select="selectEvidence"
          />
          <EvidenceDetail :item="selectedEvidence" />
        </div>
      </template>
    </section>

    <section v-else class="principles-section page-shell" aria-labelledby="principles-title">
      <div class="section-heading">
        <p class="micro-label">A reviewable trail</p>
        <h2 id="principles-title">From repository to evidence in three clear steps</h2>
      </div>
      <ol class="principle-grid">
        <li>
          <span class="principle-number">01</span>
          <div class="principle-icon" aria-hidden="true">↗</div>
          <h3>Pin the source</h3>
          <p>A public GitHub URL resolves to one immutable commit before inspection begins.</p>
        </li>
        <li>
          <span class="principle-number">02</span>
          <div class="principle-icon" aria-hidden="true">⌁</div>
          <h3>Detect safely</h3>
          <p>Versioned rules inspect eligible text files without installing or running the code.</p>
        </li>
        <li>
          <span class="principle-number">03</span>
          <div class="principle-icon" aria-hidden="true">✓</div>
          <h3>Review the proof</h3>
          <p>Every result exposes its file, lines, confidence, coverage, and redacted excerpt.</p>
        </li>
      </ol>
    </section>
  </main>

  <footer class="site-footer page-shell">
    <p><strong>No evidence, no claim.</strong> Built for honest, inspectable portfolios.</p>
    <p>SkillProof · Sprint 1</p>
  </footer>
</template>
