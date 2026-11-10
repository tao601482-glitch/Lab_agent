import { getToken } from '@/utils/auth'

export async function chatStreamApi(data, onEvent) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || ''
  const token = getToken()
  const res = await fetch(`${baseURL}/api/ai/chat/stream`, {
    method: 'POST',
    headers: {
      'content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data) //把 JavaScript 对象转换成 JSON 字符串，然后作为 HTTP 请求体发送给后端。
  })
  if (res.status == 401) {
    throw new Error('登陆失效，请重新登录')
  }
  if (!res.ok || !res.body) {
    throw new Error('流式接口请求失败')
  }
  const contentType = res.headers.get('content-Type') || ''
  if (!contentType.includes('text/event-stream')) {
    const payload = await res.json().catch(() => null)
    throw new Error(payload?.message || '流式接口返回异常')
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder('UTF-8')
  let buffer = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        throw new Error('响应中断，未收到结束事件，请核对结果后重试')
      }
      buffer += decoder.decode(value, { stream: true })
      const chunks = buffer.split('\n\n')
      buffer = chunks.pop() || '' //如果取出的是空字符串或其他假值，就使用 ''
      for (const chunk of chunks) {
        const line = chunk
          .split('\n')
          .map((item) => item.trim())
          .find((item) => item.startsWith('data:'))
        if (!line) {
          continue
        }
        const raw = line.slice(5).trim()
        if (!raw) {
          continue
        }
        const event = JSON.parse(raw)
        onEvent(event)
        if (event.type == 'done' || event.type == 'error') {
          return
        }
      }
    }
  } finally {
    try {
      await reader.cancel()
    } finally {
      reader.releaseLock()
    }
  }
}
