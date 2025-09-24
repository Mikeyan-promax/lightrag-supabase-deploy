#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows环境下PostgreSQL pgvector扩展安装脚本
自动化安装pgvector扩展的完整流程
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def check_prerequisites():
    """
    检查安装前置条件
    """
    print("检查安装前置条件...")
    
    # 检查PostgreSQL安装
    postgres_paths = [
        "D:\\APP\\postgres",
        "C:\\Program Files\\PostgreSQL\\15",
        "C:\\Program Files\\PostgreSQL\\16",
        "C:\\Program Files\\PostgreSQL\\17"
    ]
    
    postgres_root = None
    for path in postgres_paths:
        if os.path.exists(path):
            postgres_root = path
            break
    
    if not postgres_root:
        print("❌ 未找到PostgreSQL安装目录")
        return None
    
    print(f"✅ 找到PostgreSQL安装目录: {postgres_root}")
    
    # 检查pg_config
    pg_config_path = os.path.join(postgres_root, "bin", "pg_config.exe")
    if not os.path.exists(pg_config_path):
        print(f"❌ 未找到pg_config: {pg_config_path}")
        return None
    
    print(f"✅ 找到pg_config: {pg_config_path}")
    
    # 检查Git
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        print("✅ Git已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git未安装，请先安装Git for Windows")
        print("下载地址: https://git-scm.com/download/win")
        return None
    
    return postgres_root

def check_visual_studio():
    """
    检查Visual Studio构建工具
    """
    print("检查Visual Studio构建工具...")
    
    # 常见的Visual Studio路径
    vs_paths = [
        "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvars64.bat",
        "C:\\Program Files\\Microsoft Visual Studio\\2022\\Professional\\VC\\Auxiliary\\Build\\vcvars64.bat",
        "C:\\Program Files\\Microsoft Visual Studio\\2022\\Enterprise\\VC\\Auxiliary\\Build\\vcvars64.bat",
        "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat",
        "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat"
    ]
    
    for vs_path in vs_paths:
        if os.path.exists(vs_path):
            print(f"✅ 找到Visual Studio构建工具: {vs_path}")
            return vs_path
    
    print("❌ 未找到Visual Studio构建工具")
    print("请安装Visual Studio 2022 Build Tools:")
    print("下载地址: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022")
    print("安装时请确保选择 'C++ build tools'")
    return None

def install_pgvector(postgres_root, vs_path):
    """
    安装pgvector扩展
    """
    print("开始安装pgvector扩展...")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"使用临时目录: {temp_dir}")
        
        # 克隆pgvector仓库
        print("正在下载pgvector源码...")
        clone_cmd = [
            "git", "clone", "--branch", "v0.8.0", 
            "https://github.com/pgvector/pgvector.git",
            os.path.join(temp_dir, "pgvector")
        ]
        
        try:
            subprocess.run(clone_cmd, check=True, capture_output=True)
            print("✅ pgvector源码下载成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ 下载pgvector源码失败: {e}")
            return False
        
        # 切换到pgvector目录
        pgvector_dir = os.path.join(temp_dir, "pgvector")
        os.chdir(pgvector_dir)
        
        # 设置环境变量
        env = os.environ.copy()
        env['PGROOT'] = postgres_root
        
        # 创建构建脚本
        build_script = f'''
@echo off
set "PGROOT={postgres_root}"
call "{vs_path}"
nmake /F Makefile.win
nmake /F Makefile.win install
'''
        
        script_path = os.path.join(pgvector_dir, "build.bat")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(build_script)
        
        print("正在编译和安装pgvector...")
        print("注意: 此过程需要管理员权限")
        
        try:
            # 运行构建脚本
            result = subprocess.run(
                [script_path], 
                shell=True, 
                capture_output=True, 
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                print("✅ pgvector编译和安装成功")
                return True
            else:
                print(f"❌ pgvector安装失败")
                print(f"错误输出: {result.stderr}")
                print(f"标准输出: {result.stdout}")
                return False
                
        except Exception as e:
            print(f"❌ 安装过程中发生错误: {e}")
            return False

def verify_installation():
    """
    验证pgvector安装
    """
    print("验证pgvector安装...")
    
    try:
        import psycopg2
        
        # 连接到lightrag数据库
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='123456',
            database='lightrag'
        )
        
        cursor = conn.cursor()
        
        # 尝试创建扩展
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            print("✅ pgvector扩展创建成功")
        except Exception as e:
            print(f"❌ 创建pgvector扩展失败: {e}")
            return False
        
        # 测试向量操作
        try:
            cursor.execute("SELECT '[1,2,3]'::vector;")
            result = cursor.fetchone()
            print(f"✅ 向量操作测试成功: {result[0]}")
        except Exception as e:
            print(f"❌ 向量操作测试失败: {e}")
            return False
        
        # 检查扩展版本
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        version = cursor.fetchone()
        if version:
            print(f"✅ pgvector版本: {version[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 验证过程中发生错误: {e}")
        return False

def main():
    """
    主函数
    """
    print("=" * 60)
    print("PostgreSQL pgvector扩展安装程序 (Windows)")
    print("=" * 60)
    
    # 检查是否以管理员身份运行
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("⚠️  建议以管理员身份运行此脚本")
    except:
        pass
    
    # 检查前置条件
    postgres_root = check_prerequisites()
    if not postgres_root:
        print("\n❌ 前置条件检查失败，请安装必要的软件后重试")
        sys.exit(1)
    
    # 检查Visual Studio
    vs_path = check_visual_studio()
    if not vs_path:
        print("\n❌ Visual Studio构建工具检查失败")
        print("\n替代方案: 您可以尝试使用预编译的pgvector二进制文件")
        print("或者使用Docker部署PostgreSQL with pgvector")
        sys.exit(1)
    
    # 安装pgvector
    print("\n" + "=" * 40)
    print("开始安装pgvector")
    print("=" * 40)
    
    success = install_pgvector(postgres_root, vs_path)
    if not success:
        print("\n❌ pgvector安装失败")
        sys.exit(1)
    
    # 验证安装
    print("\n" + "=" * 40)
    print("验证安装结果")
    print("=" * 40)
    
    if verify_installation():
        print("\n🎉 pgvector安装和配置完成!")
        print("现在可以在LightRAG中使用PostgreSQL作为向量数据库了")
    else:
        print("\n❌ pgvector验证失败")
        sys.exit(1)

if __name__ == "__main__":
    main()