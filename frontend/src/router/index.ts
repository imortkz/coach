import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      redirect: '/exercises',
    },
    {
      path: '/exercises',
      name: 'exercises',
      component: () => import('../views/ExercisesView.vue'),
    },
    {
      path: '/programs/new',
      name: 'program-new',
      component: () => import('../views/ProgramEditView.vue'),
    },
    {
      path: '/programs/:id/edit',
      name: 'program-edit',
      component: () => import('../views/ProgramEditView.vue'),
    },
    {
      path: '/programs',
      name: 'programs',
      component: () => import('../views/ProgramsView.vue'),
    },
    {
      path: '/workout',
      name: 'workout',
      component: () => import('../views/WorkoutView.vue'),
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('../views/HistoryView.vue'),
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('../views/ReportView.vue'),
    },
    {
      path: '/exercises/:id/history',
      name: 'exercise-history',
      component: () => import('../views/ExerciseHistoryView.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Public routes (login page) are always accessible
  if (to.meta.public) return true

  // Dev mode: if no token, auto-acquire one silently
  const isDev = import.meta.env.DEV || import.meta.env.VITE_DEV_MODE === 'true'
  if (!auth.isAuthenticated && isDev) {
    await auth.devLogin()
  }

  // If still not authenticated, redirect to login
  if (!auth.isAuthenticated) {
    return { name: 'login' }
  }

  // Hydrate user info if missing
  if (!auth.user) {
    await auth.fetchMe()
  }

  // Load language preference before first view renders
  const settingsStore = useSettingsStore()
  await settingsStore.loadLanguage()

  return true
})

export default router
