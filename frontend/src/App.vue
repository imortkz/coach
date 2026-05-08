<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const navItems = [
  { to: '/exercises', label: 'exercises', icon: 'dumbbell' },
  { to: '/programs', label: 'programs', icon: 'clipboard' },
  { to: '/workout', label: 'workout', icon: 'play' },
  { to: '/history', label: 'history', icon: 'clock' },
  { to: '/settings', label: 'settings', icon: 'gear' },
] as const
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Desktop navbar -->
    <nav class="hidden md:block bg-white border-b border-gray-200">
      <div class="max-w-5xl mx-auto px-4">
        <div class="flex items-center justify-between h-14">
          <span class="text-lg font-bold text-gray-900">GymCoach</span>
          <div class="flex gap-1">
            <RouterLink
              v-for="item in navItems"
              :key="item.to"
              :to="item.to"
              class="px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
              active-class="!text-blue-600 !bg-blue-50"
            >
              {{ t('nav.' + item.label) }}
            </RouterLink>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-5xl mx-auto px-4 py-6 pb-20 md:pb-6">
      <RouterView />
    </main>

    <!-- Mobile bottom tab bar -->
    <nav class="fixed bottom-0 left-0 right-0 md:hidden bg-white border-t border-gray-200 z-50">
      <div class="flex items-center justify-around h-16">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex flex-col items-center justify-center gap-0.5 flex-1 py-2 text-gray-500 transition-colors"
          active-class="!text-blue-600"
        >
          <!-- Dumbbell icon -->
          <svg v-if="item.icon === 'dumbbell'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h2v4H3zM19 10h2v4h-2zM5 8h2v8H5zM17 8h2v8h-2zM7 11h10v2H7z" />
          </svg>
          <!-- Clipboard icon -->
          <svg v-else-if="item.icon === 'clipboard'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <!-- Play icon -->
          <svg v-else-if="item.icon === 'play'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <!-- Clock icon -->
          <svg v-else-if="item.icon === 'clock'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <!-- Gear icon -->
          <svg v-else-if="item.icon === 'gear'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span class="text-xs font-medium">{{ t('nav.' + item.label) }}</span>
        </RouterLink>
      </div>
    </nav>
  </div>
</template>
