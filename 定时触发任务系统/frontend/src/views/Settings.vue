<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">设置</div>
      <el-button type="primary" :icon="Check" :loading="saving" @click="save">保存设置</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14">
        <el-card shadow="never">
          <template #header><span style="font-weight: 600">通用设置</span></template>
          <el-form :model="form" label-width="130px">
            <el-form-item label="主题">
              <el-radio-group v-model="form.theme">
                <el-radio value="light">浅色</el-radio>
                <el-radio value="dark">深色</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="自动更新">
              <el-switch v-model="form.auto_update" />
            </el-form-item>
            <el-form-item label="更新源">
              <el-radio-group v-model="form.update_source">
                <el-radio value="auto">自动</el-radio>
                <el-radio value="manual">手动</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="错误自动上报">
              <el-switch v-model="form.err_report" />
            </el-form-item>
            <el-form-item label="上报邮箱">
              <el-input v-model="form.err_email" placeholder="接收错误报告的邮箱" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header><span style="font-weight: 600">默认 Webhook</span></template>
          <el-form :model="form" label-width="130px">
            <el-form-item label="默认地址">
              <el-input v-model="form.default_webhook_url" placeholder="任务未单独填写时使用" />
            </el-form-item>
            <el-form-item label="默认 Secret">
              <el-input
                v-model="form.default_webhook_secret"
                show-password
                placeholder="签名密钥（可选）"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card shadow="never">
          <template #header><span style="font-weight: 600">系统信息</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="应用名称">{{ appInfo.app_name || '—' }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ appInfo.version || '—' }}</el-descriptions-item>
            <el-descriptions-item label="开发者">{{ appInfo.developer || '—' }}</el-descriptions-item>
            <el-descriptions-item label="联系方式">{{ appInfo.phone || '—' }}</el-descriptions-item>
            <el-descriptions-item label="时区">{{ appInfo.timezone || '—' }}</el-descriptions-item>
            <el-descriptions-item label="调度间隔">
              {{ appInfo.scheduler_interval_seconds || '—' }} 秒
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import { getAppInfo, getSettings, updateSettings } from '../api'

const saving = ref(false)
const appInfo = ref({})
const form = reactive({
  theme: 'light',
  auto_update: true,
  update_source: 'auto',
  err_report: false,
  err_email: '',
  default_webhook_url: '',
  default_webhook_secret: ''
})

async function load() {
  const [s, info] = await Promise.all([getSettings(), getAppInfo()])
  Object.assign(form, s)
  appInfo.value = info
}

async function save() {
  saving.value = true
  try {
    await updateSettings({ ...form })
    if (form.theme) {
      document.documentElement.classList.toggle('dark', form.theme === 'dark')
      localStorage.setItem('hzx-theme', form.theme)
    }
    ElMessage.success('设置已保存')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
