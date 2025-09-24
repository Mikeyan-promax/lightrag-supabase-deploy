#!/usr/bin/env python3
"""
安装PostgreSQL pgvector扩展的脚本
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def install_pgvector():
    """安装pgvector扩展"""
    # 从环境变量获取数据库连接信息
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = int(os.getenv('POSTGRES_PORT', 5432))
    user = os.getenv('POSTGRES_USER', 'lightrag_user')
    password = os.getenv('POSTGRES_PASSWORD', '20051102')
    database = os.getenv('POSTGRES_DATABASE', 'lightrag_db')
    
    print(f"连接到PostgreSQL数据库: {host}:{port}/{database}")
    
    try:
        # 连接到数据库
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
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
                print("可能需要以超级用户身份安装pgvector扩展")
                print("请联系数据库管理员或使用以下命令:")
                print(f"psql -h {host} -p {port} -U postgres -d {database} -c \"CREATE EXTENSION IF NOT EXISTS vector;\"")
                return False
        
        # 验证vector类型是否可用
        try:
            await conn.execute("SELECT 'vector'::regtype;")
            print("vector数据类型验证成功！")
        except Exception as e:
            print(f"vector数据类型验证失败: {e}")
            return False
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(install_pgvector())
    if success:
        print("\n✅ pgvector扩展安装和验证完成！")
    else:
        print("\n❌ pgvector扩展安装失败！")