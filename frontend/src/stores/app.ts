import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'
import type { Health } from '@/types'

export const useAppStore = defineStore('app', () => {
  // 当前操作的学生标识，多个视图共享
  const studentId = ref(localStorage.getItem('edu_student_id') || 'stu_A')
  const health = ref<Health | null>(null)

  function setStudentId(id: string) {
    studentId.value = id || 'anonymous'
    localStorage.setItem('edu_student_id', studentId.value)
  }

  async function fetchHealth() {
    try {
      health.value = await api.health()
    } catch (e) {
      health.value = null
    }
    return health.value
  }

  return { studentId, health, setStudentId, fetchHealth }
})
