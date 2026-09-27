<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api, type ImageInput } from '@/api'
import { useAppStore } from '@/stores/app'
import type { AgentResponse } from '@/types'

const store = useAppStore()
const images = ref<ImageInput[]>([])
const thumbs = ref<string[]>([])
const reference = ref('')
const loading = ref(false)
const result = ref<AgentResponse | null>(null)

function onFile(file: File) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const url = e.target?.result as string
    images.value.push({ base64: url })
    thumbs.value.push(url)
  }
  reader.readAsDataURL(file)
  return false // 阻止 el-upload 自动上传
}

function clear() {
  images.value = []
  thumbs.value = []
  result.value = null
}

async function run() {
  if (!images.value.length) return ElMessage.warning('请先选择作业图片')
  loading.value = true
  try {
    result.value = await api.grade({
      images: images.value,
      student_id: store.studentId,
      reference: reference.value,
    })
    if (result.value.error) ElMessage.warning(result.value.error)
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <el-card shadow="never">
      <el-upload
        drag
        multiple
        list-type="picture-card"
        accept="image/*"
        :before-upload="() => false"
        :on-change="(f: any) => f.raw && onFile(f.raw)"
        :auto-upload="false"
      >
        <div style="padding: 12px">
          <el-icon size="28"><UploadFilled /></el-icon>
          <div class="muted">点击或拖入学生作业图片（支持多张）</div>
        </div>
      </el-upload>

      <el-input v-model="reference" style="margin-top: 12px" placeholder="参考答案 / 评分标准（可选）" />
      <div style="margin-top: 12px; display: flex; gap: 10px">
        <el-button type="primary" :loading="loading" @click="run">开始批改</el-button>
        <el-button @click="clear">清空</el-button>
      </div>
    </el-card>

    <template v-if="result">
      <el-card shadow="never" style="margin-top: 14px">
        <span class="muted">执行链路：</span>
        <el-tag v-for="s in result.steps" :key="s" size="small" style="margin: 0 4px">{{ s }}</el-tag>
        <el-tag v-if="result.error" type="danger" size="small">{{ result.error }}</el-tag>
      </el-card>

      <el-card v-if="result.grading" shadow="never" style="margin-top: 14px">
        <template #header>
          批改结果 · {{ result.grading.subject || '未识别学科' }}
          <el-tag v-if="result.saved_errors" size="small" style="margin-left: 8px">新增 {{ result.saved_errors }} 条错题</el-tag>
        </template>
        <p class="muted">得分 {{ result.grading.earned_score }} / {{ result.grading.total_score }}</p>
        <p style="margin: 6px 0">{{ result.grading.overall_comment }}</p>
        <el-table :data="result.grading.questions" size="small">
          <el-table-column prop="question_no" label="题号" width="70" />
          <el-table-column prop="student_answer" label="作答" />
          <el-table-column prop="correct_answer" label="参考答案" />
          <el-table-column label="判定" width="80">
            <template #default="{ row }">
              <span :class="row.is_correct ? 'ok' : 'bad'">{{ row.is_correct ? '✓ 对' : '✗ 错' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="得分" width="90">
            <template #default="{ row }">{{ row.score }}/{{ row.max_score }}</template>
          </el-table-column>
          <el-table-column prop="knowledge_point" label="知识点" width="130" />
          <el-table-column prop="feedback" label="批注" />
        </el-table>
      </el-card>

      <el-card v-if="result.error_analysis?.errors?.length" shadow="never" style="margin-top: 14px">
        <template #header>错题归因</template>
        <el-table :data="result.error_analysis.errors" size="small">
          <el-table-column prop="question_no" label="题号" width="70" />
          <el-table-column prop="error_type" label="错误类型" width="120" />
          <el-table-column prop="cause" label="错因分析" />
          <el-table-column prop="suggestion" label="订正建议" />
        </el-table>
        <p class="muted" style="margin-top: 8px">{{ result.error_analysis.summary }}</p>
      </el-card>
    </template>
  </div>
</template>
