import { onMounted, onBeforeUnmount, type Ref } from 'vue'

export function useSwipeLeft(
  elRef: Ref<HTMLElement | null>,
  onSwipe: () => void,
  threshold: number = 60
) {
  let startX = 0
  let startY = 0

  function handleTouchStart(e: TouchEvent) {
    const touch = e.touches[0]
    startX = touch.clientX
    startY = touch.clientY
  }

  function handleTouchEnd(e: TouchEvent) {
    const touch = e.changedTouches[0]
    const dx = startX - touch.clientX
    const dy = Math.abs(startY - touch.clientY)
    // Only trigger on horizontal swipes (left) where horizontal > vertical
    if (dx > threshold && dx > dy) {
      onSwipe()
    }
  }

  onMounted(() => {
    const el = elRef.value
    if (!el) return
    el.addEventListener('touchstart', handleTouchStart, { passive: true })
    el.addEventListener('touchend', handleTouchEnd, { passive: true })
  })

  onBeforeUnmount(() => {
    const el = elRef.value
    if (!el) return
    el.removeEventListener('touchstart', handleTouchStart)
    el.removeEventListener('touchend', handleTouchEnd)
  })
}
