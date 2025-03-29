# 中餐知识图谱聊天机器人
- 本项目将中餐食材、口味、技巧、制作步骤等信息存入知识图谱数据库。
- 大模型将知识图谱数据库作为一个工具进行查询，保证信息准确性。
- 对话中添加工具调用过程，方便用户查看知识图谱数据。

# 使用步骤
- 配置信息
  - 将config.example.py重命名为config.py，并填写相关信息
- 预处理数据
  - python preprocess_data.py
- 构建知识图谱
  - python insert_data_neo4j.py
- 启动服务
  - python gradio_server.py

# 效果展示


# 数据来源
- https://github.com/ngl567/CookBook-KG