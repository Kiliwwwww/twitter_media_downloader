#!/usr/bin/env python3
"""
测试Flask应用
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000"

def test_index():
    """测试首页"""
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("✓ 首页访问成功")
            return True
        else:
            print(f"✗ 首页访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 连接失败: {e}")
        return False

def test_download_api():
    """测试下载API"""
    try:
        # 测试无效用户ID
        response = requests.post(f"{BASE_URL}/api/download", json={"user_id": ""})
        if response.status_code == 400:
            print("✓ 空用户ID验证成功")
        
        # 测试有效用户ID（注意：这会启动真实的下载任务）
        test_user = "twitter"  # 使用官方账号测试
        response = requests.post(f"{BASE_URL}/api/download", json={"user_id": test_user})
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"✓ 下载任务创建成功: {task_id}")
            
            # 测试进度查询
            time.sleep(2)
            response = requests.get(f"{BASE_URL}/api/progress/{task_id}")
            if response.status_code == 200:
                progress_data = response.json()
                print(f"✓ 进度查询成功: {progress_data.get('status')}")
            
            return True
        else:
            print(f"✗ 下载任务创建失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API测试失败: {e}")
        return False

def main():
    """运行测试"""
    print("开始测试...")
    print("-" * 50)
    
    if test_index():
        test_download_api()
    
    print("-" * 50)
    print("测试完成")

if __name__ == '__main__':
    main()