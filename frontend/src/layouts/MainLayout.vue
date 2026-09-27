<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { ElTag } from 'element-plus'

const store = useAppStore()
const route = useRoute()

const menus = [
  { path: '/grade', title: 'AI 批改', icon: 'Camera' },
  { path: '/errors', title: '错题本', icon: 'Notebook' },
  { path: '/analytics', title: '学情分析', icon: 'DataAnalysis' },
  { path: '/tutor', title: 'AI 辅导', icon: 'ChatDotRound' },
  { path: '/recommend', title: '智能推题', icon: 'Aim' },
  { path: '/review', title: '复习调度', icon: 'AlarmClock' },
]

const activeMenu = computed(() => route.path)
const llmOn = computed(() => store.health?.llm_enabled)

onMounted(() => store.fetchHealth())
</script>

<template>
  <el-container style="height: 100%">
    <el-aside width="210px" style="background: #12161f; border-right: 1px solid var(--border)">
      <div style="padding: 18px 16px">
        <div style="font-weight: 700; font-size: 16px">教育智能体</div>
        <div class="muted" style="font-size: 12px; margin-top: 2px">多 Agent · LangGraph</div>
      </div>
      <el-menu :default-active="activeMenu" router background-color="#12161f" text-color="#a7b0c5" active-text-color="#7aa2ff" style="border-right: none">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="display: flex; align-items: center; justify-content: space-between; background: #161b26; border-bottom: 1px solid var(--border)">
        <div style="font-size: 15px">{{ (route.meta as any).title }}</div>
        <div style="display: flex; align-items: center; gap: 12px">
          <span class="muted" style="font-size: 13px">当前学生</span>
          <el-input v-model="store.studentId" size="small" style="width: 150px" @change="(v:string)=>store.setStudentId(v)" />
          <el-tag v-if="store.health" :type="llmOn ? 'success' : 'warning'" size="small">
            {{ llmOn ? '密钥已配置' : '未配置密钥' }}
          </el-tag>
          <el-tag v-else type="info" size="small">后端未连接</el-tag>
        </div>
      </el-header>

      <el-main style="background: var(--bg)">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>
