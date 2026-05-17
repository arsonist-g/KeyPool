<script setup lang="ts">
import { ref, computed } from 'vue'

const baseUrl = computed(() => window.location.origin)
const copiedKey = ref<string | null>(null)

function copy(key: string, text: string) {
  navigator.clipboard.writeText(text)
  copiedKey.value = key
  setTimeout(() => { copiedKey.value = null }, 2000)
}

const claudeCodeCommands = computed(() => {
  const url = baseUrl.value
  return [
    `claude mcp add tavily -- npx -y mcp-remote ${url}/api/tavily/mcp?token=<your-token>`,
    `claude mcp add context7 -- npx -y mcp-remote ${url}/api/context7/mcp?token=<your-token>`,
    `claude mcp add exa -- npx -y mcp-remote ${url}/api/exa/mcp?token=<your-token>`,
  ].join('\n')
})

const claudeCodeJson = computed(() => JSON.stringify({
  "mcpServers": {
    "tavily": {
      "command": "npx",
      "args": ["-y", "mcp-remote", `${baseUrl.value}/api/tavily/mcp?token=<your-token>`]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "mcp-remote", `${baseUrl.value}/api/context7/mcp?token=<your-token>`]
    },
    "exa": {
      "command": "npx",
      "args": ["-y", "mcp-remote", `${baseUrl.value}/api/exa/mcp?token=<your-token>`]
    }
  }
}, null, 2))

const codexCommands = computed(() => {
  const url = baseUrl.value
  return [
    `codex mcp add tavily --url ${url}/api/tavily/mcp?token=<your-token>`,
    `codex mcp add context7 --url ${url}/api/context7/mcp?token=<your-token>`,
    `codex mcp add exa --url ${url}/api/exa/mcp?token=<your-token>`,
  ].join('\n')
})

const codexToml = computed(() => {
  const url = baseUrl.value
  return `[mcp_servers.tavily]
url = "${url}/api/tavily/mcp?token=<your-token>"

[mcp_servers.context7]
url = "${url}/api/context7/mcp?token=<your-token>"

[mcp_servers.exa]
url = "${url}/api/exa/mcp?token=<your-token>"`
})

const genericConfig = computed(() => JSON.stringify({
  "mcpServers": {
    "tavily": {
      "url": `${baseUrl.value}/api/tavily/mcp`,
      "headers": { "Authorization": "Bearer <your-token>" }
    },
    "context7": {
      "url": `${baseUrl.value}/api/context7/mcp`,
      "headers": { "Authorization": "Bearer <your-token>" }
    },
    "exa": {
      "url": `${baseUrl.value}/api/exa/mcp`,
      "headers": { "Authorization": "Bearer <your-token>" }
    }
  }
}, null, 2))

const restExamples = computed(() => {
  const url = baseUrl.value
  return {
    tavily: `curl -X POST ${url}/api/tavily/search \\
  -H "Authorization: Bearer <your-token>" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "latest AI news", "max_results": 5}'`,
    context7: `curl -X POST ${url}/api/context7/api/v2/context \\
  -H "Authorization: Bearer <your-token>" \\
  -H "Content-Type: application/json" \\
  -d '{"libraryId": "/vercel/next.js", "query": "app router"}'`,
    exa: `curl -X POST ${url}/api/exa/search \\
  -H "Authorization: Bearer <your-token>" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "machine learning papers", "num_results": 10}'`,
  }
})

const restEndpoints = computed(() => {
  const url = baseUrl.value
  return [
    { platform: 'Tavily', base: `${url}/api/tavily/`, endpoints: ['search', 'extract', 'usage'] },
    { platform: 'Context7', base: `${url}/api/context7/`, endpoints: ['api/v2/libs/search', 'api/v2/context'] },
    { platform: 'Exa', base: `${url}/api/exa/`, endpoints: ['search', 'contents', 'answer'] },
  ]
})
</script>

<template>
  <div class="guide-page">
    <div class="page-header">
      <h1>接入指南</h1>
    </div>
    <p class="guide-intro">
      将下方配置中的 <code>&lt;your-token&gt;</code> 替换为管理员分发的项目 Token，即可接入 KeyPool 代理服务。
    </p>

    <div class="guide-card">
      <div class="card-header">
        <h2>Claude Code</h2>
        <span class="card-desc">一键命令（终端执行）</span>
      </div>
      <div class="code-block-wrap">
        <button class="btn-copy" @click="copy('claude-cmd', claudeCodeCommands)">
          {{ copiedKey === 'claude-cmd' ? '已复制' : '复制' }}
        </button>
        <pre class="code-block"><code>{{ claudeCodeCommands }}</code></pre>
      </div>
      <details class="config-details">
        <summary>或手动配置 .mcp.json</summary>
        <div class="code-block-wrap">
          <button class="btn-copy" @click="copy('claude-json', claudeCodeJson)">
            {{ copiedKey === 'claude-json' ? '已复制' : '复制' }}
          </button>
          <pre class="code-block"><code>{{ claudeCodeJson }}</code></pre>
        </div>
      </details>
    </div>

    <div class="guide-card">
      <div class="card-header">
        <h2>Codex CLI</h2>
        <span class="card-desc">一键命令（终端执行）</span>
      </div>
      <div class="code-block-wrap">
        <button class="btn-copy" @click="copy('codex-cmd', codexCommands)">
          {{ copiedKey === 'codex-cmd' ? '已复制' : '复制' }}
        </button>
        <pre class="code-block"><code>{{ codexCommands }}</code></pre>
      </div>
      <details class="config-details">
        <summary>或手动配置 ~/.codex/config.toml</summary>
        <div class="code-block-wrap">
          <button class="btn-copy" @click="copy('codex-toml', codexToml)">
            {{ copiedKey === 'codex-toml' ? '已复制' : '复制' }}
          </button>
          <pre class="code-block"><code>{{ codexToml }}</code></pre>
        </div>
      </details>
    </div>

    <div class="guide-card">
      <div class="card-header">
        <h2>通用 MCP 客户端</h2>
        <span class="card-desc">适用于支持 Streamable HTTP 的任意 MCP 客户端</span>
      </div>
      <div class="code-block-wrap">
        <button class="btn-copy" @click="copy('generic', genericConfig)">
          {{ copiedKey === 'generic' ? '已复制' : '复制' }}
        </button>
        <pre class="code-block"><code>{{ genericConfig }}</code></pre>
      </div>
    </div>

    <div class="section-divider"></div>

    <div class="page-header">
      <h1>REST API 代理</h1>
    </div>
    <p class="guide-intro">
      除 MCP 协议外，KeyPool 同时代理各平台的 REST API。请求体和响应完全透传，与直接调用原始 API 无差异。
      路由规则：<code>/api/{platform}/{path}</code> 等价于平台原始地址 + path。
    </p>

    <div class="guide-card">
      <div class="card-header">
        <h2>可用端点</h2>
        <span class="card-desc">认证方式与 MCP 相同，使用 Bearer Token</span>
      </div>
      <div class="endpoints-table">
        <table>
          <thead>
            <tr>
              <th>平台</th>
              <th>KeyPool 地址</th>
              <th>等价原始地址</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="item in restEndpoints" :key="item.platform">
              <tr v-for="ep in item.endpoints" :key="ep">
                <td>{{ item.platform }}</td>
                <td><code>{{ item.base }}{{ ep }}</code></td>
                <td><code>{{ ep }}</code></td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <div class="guide-card">
      <div class="card-header">
        <h2>Tavily Search</h2>
        <span class="card-desc">搜索接口示例</span>
      </div>
      <div class="code-block-wrap">
        <button class="btn-copy" @click="copy('rest-tavily', restExamples.tavily)">
          {{ copiedKey === 'rest-tavily' ? '已复制' : '复制' }}
        </button>
        <pre class="code-block"><code>{{ restExamples.tavily }}</code></pre>
      </div>
    </div>

    <div class="guide-card">
      <div class="card-header">
        <h2>Context7</h2>
        <span class="card-desc">文档查询接口示例</span>
      </div>
      <div class="code-block-wrap">
        <button class="btn-copy" @click="copy('rest-context7', restExamples.context7)">
          {{ copiedKey === 'rest-context7' ? '已复制' : '复制' }}
        </button>
        <pre class="code-block"><code>{{ restExamples.context7 }}</code></pre>
      </div>
    </div>

    <div class="guide-card">
      <div class="card-header">
        <h2>Exa Search</h2>
        <span class="card-desc">搜索接口示例</span>
      </div>
      <div class="code-block-wrap">
        <button class="btn-copy" @click="copy('rest-exa', restExamples.exa)">
          {{ copiedKey === 'rest-exa' ? '已复制' : '复制' }}
        </button>
        <pre class="code-block"><code>{{ restExamples.exa }}</code></pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.guide-page h1 {
  margin-bottom: var(--spacing-sm);
}

.page-header {
  margin-bottom: var(--spacing-xs);
}

.guide-intro {
  color: var(--color-ink-muted-80);
  font-size: 14px;
  margin-bottom: var(--spacing-xl);
}

.guide-intro code {
  background: var(--color-canvas-parchment);
  padding: 2px 6px;
  border-radius: var(--rounded-xs);
  font-family: "SF Mono", "Fira Code", monospace;
  font-size: 13px;
}

.guide-card {
  background: var(--color-canvas);
  border-radius: var(--rounded-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.card-header {
  margin-bottom: var(--spacing-md);
}

.card-header h2 {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: var(--spacing-xxs);
}

.card-desc {
  font-size: 13px;
  color: var(--color-ink-muted-48);
}

.code-block-wrap {
  position: relative;
}

.btn-copy {
  position: absolute;
  top: 12px;
  right: 12px;
  background: var(--color-canvas);
  color: var(--color-primary);
  font-size: 12px;
  padding: 4px 10px;
  border-radius: var(--rounded-pill);
  border: 1px solid var(--color-hairline);
  cursor: pointer;
  z-index: 1;
}

.btn-copy:hover {
  background: var(--color-canvas-parchment);
}

.code-block {
  background: var(--color-canvas-parchment);
  border-radius: var(--rounded-sm);
  padding: var(--spacing-lg);
  padding-right: 80px;
  overflow-x: auto;
  font-family: "SF Mono", "Fira Code", monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre;
  color: var(--color-ink-muted-80);
}

.config-details {
  margin-top: var(--spacing-md);
}

.config-details summary {
  font-size: 13px;
  color: var(--color-primary);
  cursor: pointer;
  margin-bottom: var(--spacing-sm);
}

.config-details summary:hover {
  text-decoration: underline;
}

.section-divider {
  height: 1px;
  background: var(--color-hairline);
  margin: var(--spacing-xl) 0;
}

.endpoints-table {
  overflow-x: auto;
}

.endpoints-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.endpoints-table th,
.endpoints-table td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-hairline);
}

.endpoints-table th {
  font-weight: 600;
  color: var(--color-ink-muted-80);
  background: var(--color-canvas-parchment);
}

.endpoints-table td code {
  font-family: "SF Mono", "Fira Code", monospace;
  font-size: 12px;
  background: var(--color-canvas-parchment);
  padding: 2px 6px;
  border-radius: var(--rounded-xs);
}
</style>
