#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动安装pgvector扩展的简化脚本
当自动安装遇到权限问题时使用
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def download_pgvector_source():
    """
    下载pgvector源码到当前目录
    """
    print("下载pgvector源码...")
    
    # 检查是否已存在
    if os.path.exists("pgvector"):
        print("✅ pgvector目录已存在")
        return True
    
    try:
        # 克隆仓库
        subprocess.run([
            "git", "clone", "--branch", "v0.8.0", 
            "https://github.com/pgvector/pgvector.git"
        ], check=True)
        print("✅ pgvector源码下载成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 下载失败: {e}")
        return False

def compile_pgvector():
    """
    编译pgvector扩展
    """
    print("编译pgvector扩展...")
    
    if not os.path.exists("pgvector"):
        print("❌ pgvector目录不存在")
        return False
    
    # 切换到pgvector目录
    original_dir = os.getcwd()
    os.chdir("pgvector")
    
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['PGROOT'] = 'D:\\APP\\postgres'
        
        # 创建构建脚本
        build_script = '''
@echo off
set "PGROOT=D:\\APP\\postgres"
call "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvars64.bat"
nmake /F Makefile.win
'''
        
        with open("build_only.bat", 'w', encoding='utf-8') as f:
            f.write(build_script)
        
        # 只编译，不安装
        result = subprocess.run(
            ["build_only.bat"], 
            shell=True, 
            capture_output=True, 
            text=True,
            env=env
        )
        
        if result.returncode == 0:
            print("✅ pgvector编译成功")
            
            # 检查生成的文件
            dll_file = "vector.dll"
            control_file = "vector.control"
            sql_file = "vector--0.8.0.sql"
            
            if os.path.exists(dll_file) and os.path.exists(control_file):
                print(f"✅ 找到编译文件: {dll_file}, {control_file}")
                return True
            else:
                print("❌ 编译文件不完整")
                return False
        else:
            print(f"❌ 编译失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 编译过程中发生错误: {e}")
        return False
    finally:
        os.chdir(original_dir)

def manual_install_instructions():
    """
    提供手动安装说明
    """
    print("\n" + "=" * 60)
    print("手动安装说明")
    print("=" * 60)
    
    print("\n由于权限限制，需要手动完成以下步骤:")
    print("\n1. 以管理员身份打开命令提示符或PowerShell")
    print("\n2. 执行以下命令复制文件:")
    
    current_dir = os.getcwd()
    pgvector_dir = os.path.join(current_dir, "pgvector")
    
    print(f'\n   copy "{pgvector_dir}\\vector.dll" "D:\\APP\\postgres\\lib\\"')
    print(f'   copy "{pgvector_dir}\\vector.control" "D:\\APP\\postgres\\share\\extension\\"')
    print(f'   copy "{pgvector_dir}\\vector--*.sql" "D:\\APP\\postgres\\share\\extension\\"')
    
    print("\n3. 重启PostgreSQL服务:")
    print("   net stop postgresql-x64-15")
    print("   net start postgresql-x64-15")
    
    print("\n4. 连接到lightrag数据库并创建扩展:")
    print('   psql -h localhost -U postgres -d lightrag -c "CREATE EXTENSION vector;"')
    
    print("\n或者运行验证脚本:")
    print(f'   python "{current_dir}\\LightRAG-1.4.6\\test_postgres_connection.py"')

def create_install_batch():
    """
    创建管理员安装批处理文件
    """
    print("创建管理员安装脚本...")
    
    current_dir = os.getcwd()
    pgvector_dir = os.path.join(current_dir, "pgvector")
    
    batch_content = f'''@echo off
echo 正在安装pgvector扩展...
echo.

REM 复制DLL文件
echo 复制vector.dll...
copy "{pgvector_dir}\\vector.dll" "D:\\APP\\postgres\\lib\\" /Y
if %errorlevel% neq 0 (
    echo 错误: 无法复制vector.dll
    pause
    exit /b 1
)

REM 复制控制文件
echo 复制vector.control...
copy "{pgvector_dir}\\vector.control" "D:\\APP\\postgres\\share\\extension\\" /Y
if %errorlevel% neq 0 (
    echo 错误: 无法复制vector.control
    pause
    exit /b 1
)

REM 复制SQL文件
echo 复制SQL文件...
copy "{pgvector_dir}\\vector--*.sql" "D:\\APP\\postgres\\share\\extension\\" /Y
if %errorlevel% neq 0 (
    echo 错误: 无法复制SQL文件
    pause
    exit /b 1
)

echo.
echo [OK] 文件复制完成!
echo.
echo 正在重启PostgreSQL服务...
net stop postgresql-x64-15
net start postgresql-x64-15

echo.
echo [OK] pgvector扩展安装完成!
echo 现在可以在数据库中使用 CREATE EXTENSION vector; 命令了
echo.
pause
'''
    
    batch_file = "install_pgvector_admin.bat"
    with open(batch_file, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"[OK] 创建了管理员安装脚本: {batch_file}")
    print("\n请右键点击此文件，选择'以管理员身份运行'")
    
    return batch_file

def check_compiled_files():
    """
    检查编译后的文件是否存在
    """
    pgvector_dir = "pgvector"
    if not os.path.exists(pgvector_dir):
        return False
    
    required_files = [
        os.path.join(pgvector_dir, "vector.dll"),
        os.path.join(pgvector_dir, "vector.control")
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ 缺少文件: {file_path}")
            return False
    
    print("✅ 所有必需的编译文件都存在")
    return True

def main():
    """
    主函数
    """
    print("=" * 60)
    print("pgvector手动安装助手")
    print("=" * 60)
    
    # 检查是否已有编译文件
    if check_compiled_files():
        print("发现已编译的pgvector文件")
        create_install_batch()
        manual_install_instructions()
        return
    
    # 下载源码
    if not download_pgvector_source():
        print("❌ 下载源码失败")
        sys.exit(1)
    
    # 编译
    if not compile_pgvector():
        print("❌ 编译失败")
        sys.exit(1)
    
    # 创建安装脚本
    batch_file = create_install_batch()
    
    # 提供手动安装说明
    manual_install_instructions()
    
    print("\n" + "=" * 60)
    print("下一步操作:")
    print("=" * 60)
    print(f"1. 右键点击 '{batch_file}' 文件")
    print("2. 选择 '以管理员身份运行'")
    print("3. 等待安装完成")
    print("4. 运行测试脚本验证安装")

if __name__ == "__main__":
    main()