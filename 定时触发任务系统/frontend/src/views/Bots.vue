<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">应用机器人</div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增机器人</el-button>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="应用机器人用于「应用机器人 API」方式推送消息，需填写飞书开放平台应用的 App ID / App Secret。"
      style="margin-bottom: 16px"
    />

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="app_id" label="App ID" min-width="220" show-overflow-tooltip />
        <el-table-column label="App Secret" min-width="180">
          <template #default="{ row }">
            <span class="mono">{{ row.app_secret ? '••••••••' : '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="open_id" label="机器人 Open ID" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !list.length" description="暂未配置应用机器人" />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑机器人' : '新增机器人'" width="560px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如：定时任务触发机器人" />
        </el-form-item>
        <el-form-item label="App ID">
          <el-input v-model="form.app_id" placeholder="cli_xxxxxxxxxxxx" class="mono" />
        </el-form-item>
        <el-form-item label="App Secret">
          <el-input v-model="form.app_secret" show-password placeholder="应用密钥" class="mono" />
        </el-form-item>
        <el-form-item label="Open ID">
          <el-input v-model="form.open_id" placeholder="机器人自身的 open_id（可选）" class="mono" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createBot, deleteBot, listBots, updateBot } from '../api'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref('')

const form = reactive({ name: '', app_id: '', app_secret: '', open_id: '' })

function reset() {
  Object.assign(form, { name: '', app_id: '', app_secret: '', open_id: '' })
}

async function load() {
  loading.value = true
  try {
    list.value = await listBots()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  reset()
  editing.value = false
  editingId.value = ''
  dialogVisible.value = true
}

function openEdit(row) {
  reset()
  Object.assign(form, row)
  editing.value = true
  editingId.value = row.id
  dialogVisible.value = true
}

async function save() {
  if (!form.name) {
    ElMessage.warning('请填写名称')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateBot(editingId.value, { ...form })
      ElMessage.success('机器人已更新')
    } else {
      await createBot({ ...form })
      ElMessage.success('机器人已新增')
    }
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除机器人「${row.name}」？`, '提示', { type: 'warning' })
  await deleteBot(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>
