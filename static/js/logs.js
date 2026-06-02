const { createApp, ref, computed, onMounted, onUnmounted, nextTick } = Vue;

const app = createApp({
    setup() {
        const logs = ref([]);
        const isConnected = ref(false);
        const autoScroll = ref(true);
        const filter = ref('all');
        const logBody = ref(null);
        let eventSource = null;
        
        // 过滤日志
        const filteredLogs = computed(() => {
            if (filter.value === 'all') return logs.value;
            if (filter.value === 'error') {
                return logs.value.filter(log => log.level === 'error');
            }
            return logs.value.filter(log => log.category === filter.value);
        });
        
        // 连接SSE
        const connectSSE = () => {
            if (eventSource) {
                eventSource.close();
            }
            
            eventSource = new EventSource('/api/logs/stream');
            
            eventSource.onopen = () => {
                isConnected.value = true;
            };
            
            eventSource.onmessage = (event) => {
                try {
                    const log = JSON.parse(event.data);
                    logs.value.push(log);
                    
                    // 限制日志数量
                    if (logs.value.length > 2000) {
                        logs.value = logs.value.slice(-1500);
                    }
                    
                    // 自动滚动
                    if (autoScroll.value) {
                        nextTick(() => {
                            if (logBody.value) {
                                logBody.value.scrollTop = logBody.value.scrollHeight;
                            }
                        });
                    }
                } catch (e) {
                    console.error('Parse log error:', e);
                }
            };
            
            eventSource.onerror = () => {
                isConnected.value = false;
                // 自动重连
                setTimeout(() => {
                    if (eventSource.readyState === EventSource.CLOSED) {
                        connectSSE();
                    }
                }, 3000);
            };
        };
        
        // 格式化时间
        const formatTime = (timestamp) => {
            const date = new Date(timestamp * 1000);
            return date.toLocaleTimeString('zh-CN', { 
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit' 
            });
        };
        
        // 切换自动滚动
        const toggleAutoScroll = () => {
            autoScroll.value = !autoScroll.value;
            if (autoScroll.value) {
                nextTick(() => {
                    if (logBody.value) {
                        logBody.value.scrollTop = logBody.value.scrollHeight;
                    }
                });
            }
        };
        
        // 清空日志
        const clearLogs = async () => {
            try {
                await ElementPlus.ElMessageBox.confirm(
                    '确定要清空所有日志吗？',
                    '确认清空',
                    {
                        confirmButtonText: '确定',
                        cancelButtonText: '取消',
                        type: 'warning'
                    }
                );
                
                logs.value = [];
                await fetch('/api/logs', { method: 'DELETE' });
                ElementPlus.ElMessage.success('日志已清空');
            } catch (error) {
                if (error !== 'cancel') {
                    ElementPlus.ElMessage.error('清空失败');
                }
            }
        };
        
        onMounted(() => {
            connectSSE();
        });
        
        onUnmounted(() => {
            if (eventSource) {
                eventSource.close();
            }
        });
        
        return {
            logs,
            isConnected,
            autoScroll,
            filter,
            logBody,
            filteredLogs,
            formatTime,
            toggleAutoScroll,
            clearLogs
        };
    }
});

app.use(ElementPlus);
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
}
registerGlobalComponents(app);
app.mount('#app');
