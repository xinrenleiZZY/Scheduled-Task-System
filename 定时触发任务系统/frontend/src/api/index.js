import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const detail = err?.response?.data?.detail
    const msg = typeof detail === 'string' ? detail : (err.message || '请求失败')
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

// ===== 仪表盘 =====
export const getDashboard = () => http.get('/dashboard')
export const getAppInfo = () => http.get('/app-info')

// ===== 任务 =====
export const listTasks = (params) => http.get('/tasks', { params })
export const createTask = (data) => http.post('/tasks', data)
export const updateTask = (id, data) => http.put(`/tasks/${id}`, data)
export const deleteTask = (id) => http.delete(`/tasks/${id}`)
export const toggleTask = (id) => http.post(`/tasks/${id}/toggle`)
export const pinTask = (id) => http.post(`/tasks/${id}/pin`)
export const runTaskNow = (id) => http.post(`/tasks/${id}/run`)
export const getTaskLogs = (id, limit = 200) => http.get(`/tasks/${id}/logs`, { params: { limit } })
export const clearTaskLogs = (id) => http.delete(`/tasks/${id}/logs`)

// ===== 机器人 =====
export const listBots = () => http.get('/bots')
export const createBot = (data) => http.post('/bots', data)
export const updateBot = (id, data) => http.put(`/bots/${id}`, data)
export const deleteBot = (id) => http.delete(`/bots/${id}`)

// ===== 群聊 =====
export const listChats = () => http.get('/chats')
export const createChat = (data) => http.post('/chats', data)
export const updateChat = (id, data) => http.put(`/chats/${id}`, data)
export const deleteChat = (id) => http.delete(`/chats/${id}`)

// ===== 用户 =====
export const listUsers = () => http.get('/users')
export const createUser = (data) => http.post('/users', data)
export const updateUser = (id, data) => http.put(`/users/${id}`, data)
export const deleteUser = (id) => http.delete(`/users/${id}`)

// ===== 日志 =====
export const getSystemLogs = (limit = 300) => http.get('/logs/system', { params: { limit } })
export const clearSystemLogs = () => http.delete('/logs/system')
export const getTaskLogOverview = () => http.get('/logs/tasks')

// ===== 设置 =====
export const getSettings = () => http.get('/settings')
export const updateSettings = (data) => http.put('/settings', data)

// ===== 备份 =====
export const listBackups = () => http.get('/backups')
export const createBackup = (note = '') => http.post('/backups', null, { params: { note } })
export const restoreBackup = (id) => http.post(`/backups/${id}/restore`)
export const deleteBackup = (id) => http.delete(`/backups/${id}`)
export const backupDownloadUrl = (id) => `/api/backups/${id}/download`
export const exportNow = () => http.get('/backups/export')
export const importData = (data) => http.post('/backups/import', data)

// ===== 邮件 =====
export const sendEmail = (data) => http.post('/email/send', data)

export default http
