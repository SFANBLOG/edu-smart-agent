<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'
import type { ErrorRecord } from '@/types'

const store = useAppStore()
const onlyMine = ref(true)
const rows = ref<ErrorRecord[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    rows.value = await api.errors(onlyMine.value ? store.studentId : null, 200)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
load()
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span>错题本明细</span>
        <div style="display: flex; align-items: center; gap: 12px">
          <el-switch v-model="onlyMine" active-text="仅当前学生" @change="load" />
          <el-button size="small" :loading="loading" @click="load">刷新</el-button>
        </div>
      </div>
    </template>
    <el-table :data="rows" v-loading="loading" size="small" empty-text="暂无错题记录">
      <el-table-column prop="student_id" label="学生" width="90" />
      <el-table-column prop="subject" label="学科" width="70" />
      <el-table-column prop="question_no" label="题号" width="60" />
      <el-table-column prop="knowledge_point" label="知识点" width="130" />
      <el-table-column prop="error_type" label="错误类型" width="100" />
      <el-table-column prop="cause" label="错因" show-overflow-tooltip />
      <el-table-column prop="suggestion" label="建议" show-overflow-tooltip />
      <el-table-column label="复习" width="90">
        <template #default="{ row }">已 {{ row.review_count }} 次</template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
