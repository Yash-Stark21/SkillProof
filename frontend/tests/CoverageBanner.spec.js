import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CoverageBanner from '../src/components/CoverageBanner.vue'
import EvidenceList from '../src/components/EvidenceList.vue'

describe('CoverageBanner', () => {
  it('keeps an unknown API enum visible without treating it as complete', () => {
    const wrapper = mount(CoverageBanner, {
      props: {
        coverage: {
          state: 'future_state',
          reasons: [],
          files_discovered: 4,
          files_inspected: 2,
          files_skipped_by_policy: 1,
        },
      },
    })

    expect(wrapper.text()).toContain('Unknown coverage')
    expect(wrapper.text()).toContain('future_state')
    expect(wrapper.text()).toContain('will not infer what that state means')
    expect(wrapper.text()).not.toContain('Every eligible file')
  })
})

describe('EvidenceList', () => {
  it('does not assert absence when the coverage enum is unknown', () => {
    const wrapper = mount(EvidenceList, {
      props: {
        evidence: [],
        coverageState: 'future_state',
      },
    })

    expect(wrapper.text()).toContain('Coverage is not confirmed complete')
    expect(wrapper.text()).not.toContain('No detector evidence was found')
  })
})
