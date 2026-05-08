<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  remaining: number
  isRunning: boolean
  totalSeconds: number
}>()

const emit = defineEmits<{
  skip: []
}>()

const timeDisplay = computed(() => {
  const mins = Math.floor(props.remaining / 60)
  const secs = props.remaining % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
})

const progressPercent = computed(() => {
  if (props.totalSeconds <= 0) return 0
  return (props.remaining / props.totalSeconds) * 100
})
</script>

<template>
  <Transition name="slide-up">
    <div
      v-if="isRunning"
      class="fixed left-0 right-0 z-40 flex justify-center bottom-16 sm:bottom-0 pointer-events-none"
    >
      <div class="w-full max-w-2xl mx-2 bg-gray-900/90 backdrop-blur-sm text-white rounded-t-xl px-4 py-3 pointer-events-auto">
        <!-- Progress bar -->
        <div class="h-1 bg-gray-700 rounded-full mb-2 overflow-hidden">
          <div
            class="h-full bg-blue-400 rounded-full transition-all duration-1000 ease-linear"
            :style="{ width: `${progressPercent}%` }"
          />
        </div>

        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-400 uppercase tracking-wide font-medium">Rest</span>
          <span class="text-lg font-bold tabular-nums">{{ timeDisplay }}</span>
          <button
            class="px-3 py-1 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
            @click="emit('skip')"
          >
            Skip
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
