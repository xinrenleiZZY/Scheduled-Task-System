<template>
  <div class="page">
    <div class="page-header">
      <div class="page-title">使用教程</div>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><span style="font-weight: 600">快速开始</span></template>
      <el-steps :active="4" align-center finish-status="success">
        <el-step title="配置机器人" description="应用机器人与群聊/用户" />
        <el-step title="新建任务" description="设置调度与消息" />
        <el-step title="任务监控" description="查看运行结果" />
        <el-step title="备份恢复" description="保障数据安全" />
      </el-steps>
      <div class="hint" style="margin-top: 16px">
        <div>1. 在「群聊配置」「用户配置」中添加推送目标，在「应用机器人」中填写飞书应用的 App ID / Secret。</div>
        <div>2. 在「任务管理」中新建任务，选择「间隔执行」或「Cron 表达式」，设置发送方式与消息内容。</div>
        <div>3. 在「任务监控」中实时查看各任务的运行状态、耗时与最近错误。</div>
        <div>4. 定期在「备份恢复」中导出数据，或使用自动备份。</div>
      </div>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><span style="font-weight: 600">Cron 表达式说明</span></template>
      <div class="hint">
        <div>格式为 5 个字段：<span class="mono">分 时 日 月 周</span>，遵循标准 cron 语义，支持 <span class="mono">*</span>、整数、范围（-）、列表（,）与步长（/）。</div>
        <div>「周」字段：<span class="mono">0</span> 或 <span class="mono">7</span> = 周日，<span class="mono">1</span> = 周一 … <span class="mono">6</span> = 周六。</div>
      </div>
      <el-table :data="cronExamples" size="small" style="margin-top: 12px" border>
        <el-table-column prop="expr" label="表达式" width="180">
          <template #default="{ row }"><span class="mono">{{ row.expr }}</span></template>
        </el-table-column>
        <el-table-column prop="desc" label="含义" />
      </el-table>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header><span style="font-weight: 600">发送方式说明</span></template>
      <el-table :data="sendTypes" size="small" border>
        <el-table-column prop="type" label="方式" width="180" />
        <el-table-column prop="desc" label="说明" />
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header><span style="font-weight: 600">@ 提及说明</span></template>
      <div class="hint">
        <div>• 在任务编辑中「@ 用户」选择或输入用户的 <span class="mono">open_id</span>（ou_ 开头）或 <span class="mono">user_id</span>。</div>
        <div>• 开启「@ 所有人」将额外附带 <span class="mono">&lt;at user_id="all"&gt;&lt;/at&gt;</span> 以提醒群内所有人。</div>
        <div>• Webhook 方式会自动根据 ID 前缀判断类型；应用机器人 API 方式同样自动识别。</div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
const cronExamples = [
  { expr: '0 9 * * *', desc: '每天 09:00 执行' },
  { expr: '30 8 * * *', desc: '每天 08:30 执行' },
  { expr: '0 18 * * *', desc: '每天 18:00 执行' },
  { expr: '0 9 * * 1-5', desc: '工作日（周一~周五）09:00 执行' },
  { expr: '1 18 * * 1-6', desc: '周一~周六 18:01 执行' },
  { expr: '0 9 * * 0', desc: '每周日 09:00 执行' },
  { expr: '0 9 1 * *', desc: '每月 1 日 09:00 执行' },
  { expr: '0 0 * * *', desc: '每天 00:00 执行' }
]

const sendTypes = [
  {
    type: 'Webhook（自定义机器人）',
    desc: '使用飞书群自定义机器人的 Webhook 地址推送文本，支持签名校验（Secret）。'
  },
  {
    type: '应用机器人 API',
    desc: '使用飞书开放平台应用凭证（App ID / Secret）调用消息接口，可发送到群聊（oc_）或用户/机器人（open_id）。'
  }
]
</script>
