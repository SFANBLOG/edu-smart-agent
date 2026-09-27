<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'
import type { ReviewItem } from '@/types'

const store = useAppStore()
const scope = ref<'mine' | 'all'>('mine')
const queue = ref<ReviewItem[]>([])
const loading = ref(false)

async function load(reviewIds: number[] = []) {
  loading.value = true
  try {
    const res = await api.review({
      student_id: scope.value === 'mine' ? store.studentId : null,
      review_ids: reviewIds,
    })
    queue.value = res.review_queue
    if (reviewIds.length) ElMessage.success(`已标记 ${res.reviewed} 道为已复习，重新排期`)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
load()

function mark(id: number) {
  load([id])
}
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span>今日待复习 · 艾宾浩斯遗忘曲线（1/2/4/7/15/30 天）</span>
        <div style="display: flex; align-items: center; gap: 12px">
          <el-radio-group v-model="scope" size="small" @change="load()">
            <el-radio-button value="mine">当前学生</el-radio-button>
            <el-radio-button value="all">全部</el-radio-button>
          </el-radio-group>
          <el-button size="small" :loading="loading" @click="load()">刷新队列</el-button>
        </div>
      </div>
    </template>

    <el-empty v-if="!queue.length && !loading" description="今天没有到期需复习的错题，继续保持 👍" />
    <div v-loading="loading">
      <el-card v-for="it in queue" :key="it.error_id" shadow="never" style="margin-bottom: 10px">
        <div style="display: flex; justify-content: space-between; align-items: center">
          <div>
            <b>{{ it.knowledge_point }}</b>
            <span class="muted"> · 第 {{ it.question_no }} 题</span>
            <el-tag size="small" type="danger" style="margin-left: 8px">逾期 {{ it.overdue_days }} 天</el-tag>
            <el-tag size="small" style="margin-left: 4px">已复习 {{ it.review_count }} 次</el-tag>
          </div>
          <el-button type="primary" size="small" @click="mark(it.error_id)">标记已复习</el-button>
        </div>
        <p class="muted" style="margin: 8px 0 0">错因：{{ it.cause || '—' }}　→　建议：{{ it.suggestion || '—' }}</p>
      </el-card>
    </div>
  </el-card>
</template>
