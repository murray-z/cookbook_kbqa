
import gradio as gr
import json

from openai import OpenAI
from py2neo import Graph, Node, Relationship
from config import *

# 连接 Neo4j
graph = Graph(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


system_prompt = """
你是一个中餐知识图谱的智能助手，名字叫‘小雷’，有一个neo4j的中餐知识图谱数据库，可以供你查询，以回答用户的问题。

# Neo4j数据库结构
- Node: Category
    - 菜品大类，例如：红烧肉类、意大利面类
    - 属性
        - name: 菜品大类的名称
- Node: Dish
    - 具体的菜品，例如：元宝红烧肉、蕃茄火腿意面
    - 属性
        - name: 菜品的名称
        - Flavor: 菜品的口味
        - Technique: 菜品的烹饪技巧
        - Time: 菜品的烹饪时间
        - Difficulty: 菜品的烹饪难度
        - Step: 菜品的烹饪步骤
- Node: Ingredient
    - 菜品的食材，例如：五花肉、番茄、火腿
    - 属性
        - name: 食材的名称      
- Relationship: BELONGS_TO
    - 菜品属于某个菜品大类
- Relationship: CONTAINS
    - 菜品包含某个食材
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_neo4j_res",
            "description": "从菜谱知识图谱数据库获取相关查询结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "cypher_query": {
                        "type": "string",
                        "description": "Cypher 查询语句"
                    }
                },
                "required": ["cypher_query"]
            }
        }
    }
]


def get_neo4j_res(cypher_query):
    result = graph.run(cypher_query).data()
    return json.dumps(result, ensure_ascii=False, indent=2)


def llm(query, history):
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for user, bot in history[-3:]:
            messages.append({"role": "user", "content": user})
            messages.append({"role": "assistant", "content": bot})

    messages.append({"role": "user", "content": query})

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        stream=True
    )

    response = ""
    tool_calls = []

    for chunk in completion:
        if chunk.choices[0].finish_reason == "stop" and not chunk.choices[0].delta.content:
            print(chunk)
            break

        delta = chunk.choices[0].delta
        if delta.tool_calls:  # 检测工具调用
            tool_calls.extend(delta.tool_calls)
        elif delta.content:  # 正常文本输出
            response += delta.content
            yield response  # 逐步返回内容

    print(tool_calls)
    # 处理工具调用
    if tool_calls:
        args = ""
        func_name = ""
        for tool_call in tool_calls:
            chunk_args = tool_call.function.arguments
            if chunk_args:
                args += tool_call.function.arguments
            if tool_call.function.name:
                func_name = tool_call.function.name

        print(args, func_name)
        if func_name == "get_neo4j_res":
            arguments = json.loads(args)

            # 将系统提示包装为折叠项的 HTML
            tip_msg = (
                f"<details style='margin-bottom: 10px;'>"
                f"<summary style='font-size: 16px; color: #2c3e50;'>🔧【系统提示】调用工具 {func_name}，点击展开查看详情</summary>\n\n"
                f"<strong>调用参数：</strong>\n"
                f"<pre style='background-color: #f7f7f7; border: 1px solid #ccc; padding: 10px;'>{json.dumps(arguments, ensure_ascii=False, indent=2)}</pre>\n"
                f"</details>"
            )

            response += tip_msg
            yield response  # 返回折叠项的系统提示

            tool_response = get_neo4j_res(**arguments)
            print(f"tool_response: {tool_response}")

            tip_result = (
                f"<details style='margin-bottom: 10px;'>"
                f"<summary style='font-size: 16px; color: #2c3e50;'>🔧【系统提示】工具 {func_name} 返回结果，点击展开查看详情</summary>\n\n"
                f"<strong>返回结果：</strong>\n"
                f"<pre style='background-color: #f7f7f7; border: 1px solid #ccc; padding: 10px;'>{tool_response}</pre>\n"
                f"</details>"
            )

            response += tip_result
            yield response  # 返回折叠项的工具返回结果

            tool_calls = [{"id": "tool_call_1", "function": {"name": func_name, "arguments": args}}]

            messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
            messages.append({"role": "tool", "name": "get_neo4j_res", "content": tool_response})

            # 继续对话
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                stream=True
            )

            for chunk in completion:
                if chunk.choices[0].finish_reason == "stop" and not chunk.choices[0].delta.content:
                    break
                delta = chunk.choices[0].delta
                if delta.content:
                    response += delta.content
                    yield response  # 逐步返回最终内容


def chat_with_ai(user_input, history):
    response = ""
    for chunk in llm(user_input, history):
        response += chunk
        yield chunk  # 只返回增量


# 使用 Gradio Blocks API 创建界面
with gr.Blocks() as demo:
    gr.Markdown("""
# 🍜 中餐知识小助手 —— 小雷 👨‍🍳  

你好！我是 **小雷**，你的 **中餐智能助手**。我连接着一个 **强大的中餐知识图谱数据库**，可以帮助你探索 **中华美食的奥秘**！  

### 📚 **我能做什么？**  
✅ **推荐菜品**：不知道吃什么？我可以帮你挑选适合你的中餐美食！  
✅ **查询烹饪方法**：想自己动手做一道美味的菜？我可以提供详细的 **步骤、技巧、时间和难度**！  
✅ **食材搭配建议**：不确定某种食材怎么搭配？我可以告诉你 **哪些食材能碰撞出绝佳口感**！  

### 🏛 **我的知识库**  
📌 **菜品分类**：红烧肉类、意大利面类……各种风味应有尽有！  
📌 **菜品信息**：口味、烹饪技巧、制作时间、难度、详细步骤，一目了然！  
📌 **食材知识**：从五花肉到番茄，从火腿到秘制香料，食材搭配不再难！  

📢 **无论是探索经典中餐，还是寻找烹饪灵感，快来和小雷聊聊吧！** 🎉  
""")
    chatbot = gr.Chatbot()
    user_input = gr.Textbox(label="请输入你的问题")
    history = gr.State([])


    def respond(message, chat_history):
        chat_history.append((message, ""))  # 先占位
        for chunk in chat_with_ai(message, chat_history):
            chat_history[-1] = (message, chunk)  # 只更新最新的 chunk
            yield chat_history, chat_history, ""


    user_input.submit(respond, [user_input, history], [chatbot, history, user_input])

demo.launch(share=True)
