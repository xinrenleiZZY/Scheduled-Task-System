<template>
  <el-container class="layout">
    <el-aside width="210px" class="aside">
      <div class="logo">
        <el-icon :size="22"><AlarmClock /></el-icon>
        <span>HZX 定时任务</span>
      </div>
      <el-menu :default-active="activeMenu" router class="menu">
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
      <div class="aside-footer mono">{{ appInfo.version }}</div>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ currentTitle }}</div>
        <div class="header-right">
          <el-tag type="success" effect="plain" size="small">调度器运行中</el-tag>
          <el-switch
            v-model="dark"
            inline-prompt
            :active-icon="Moon"
            :inactive-icon="Sunny"
            @change="toggleDark"
          />
        </div>
      </el-header>
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <keep-alive :max="3">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Moon, Sunny } from '@element-plus/icons-vue'
import { getAppInfo, getSettings, updateSettings } from '../api'

const route = useRoute()
const appInfo = ref({ version: '' })
const dark = ref(false)

const menus = [
  { path: '/dashboard', title: '首页', icon: 'HomeFilled' },
  { path: '/tasks', title: '任务管理', icon: 'List' },
  { path: '/monitor', title: '任务监控', icon: 'Monitor' },
  { path: '/logs', title: '日志', icon: 'Document' },
  { path: '/bots', title: '应用机器人', icon: 'MagicStick' },
  { path: '/chats', title: '群聊配置', icon: 'ChatDotRound' },
  { path: '/users', title: '用户配置', icon: 'User' },
  { path: '/backup', title: '备份恢复', icon: 'RefreshLeft' },
  { path: '/email', title: '邮箱反馈', icon: 'Message' },
  { path: '/settings', title: '设置', icon: 'Setting' },
  { path: '/tutorial', title: '使用教程', icon: 'Reading' }
]

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '首页')

function applyDark(value) {
  document.documentElement.classList.toggle('dark', value)
  localStorage.setItem('hzx-theme', value ? 'dark' : 'light')
}

async function toggleDark(value) {
  applyDark(value)
  try {
    await updateSettings({ theme: value ? 'dark' : 'light' })
  } catch (e) {
    /* 忽略持久化失败 */
  }
}

onMounted(async () => {
  try {
    appInfo.value = await getAppInfo()
  } catch (e) {
    /* ignore */
  }
  try {
    const s = await getSettings()
    dark.value = s.theme === 'dark'
    applyDark(dark.value)
  } catch (e) {
    dark.value = localStorage.getItem('hzx-theme') === 'dark'
    applyDark(dark.value)
  }
})
</script>

<style scoped>
.layout {
  height: 100%;
}

.aside {
  background: var(--hzx-aside-bg);
  border-right: 1px solid var(--hzx-aside-border);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  transition: background 0.3s ease;
}

/* 侧边栏顶部柔和光晕 */
.aside::before {
  content: '';
  position: absolute;
  top: -110px;
  left: -70px;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(74, 125, 255, 0.38), transparent 66%);
  pointer-events: none;
}

.aside::after {
  content: '';
  position: absolute;
  bottom: -120px;
  right: -80px;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(123, 92, 255, 0.28), transparent 68%);
  pointer-events: none;
}

.logo {
  position: relative;
  z-index: 1;
  height: 64px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  font-weight: 700;
  font-size: 15.5px;
  letter-spacing: 0.3px;
  color: #ffffff;
  border-bottom: 1px solid var(--hzx-aside-border);
  white-space: nowrap;
}

.logo .el-icon {
  flex: none;
  width: 34px;
  height: 34px;
  border-radius: 11px;
  color: #ffffff;
  background: var(--hzx-brand-grad);
  box-shadow: 0 10px 20px -10px rgba(74, 125, 255, 0.95);
}

.menu {
  position: relative;
  z-index: 1;
  border-right: none;
  background: transparent;
  flex: 1;
  padding: 10px 0;
  overflow-y: auto;
}

.aside-footer {
  position: relative;
  z-index: 1;
  padding: 12px 18px;
  color: var(--hzx-muted);
  font-size: 12px;
  letter-spacing: 0.4px;
  border-top: 1px solid var(--hzx-aside-border);
}

.header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--hzx-header-bg);
  border-bottom: 1px solid var(--hzx-border);
  backdrop-filter: saturate(180%) blur(10px);
  box-shadow: 0 6px 16px -16px rgba(23, 32, 58, 0.6);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.2px;
  color: var(--hzx-text);
}

.header-title::before {
  content: '';
  width: 4px;
  height: 18px;
  border-radius: 4px;
  background: var(--hzx-brand-grad);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.main {
  background-color: var(--hzx-bg);
  background-image: radial-gradient(900px 320px at 100% -8%, var(--hzx-bg-glow-1), transparent 62%),
    radial-gradient(720px 300px at -6% -4%, var(--hzx-bg-glow-2), transparent 60%);
  background-repeat: no-repeat;
  padding: 18px 20px 26px;
  overflow-y: auto;
  transition: background-color 0.3s ease;
}
</style>
