<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">群聊配置</div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增群聊</el-button>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="群聊 Chat ID 以 oc_ 开头，可在飞书群设置中获取。任务发送目标为「群聊」时从此处选择。"
      style="margin-bottom: 16px"
    />

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="name" label="群聊名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="chat_id" label="Chat ID" min-width="320">
          <template #default="{ row }"><span class="mono">{{ row.chat_id }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !list.length" description="暂未配置群聊" />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑群聊' : '新增群聊'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="群聊名称">
          <el-input v-model="form.name" placeholder="如：运营群" />
        </el-form-item>
        <el-form-item label="Chat ID">
          <el-input v-model="form.chat_id" placeholder="oc_xxxxxxxxxxxxxxxx" class="mono" />
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
import { createChat, deleteChat, listChats, updateChat } from '../api'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref('')

const form = reactive({ name: '', chat_id: '' })

function reset() {
  Object.assign(form, { name: '', chat_id: '' })
}

async function load() {
  loading.value = true
  try {
    list.value = await listChats()
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
  if (!form.name || !form.chat_id) {
    ElMessage.warning('请填写群聊名称与 Chat ID')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateChat(editingId.value, { ...form })
      ElMessage.success('群聊已更新')
    } else {
      await createChat({ ...form })
      ElMessage.success('群聊已新增')
    }
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除群聊「${row.name}」？`, '提示', { type: 'warning' })
  await deleteChat(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>
