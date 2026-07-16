import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import EvidenceDetail from '../src/components/EvidenceDetail.vue'

describe('EvidenceDetail', () => {
  it('renders redacted excerpts strictly as text', () => {
    const maliciousLookingExcerpt = '<img src=x onerror="alert(1)"> const safe = true'
    const wrapper = mount(EvidenceDetail, {
      props: {
        item: {
          id: 'evidence-safe-rendering',
          contract_version: '0.1',
          canonical_skill_id: 'javascript',
          rule_id: 'javascript.syntax.const',
          detector_version: '0.1.0',
          repository: 'github:octocat/example',
          commit_sha: '0123456789abcdef0123456789abcdef01234567',
          path: 'src/example.js',
          content_hash:
            'ef12e4c75a1dbc72c641ca357a9a983339b5557dc0fb14f17c58366e54231c0c',
          start_line: 1,
          end_line: 1,
          redacted_excerpt: maliciousLookingExcerpt,
          evidence_kind: 'language_syntax',
          confidence: 'medium',
          coverage_state: 'partial',
          claim_eligible: false,
        },
      },
    })

    expect(wrapper.get('[data-testid="evidence-excerpt"]').text()).toBe(maliciousLookingExcerpt)
    expect(wrapper.find('.excerpt-section img').exists()).toBe(false)
    expect(wrapper.text()).toContain('Supporting evidence')
  })
})
