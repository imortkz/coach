<script setup lang="ts">
defineProps<{
  message: string
  visible: boolean
}>()

const emit = defineEmits<{
  undo: []
}>()
</script>

<template>
  <Transition name="slide-up-toast">
    <div
      v-if="visible"
      class="fixed left-0 right-0 z-50 flex justify-center bottom-20 sm:bottom-4"
    >
      <div class="mx-4 bg-gray-800 text-white rounded-lg shadow-lg px-4 py-3 flex items-center gap-3 max-w-md">
        <span class="text-sm flex-1">{{ message }}</span>
        <button
          class="text-sm font-bold text-blue-400 hover:text-blue-300 transition-colors uppercase tracking-wide"
          @click="emit('undo')"
        >
          Undo
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.slide-up-toast-enter-active,
.slide-up-toast-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.slide-up-toast-enter-from,
.slide-up-toast-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
