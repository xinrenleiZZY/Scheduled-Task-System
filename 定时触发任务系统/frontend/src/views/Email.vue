<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">邮箱反馈</div>
    </div>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="用于发送问题反馈或测试邮件。SMTP 服务器信息在后端 .env（SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD）中配置。"
      style="margin-bottom: 16px"
    />

    <el-card shadow="never" style="max-width: 760px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="收件人">
          <el-input v-model="form.to_addr" placeholder="name@example.com" />
        </el-form-item>
        <el-form-item label="主题">
          <el-input v-model="form.subject" placeholder="邮件主题" />
        </el-form-item>
        <el-form-item label="正文">
          <el-input v-model="form.body" type="textarea" :rows="8" placeholder="请输入正文内容" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Promotion" :loading="sending" @click="send">发送邮件</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div class="hint">
        <div>• 默认 SMTP：smtp.qq.com:587（STARTTLS）</div>
        <div>• 若使用 QQ 邮箱，密码请填写「授权码」而非登录密码</div>
        <div>• 可在「设置」中开启错误自动上报，任务失败时自动发送到指定邮箱</div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'
import { sendEmail } from '../api'

const sending = ref(false)
const form = reactive({ to_addr: '', subject: '', body: '' })

function reset() {
  Object.assign(form, { to_addr: '', subject: '', body: '' })
}

async function send() {
  if (!form.to_addr) {
    ElMessage.warning('请填写收件人')
    return
  }
  sending.value = true
  try {
    const res = await sendEmail({ ...form })
    ElMessage[res.success ? 'success' : 'error'](res.message)
  } finally {
    sending.value = false
  }
}
</script>
