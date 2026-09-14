/**
 * 浏览器端的复制 / 下载小工具。
 *
 * 复制优先用异步剪贴板 API；在非安全上下文（例如用局域网 IP 打开的 http 页面）
 * 里 navigator.clipboard 不可用，退回到临时的 textarea + execCommand。
 */

export async function copyText(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* 落到下面的兜底方案 */
  }

  try {
    const area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.top = '-1000px';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand('copy');
    area.remove();
    return ok;
  } catch {
    return false;
  }
}

/** 触发一次文本文件下载（用于导出 BibTeX 等） */
export function downloadText(filename, text, mime = 'application/x-bibtex;charset=utf-8') {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // 稍后再释放，避免部分浏览器还没开始读取就失效
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
