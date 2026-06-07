<template>
  <div class="placeholder-page">
    <el-card class="placeholder-card">
      <div class="emoji">🤖</div>
      <h2>AI 智能助手</h2>
      <p class="status">该功能正在开发中</p>
      <p class="hint">AI 组同学正在加紧开发，敬请期待！</p>

      <div class="meta">
        <p><strong>负责小组：</strong>AI 智能化部分（成员E、成员F）</p>
        <p><strong>当前进度：</strong>已搭建对话框架，正在接入意图识别和大模型</p>
        <p><strong>预计完成：</strong>Sprint 2-3（第 3-6 周）</p>
      </div>

      <div class="features">
        <h4>即将上线的功能</h4>
        <ul>
          <li>✅ 自然语言查询空座（"今晚还有靠窗的座位吗？"）</li>
          <li>✅ 一键查看个人预约记录</li>
          <li>✅ 智能推荐座位（基于历史偏好）</li>
          <li>✅ 多轮对话与上下文理解</li>
        </ul>
      </div>

      <el-button type="primary" @click="$router.push('/login')">返回登录</el-button>
    </el-card>
  </div>
</template>

<script setup>
</script>

<style scoped>
.placeholder-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.placeholder-card {
  width: 100%;
  max-width: 540px;
  text-align: center;
  padding: 20px;
}

.emoji {
  font-size: 64px;
  margin-bottom: 16px;
}

h2 {
  margin: 0 0 12px;
  color: #303133;
}

.status {
  color: #e6a23c;
  font-size: 16px;
  font-weight: 500;
  margin: 8px 0;
}

.hint {
  color: #909399;
  margin: 8px 0 24px;
}

.meta {
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 6px;
  margin: 20px 0;
  text-align: left;
  font-size: 14px;
  color: #606266;
}

.meta p {
  margin: 4px 0;
}

.features {
  text-align: left;
  background: #ecf5ff;
  padding: 16px;
  border-radius: 6px;
  margin: 16px 0;
}

.features h4 {
  margin: 0 0 8px;
  color: #409eff;
}

.features ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 1.8;
}
</style>
