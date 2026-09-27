<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'
import type { PracticePlan } from '@/types'

const store = useAppStore()
const subject = ref('')
const topK = ref(3)
const loading = ref(false)
const plan = ref<PracticePlan | null>(null)

async function run() {
  loading.value = true
  try {
    const res = await api.recommend({
      student_id: store.studentId,
      subject: subject.value || null,
      top_k: topK.value,
    })
    plan.value = res.practice_plan ?? null
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function diffType(d: string) {
  return d === '挑战' ? 'danger' : d === '提高' ? 'warning' : 'success'
}
</script>

<template>
  <div v-loading="loading">
    <el-card shadow="never">
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
        <span class="muted">学生：{{ store.studentId }}</span>
        <el-input v-model="subject" size="small" style="width: 150px" placeholder="学科（留空=全部）" />
        <span class="muted">薄弱点数量</span>
        <el-input-number v-model="topK" :min="1" :max="10" size="small" />
        <el-button type="primary" size="small" :loading="loading" @click="run">生成练习计划</el-button>
      </div>
    </el-card>

    <template v-if="plan">
      <el-card shadow="never" style="margin-top: 14px">
        <template #header>练习计划</template>
        <p class="muted" style="margin: 0">{{ plan.plan_summary }}</p>
      </el-card>

      <el-empty v-if="!plan.items?.length" description="暂无推荐题目（可先批改入库或运行 seed_demo 灌演示数据）" />
      <el-card v-for="(it, i) in plan.items" :key="i" shadow="never" style="margin-top: 12px">
        <div style="display: flex; justify-content: space-between; align-items: center">
          <b>{{ it.knowledge_point || '综合' }}</b>
          <el-tag size="small" :type="diffType(it.difficulty)">{{ it.difficulty }}</el-tag>
        </div>
        <p style="margin: 10px 0">{{ it.stem }}</p>
        <p v-if="it.hint" class="muted">💡 提示：{{ it.hint }}</p>
        <el-collapse v-if="it.answer">
          <el-collapse-item title="查看参考答案">
            <span style="color: #57d38c">{{ it.answer }}</span>
          </el-collapse-item>
        </el-collapse>
        <p v-if="it.why" class="muted" style="margin-top: 6px; font-size: 12px">为什么推荐：{{ it.why }}</p>
      </el-card>
    </template>
  </div>
</template>
