import client from './client'
import type { AgentResponse, ErrorRecord, Health } from '@/types'

export interface ImageInput {
  url?: string
  base64?: string
}

export const api = {
  health: () => client.get<Health>('/health').then((r) => r.data),

  // AI 批改（JSON：图片 base64/url + 学生 + 参考答案）
  grade: (payload: {
    images: ImageInput[]
    student_id: string
    reference?: string
  }) => client.post<AgentResponse>('/grade', payload).then((r) => r.data),

  // AI 批改（直接上传图片文件）
  gradeUpload: (file: File, student_id: string, reference = '') => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('student_id', student_id)
    fd.append('reference', reference)
    return client
      .post<AgentResponse>('/grade/upload', fd)
      .then((r) => r.data)
  },

  // 学情分析
  analytics: (payload: { student_id?: string | null; subject?: string | null }) =>
    client.post<AgentResponse>('/analytics', payload).then((r) => r.data),

  // 苏格拉底式辅导
  tutor: (payload: {
    student_id: string
    question: string
    history: { role: string; content: string }[]
  }) => client.post<AgentResponse>('/tutor', payload).then((r) => r.data),

  // 智能推题
  recommend: (payload: {
    student_id: string
    subject?: string | null
    top_k?: number
  }) => client.post<AgentResponse>('/recommend', payload).then((r) => r.data),

  // 复习调度：拉队列 / 回写已复习
  review: (payload: { student_id?: string | null; review_ids?: number[] }) =>
    client.post<AgentResponse>('/review', payload).then((r) => r.data),

  // 错题本明细
  errors: (student_id?: string | null, limit = 100) =>
    client
      .get<{ errors: ErrorRecord[] }>('/errors', {
        params: { student_id: student_id || undefined, limit },
      })
      .then((r) => r.data.errors),
}
