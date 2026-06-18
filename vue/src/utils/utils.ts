import i18n from './i18n'

/**
 * 格式化文件大小
 * @param bytes - 字节数
 * @returns 格式化后的文件大小
 */
export function formatFileSize(bytes: number): string {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let unitIndex = 0
  let size = bytes
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return size.toFixed(2) + ' ' + units[unitIndex]
}

/**
 * 获取状态文本
 * @param status - 状态值
 * @returns 状态文本
 */
export function getStatusText(status: string): string {
  return i18n.t(`status.${status}`) || i18n.t('status.unknown')
}

/**
 * 防抖函数
 * @param func - 要执行的函数
 * @param wait - 等待时间（毫秒）
 * @returns 防抖后的函数
 */
export function debounce<T extends (...args: any[]) => any>(func: T, wait = 300): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * 格式化时间
 * @param timestamp - 时间戳
 * @returns 格式化后的时间
 */
export function formatTime(timestamp: string | Date): string {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

/**
 * 计算耗时
 * @param seconds - 秒数
 * @returns 格式化后的耗时
 */
export function formatElapsedTime(seconds: number): string {
  const secondsText = i18n.t('time.seconds') || '秒'
  const minutesText = i18n.t('time.minutes') || '分'
  const hoursText = i18n.t('time.hours') || '小时'

  if (seconds < 60) return `${Math.floor(seconds)}${secondsText}`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}${minutesText}${Math.floor(seconds % 60)}${secondsText}`
  return `${Math.floor(seconds / 3600)}${hoursText}${Math.floor((seconds % 3600) / 60)}${minutesText}`
}
