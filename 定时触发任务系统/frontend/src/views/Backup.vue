<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">备份恢复</div>
      <div style="display: flex; gap: 10px">
        <el-button :icon="Download" @click="exportNowData">导出数据</el-button>
        <el-button :icon="Upload" @click="importVisible = true">导入数据</el-button>
        <el-button type="primary" :icon="Plus" :loading="creating" @click="create">创建备份</el-button>
      </div>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="系统每天自动备份一次。备份包含任务、机器人、群聊、用户与设置数据；恢复会按 ID 合并写入当前数据库。"
      style="margin-bottom: 16px"
    />

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="filename" label="文件名" min-width="240" show-overflow-tooltip>
          <template #default="{ row }"><span class="mono">{{ row.filename }}</span></template>
        </el-table-column>
        <el-table-column label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.kind === 'auto' ? 'info' : 'primary'">
              {{ row.kind === 'auto' ? '自动' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="110" align="center">
          <template #default="{ row }">{{ formatSize(row.size) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="190" />
        <el-table-column prop="note" label="备注" min-width="140" show-overflow-tooltip />
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link @click="download(row)">下载</el-button>
            <el-button size="small" type="warning" link @click="restore(row)">恢复</el-button>
            <el-button size="small" type="danger" link @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !list.length" description="暂无备份记录" />
    </el-card>

    <el-dialog v-model="importVisible" title="导入数据" width="640px">
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="导入将按 ID 合并覆盖同名数据，请先确保已备份当前数据。"
        style="margin-bottom: 12px"
      />
      <el-upload
        drag
        :auto-upload="false"
        :show-file-list="false"
        accept=".json"
        :on-change="onFileChange"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽 JSON 文件到此处，或<em>点击选择文件</em></div>
      </el-upload>
      <el-form-item label="或粘贴 JSON" label-width="100px" style="margin-top: 12px" v-if="false" />
      <el-input
        v-model="importText"
        type="textarea"
        :rows="8"
        placeholder="在此粘贴导出的 JSON 内容"
        class="mono"
        style="margin-top: 12px"
      />
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Plus, Upload, UploadFilled } from '@element-plus/icons-vue'
import {
  backupDownloadUrl,
  createBackup,
  deleteBackup,
  exportNow,
  importData,
  listBackups,
  restoreBackup
} from '../api'

const loading = ref(false)
const creating = ref(false)
const importing = ref(false)
const list = ref([])
const importVisible = ref(false)
const importText = ref('')

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

function saveBlob(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function load() {
  loading.value = true
  try {
    list.value = await listBackups()
  } finally {
    loading.value = false
  }
}

async function create() {
  creating.value = true
  try {
    await createBackup('手动备份')
    ElMessage.success('备份已创建')
    load()
  } finally {
    creating.value = false
  }
}

function download(row) {
  window.open(backupDownloadUrl(row.id), '_blank')
}

async function restore(row) {
  await ElMessageBox.confirm(`确认从备份「${row.filename}」恢复？将覆盖同 ID 数据。`, '提示', {
    type: 'warning'
  })
  const res = await restoreBackup(row.id)
  ElMessage[res.success ? 'success' : 'error'](res.message)
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除备份「${row.filename}」？`, '提示', { type: 'warning' })
  await deleteBackup(row.id)
  ElMessage.success('已删除')
  load()
}

async function exportNowData() {
  const data = await exportNow()
  saveBlob(data, `hzx-export-${Date.now()}.json`)
  ElMessage.success('数据已导出')
}

function onFileChange(file) {
  const reader = new FileReader()
  reader.onload = () => {
    importText.value = reader.result
  }
  reader.readAsText(file.raw)
}

async function doImport() {
  if (!importText.value.trim()) {
    ElMessage.warning('请输入或选择 JSON 数据')
    return
  }
  let data
  try {
    data = JSON.parse(importText.value)
  } catch (e) {
    ElMessage.error('JSON 解析失败：' + e.message)
    return
  }
  importing.value = true
  try {
    const res = await importData(data)
    ElMessage[res.success ? 'success' : 'error'](res.message)
    importVisible.value = false
    importText.value = ''
    load()
  } finally {
    importing.value = false
  }
}

onMounted(load)
</script>
