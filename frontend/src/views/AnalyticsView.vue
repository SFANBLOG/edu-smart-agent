<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'
import type { LearningReport } from '@/types'

const store = useAppStore()
const scope = ref<'mine' | 'all'>('mine')
const subject = ref('')
const loading = ref(false)
const report = ref<LearningReport | null>(null)

async function run() {
  loading.value = true
  try {
    const res = await api.analytics({
      student_id: scope.value === 'mine' ? store.studentId : null,
      subject: subject.value || null,
    })
    report.value = res.report ?? null
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
run()

function masteryColor(rate: number) {
  if (rate >= 0.85) return '#57d38c'
  if (rate >= 0.6) return '#ffcc66'
  return '#ff6b6b'
}
</script>

<template>
  <div v-loading="loading">
    <el-card shadow="never">
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
        <el-radio-group v-model="scope" @change="run">
          <el-radio-button value="mine">当前学生</el-radio-button>
          <el-radio-button value="all">全班</el-radio-button>
        </el-radio-group>
        <el-input v-model="subject" size="small" style="width: 160px" placeholder="学科（留空=全部）" />
        <el-button type="primary" size="small" :loading="loading" @click="run">生成报告</el-button>
      </div>
    </el-card>

    <template v-if="report">
      <el-card shadow="never" style="margin-top: 14px">
        <template #header>学情总览 · {{ report.scope }}</template>
        <el-space wrap size="large">
          <el-statistic title="批改次数" :value="report.total_gradings" />
          <el-statistic title="错题数量" :value="report.total_errors" />
          <el-statistic title="平均得分率" :value="Math.round(report.avg_score_rate * 100)">
            <template #suffix>%</template>
          </el-statistic>
        </el-space>
      </el-card>

      <el-card v-if="report.knowledge_mastery?.length" shadow="never" style="margin-top: 14px">
        <template #header>知识点掌握度</template>
        <div v-for="m in report.knowledge_mastery" :key="m.knowledge_point" style="margin-bottom: 12px">
          <div style="display: flex; justify-content: space-between; font-size: 13px">
            <span>{{ m.knowledge_point }} <span class="muted">（考查 {{ m.attempts }} · 错 {{ m.wrong }}）</span></span>
            <span>{{ (m.mastery_rate * 100).toFixed(0) }}%</span>
          </div>
          <el-progress :percentage="Math.round(m.mastery_rate * 100)" :color="masteryColor(m.mastery_rate)" :show-text="false" />
        </div>
      </el-card>

      <el-card v-if="Object.keys(report.error_type_dist || {}).length" shadow="never" style="margin-top: 14px">
        <template #header>错误类型分布</template>
        <el-tag v-for="(n, k) in report.error_type_dist" :key="k" style="margin: 4px">{{ k }}: {{ n }}</el-tag>
      </el-card>

      <el-card v-if="report.narrative" shadow="never" style="margin-top: 14px">
        <template #header>AI 学情洞察</template>
        <pre style="white-space: pre-wrap; margin: 0; font-family: inherit">{{ report.narrative }}</pre>
      </el-card>
    </template>
  </div>
</template>
