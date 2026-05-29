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
        let startTime = null;
        
        const statusText = computed(() => {
            switch (status.value) {
                case 'pending':
                    return '等待中';
                case 'downloading':
                    return '下载中';
                case 'completed':
                    return '下载完成';
                case 'failed':
                    return '下载失败';
                default:
                    return '未知状态';
            }
        });
        
        const progressBarClass = computed(() => {
            switch (status.value) {
                case 'downloading':
                    return 'bg-primary';
                case 'completed':
                    return 'bg-success';
                case 'failed':
                    return 'bg-danger';
                default:
                    return 'bg-warning';
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
                        if (progressInterval) {
                            clearInterval(progressInterval);
                            progressInterval = null;
                        }
                    }
                } else {
                    console.error('获取进度失败:', data.error);
                }
            } catch (error) {
                console.error('请求失败:', error);
            }
        };
        
        const startDownload = async () => {
            if (!userId.value.trim()) {
                alert('请输入用户ID');
                return;
            }
            
            isDownloading.value = true;
            status.value = 'pending';
            progress.value = 0;
            totalFiles.value = 0;
            downloadedFiles.value = 0;
            errorMessage.value = '';
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
                    // 同时更新已用时间
                    setInterval(updateElapsedTime, 1000);
                } else {
                    alert(data.error || '下载失败');
                    isDownloading.value = false;
                }
            } catch (error) {
                alert('请求失败: ' + error.message);
                isDownloading.value = false;
            }
        };
        
        onUnmounted(() => {
            if (progressInterval) {
                clearInterval(progressInterval);
            }
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
            progressBarClass,
            startDownload
        };
    }
});

app.mount('#app');