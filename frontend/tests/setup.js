import { afterEach } from 'vitest'
import { config } from '@vue/test-utils'

config.global.renderStubDefaultSlot = true

afterEach(() => {
  document.body.innerHTML = ''
})
