<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'

interface Msg {
  role: 'user' | 'assistant'
  content: string
  points?: string[]
}

const store = useAppStore()
const msgs = ref<Msg[]>([])
const input = ref('')
const loading = ref(false)
const scroller = ref<HTMLElement | null>(null)

async function send() {
  const q = input.value.trim()
  if (!q) return
  msgs.value.push({ role: 'user', content: q })
  input.value = ''
  await scroll()
  loading.value = true
  try {
    // 仅回传纯文本历史给后端
    const history = msgs.value.slice(0, -1).map((m) => ({ role: m.role, content: m.content }))
    const res = await api.tutor({ student_id: store.studentId, question: q, history })
    msgs.value.push({
      role: 'assistant',
      content: res.tutor_reply?.reply || '（无回复）',
      points: res.tutor_reply?.grounded_points || [],
    })
  } catch (e: any) {
    ElMessage.error(e.message)
    msgs.value.push({ role: 'assistant', content: '请求失败：' + e.message })
  } finally {
    loading.value = false
    await scroll()
  }
}

async function scroll() {
  await nextTick()
  if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
}
</script>

<template>
  <el-card shadow="never">
    <template #header>
      苏格拉底式辅导（针对学生「{{ store.studentId }}」的错题落点启发，不直接给答案）
      <el-button link size="small" style="float: right" @click="msgs = []">清空会话</el-button>
    </template>

    <div ref="scroller" style="height: 55vh; overflow: auto; padding-right: 8px">
      <el-empty v-if="!msgs.length" description="描述你的题目或卡点，让 AI 老师一步步启发你" />
      <div v-for="(m, i) in msgs" :key="i" :style="{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: '12px' }">
        <div
          :style="{
            maxWidth: '76%',
            padding: '10px 14px',
            borderRadius: '12px',
            background: m.role === 'user' ? '#24406e' : '#1b2331',
            border: m.role === 'user' ? 'none' : '1px solid var(--border)',
            whiteSpace: 'pre-wrap',
          }"
        >
          {{ m.content }}
          <div v-if="m.points?.length" style="margin-top: 6px">
            <span class="muted" style="font-size: 12px">关联薄弱点：</span>
            <el-tag v-for="p in m.points" :key="p" size="small" style="margin: 2px">{{ p }}</el-tag>
          </div>
        </div>
      </div>
      <div v-if="loading" class="muted" style="font-size: 13px">AI 正在思考…</div>
    </div>

    <div style="display: flex; gap: 10px; margin-top: 12px">
      <el-input v-model="input" type="textarea" :rows="2" placeholder="例如：这道导数题我不知道从哪入手" @keydown.enter.exact.prevent="send" />
      <el-button type="primary" :loading="loading" @click="send">发送</el-button>
    </div>
  </el-card>
</template>
