#!/usr/bin/env python3
"""
使用超级用户权限安装PostgreSQL pgvector扩展的脚本
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def install_pgvector_as_admin():
    """使用超级用户权限安装pgvector扩展"""
    # 从环境变量获取数据库连接信息
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = int(os.getenv('POSTGRES_PORT', 5432))
    database = os.getenv('POSTGRES_DATABASE', 'lightrag_db')
    
    # 使用postgres超级用户
    admin_user = 'postgres'
    admin_password = '20051102'  # 假设与lightrag_user密码相同
    
    print(f"使用超级用户连接到PostgreSQL数据库: {host}:{port}/{database}")
    
    try:
        # 连接到数据库
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            database=database
        )
        
        print("数据库连接成功！")
        
        # 检查pgvector扩展是否已安装
        result = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
        )
        
        if result:
            print("pgvector扩展已经安装")
        else:
            print("正在安装pgvector扩展...")
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                print("pgvector扩展安装成功！")
            except Exception as e:
                print(f"安装pgvector扩展失败: {e}")
                print("可能需要先安装pgvector软件包")
                print("请参考: https://github.com/pgvector/pgvector#installation")
                return False
        
        # 验证vector类型是否可用
        try:
            await conn.execute("SELECT 'vector'::regtype;")
            print("vector数据类型验证成功！")
        except Exception as e:
            print(f"vector数据类型验证失败: {e}")
            return False
        
        # 给lightrag_user用户授权使用vector扩展
        lightrag_user = os.getenv('POSTGRES_USER', 'lightrag_user')
        try:
            await conn.execute(f"GRANT USAGE ON SCHEMA public TO {lightrag_user};")
            await conn.execute(f"GRANT CREATE ON SCHEMA public TO {lightrag_user};")
            print(f"已授权用户 {lightrag_user} 使用vector扩展")
        except Exception as e:
            print(f"授权失败: {e}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("请确保:")
        print("1. PostgreSQL服务正在运行")
        print("2. postgres用户密码正确")
        print("3. 数据库lightrag_db存在")
        return False

if __name__ == "__main__":
    success = asyncio.run(install_pgvector_as_admin())
    if success:
        print("\n✅ pgvector扩展安装和验证完成！")
    else:
        print("\n❌ pgvector扩展安装失败！")