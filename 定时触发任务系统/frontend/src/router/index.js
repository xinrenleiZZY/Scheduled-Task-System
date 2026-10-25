import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '首页', icon: 'HomeFilled' } },
      { path: 'tasks', name: 'tasks', component: () => import('../views/Tasks.vue'), meta: { title: '任务管理', icon: 'List' } },
      { path: 'monitor', name: 'monitor', component: () => import('../views/Monitor.vue'), meta: { title: '任务监控', icon: 'Monitor' } },
      { path: 'logs', name: 'logs', component: () => import('../views/Logs.vue'), meta: { title: '日志', icon: 'Document' } },
      { path: 'bots', name: 'bots', component: () => import('../views/Bots.vue'), meta: { title: '应用机器人', icon: 'MagicStick' } },
      { path: 'chats', name: 'chats', component: () => import('../views/Chats.vue'), meta: { title: '群聊配置', icon: 'ChatDotRound' } },
      { path: 'users', name: 'users', component: () => import('../views/Users.vue'), meta: { title: '用户配置', icon: 'User' } },
      { path: 'backup', name: 'backup', component: () => import('../views/Backup.vue'), meta: { title: '备份恢复', icon: 'RefreshLeft' } },
      { path: 'email', name: 'email', component: () => import('../views/Email.vue'), meta: { title: '邮箱反馈', icon: 'Message' } },
      { path: 'settings', name: 'settings', component: () => import('../views/Settings.vue'), meta: { title: '设置', icon: 'Setting' } },
      { path: 'tutorial', name: 'tutorial', component: () => import('../views/Tutorial.vue'), meta: { title: '使用教程', icon: 'Reading' } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
