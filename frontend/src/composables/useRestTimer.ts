import { ref, onScopeDispose } from 'vue'

export function useRestTimer(defaultSeconds: number = 120) {
  const remaining = ref(0)
  const isRunning = ref(false)
  let endTime: number | null = null
  let intervalId: ReturnType<typeof setInterval> | null = null
  let permissionRequested = false

  function start(seconds?: number) {
    stop()
    const duration = seconds ?? defaultSeconds
    endTime = Date.now() + duration * 1000
    remaining.value = duration
    isRunning.value = true

    // Request notification permission on first use
    if (!permissionRequested && typeof Notification !== 'undefined' && Notification.permission === 'default') {
      permissionRequested = true
      Notification.requestPermission()
    }

    intervalId = setInterval(() => {
      if (endTime === null) return
      const left = Math.ceil((endTime - Date.now()) / 1000)
      if (left <= 0) {
        stop()
        notifyRestComplete()
      } else {
        remaining.value = left
      }
    }, 1000)
  }

  function skip() {
    stop()
  }

  function stop() {
    if (intervalId !== null) {
      clearInterval(intervalId)
      intervalId = null
    }
    isRunning.value = false
    remaining.value = 0
    endTime = null
  }

  function notifyRestComplete() {
    if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
      new Notification('Rest Complete', { body: 'Time for next set!' })
    }
  }

  function handleVisibilityChange() {
    if (document.visibilityState !== 'visible' || endTime === null) return
    if (endTime <= Date.now()) {
      stop()
      notifyRestComplete()
    } else {
      remaining.value = Math.ceil((endTime - Date.now()) / 1000)
    }
  }

  document.addEventListener('visibilitychange', handleVisibilityChange)

  onScopeDispose(() => {
    stop()
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  })

  return { remaining, isRunning, start, skip }
}
