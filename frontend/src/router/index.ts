import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', redirect: '/grade' },
        { path: 'grade', name: 'grade', component: () => import('@/views/GradeView.vue'), meta: { title: 'AI 批改', icon: 'Camera' } },
        { path: 'errors', name: 'errors', component: () => import('@/views/ErrorsView.vue'), meta: { title: '错题本', icon: 'Notebook' } },
        { path: 'analytics', name: 'analytics', component: () => import('@/views/AnalyticsView.vue'), meta: { title: '学情分析', icon: 'DataAnalysis' } },
        { path: 'tutor', name: 'tutor', component: () => import('@/views/TutorView.vue'), meta: { title: 'AI 辅导', icon: 'ChatDotRound' } },
        { path: 'recommend', name: 'recommend', component: () => import('@/views/RecommendView.vue'), meta: { title: '智能推题', icon: 'Aim' } },
        { path: 'review', name: 'review', component: () => import('@/views/ReviewView.vue'), meta: { title: '复习调度', icon: 'AlarmClock' } },
      ],
    },
  ],
})

export default router
