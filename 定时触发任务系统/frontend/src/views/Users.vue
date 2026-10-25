<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">用户配置</div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增用户</el-button>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="用户 Open ID 以 ou_ 开头，机器人 Open ID 为机器人自身 ID。任务发送目标为「用户/机器人」时从此处选择，也可用于 @ 提及。"
      style="margin-bottom: 16px"
    />

    <el-card shadow="never">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
        <el-table-column label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.type === 'bot' ? 'warning' : 'primary'">
              {{ row.type === 'bot' ? '机器人' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="open_id" label="Open ID" min-width="320">
          <template #default="{ row }"><span class="mono">{{ row.open_id }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !list.length" description="暂未配置用户" />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑用户' : '新增用户'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如：张三" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.type">
            <el-radio value="user">用户</el-radio>
            <el-radio value="bot">机器人</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Open ID">
          <el-input v-model="form.open_id" placeholder="ou_xxxxxxxxxxxxxxxx" class="mono" />
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
import { createUser, deleteUser, listUsers, updateUser } from '../api'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref('')

const form = reactive({ name: '', type: 'user', open_id: '' })

function reset() {
  Object.assign(form, { name: '', type: 'user', open_id: '' })
}

async function load() {
  loading.value = true
  try {
    list.value = await listUsers()
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
  if (!form.name || !form.open_id) {
    ElMessage.warning('请填写名称与 Open ID')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateUser(editingId.value, { ...form })
      ElMessage.success('用户已更新')
    } else {
      await createUser({ ...form })
      ElMessage.success('用户已新增')
    }
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除「${row.name}」？`, '提示', { type: 'warning' })
  await deleteUser(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>
