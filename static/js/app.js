const { createApp, ref, computed, onMounted, onUnmounted } = Vue;

const app = createApp({
    setup() {
        const userId = ref('');
        const taskId = ref('');
        const status = ref('pending');
        const progress = ref(0);
        const totalFiles = ref(0);
        const downloadedFiles = ref(0);
        const elapsedTime = ref('0秒');
        const errorMessage = ref('');
        const isDownloading = ref(false);
        
        let progressInterval = null;
        let timeInterval = null;
        let startTime = null;
        
        const statusText = computed(() => {
            switch (status.value) {
                case 'pending': return '等待中';
                case 'downloading': return '下载中';
                case 'completed': return '下载完成';
                case 'failed': return '下载失败';
                default: return '未知状态';
            }
        });
        
        const statusTagType = computed(() => {
            switch (status.value) {
                case 'pending': return 'warning';
                case 'downloading': return '';
                case 'completed': return 'success';
                case 'failed': return 'danger';
                default: return 'info';
            }
        });
        
        const progressStatus = computed(() => {
            switch (status.value) {
                case 'completed': return 'success';
                case 'failed': return 'exception';
                default: return '';
            }
        });
        
        const updateElapsedTime = () => {
            if (!startTime) return;
            
            const now = new Date();
            const diff = Math.floor((now - startTime) / 1000);
            
            if (diff < 60) {
                elapsedTime.value = `${diff}秒`;
            } else if (diff < 3600) {
                const minutes = Math.floor(diff / 60);
                const seconds = diff % 60;
                elapsedTime.value = `${minutes}分${seconds}秒`;
            } else {
                const hours = Math.floor(diff / 3600);
                const minutes = Math.floor((diff % 3600) / 60);
                elapsedTime.value = `${hours}小时${minutes}分`;
            }
        };
        
        const stopTimers = () => {
            if (progressInterval) {
                clearInterval(progressInterval);
                progressInterval = null;
            }
            if (timeInterval) {
                clearInterval(timeInterval);
                timeInterval = null;
            }
        };
        
        const fetchProgress = async () => {
            if (!taskId.value) return;
            
            try {
                const response = await fetch(`/api/progress/${taskId.value}`);
                const data = await response.json();
                
                if (response.ok) {
                    status.value = data.status;
                    progress.value = data.progress;
                    totalFiles.value = data.total_files;
                    downloadedFiles.value = data.downloaded_files;
                    errorMessage.value = data.error_message || '';
                    
                    if (data.status === 'completed' || data.status === 'failed') {
                        isDownloading.value = false;
                        stopTimers();
                    }
                }
            } catch (error) {
                console.error('请求失败:', error);
            }
        };
        
        const startDownload = async () => {
            if (!userId.value.trim()) {
                ElementPlus.ElMessage.warning('请输入用户ID');
                return;
            }
            
            isDownloading.value = true;
            status.value = 'pending';
            progress.value = 0;
            totalFiles.value = 0;
            downloadedFiles.value = 0;
            errorMessage.value = '';
            elapsedTime.value = '0秒';
            startTime = new Date();
            
            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: userId.value.trim()
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    taskId.value = data.task_id;
                    status.value = 'downloading';
                    
                    // 开始轮询进度
                    progressInterval = setInterval(fetchProgress, 1000);
                    // 更新已用时间
                    timeInterval = setInterval(updateElapsedTime, 1000);
                    
                    ElementPlus.ElMessage.success('下载任务已创建');
                } else {
                    ElementPlus.ElMessage.error(data.error || '下载失败');
                    isDownloading.value = false;
                }
            } catch (error) {
                ElementPlus.ElMessage.error('请求失败: ' + error.message);
                isDownloading.value = false;
            }
        };
        
        const downloadZip = () => {
            if (taskId.value) {
                window.location.href = `/api/download/${taskId.value}`;
            }
        };
        
        onUnmounted(() => {
            stopTimers();
        });
        
        return {
            userId,
            taskId,
            status,
            progress,
            totalFiles,
            downloadedFiles,
            elapsedTime,
            errorMessage,
            isDownloading,
            statusText,
            statusTagType,
            progressStatus,
            startDownload,
            downloadZip
        };
    }
});

app.use(ElementPlus);
app.mount('#app');