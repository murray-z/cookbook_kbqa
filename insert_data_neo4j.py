import json
from py2neo import Graph, Node, Relationship
from config import *

# 连接 Neo4j
graph = Graph(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# 读取 JSON 数据
with open("./data/category_data.json", "r", encoding="utf-8") as f:
    category_data = json.load(f)

with open("./data/dish_data.json", "r", encoding="utf-8") as f:
    dish_data = json.load(f)

# 创建 Category 和 Dish 关系
for category, dishes in category_data.items():
    category_node = graph.nodes.match("Category", name=category).first()
    if not category_node:
        category_node = Node("Category", name=category)
        graph.create(category_node)

    for dish in dishes:
        dish_node = graph.nodes.match("Dish", name=dish).first()
        if not dish_node:
            dish_node = Node("Dish", name=dish)
            graph.create(dish_node)

        # 建立菜品与类别的关系
        rel = Relationship(dish_node, "BELONGS_TO", category_node)
        graph.create(rel)

# 创建 Dish、Ingredient 关系
for dish_name, dish_info in dish_data.items():
    dish_node = graph.nodes.match("Dish", name=dish_name).first()
    if not dish_node:
        dish_node = Node("Dish", name=dish_name)
        graph.create(dish_node)

    # 添加 Dish 属性
    dish_node["Flavor"] = dish_info["Flavor"]
    dish_node["Technique"] = dish_info["Technique"]
    dish_node["Time"] = dish_info["Time"]
    dish_node["Difficulty"] = dish_info["Difficulty"]
    dish_node["Step"] = dish_info["Step"]
    graph.push(dish_node)  # 更新节点信息

    # 处理食材
    for ingredient in dish_info["Ingredient"]:
        ingredient_node = graph.nodes.match("Ingredient", name=ingredient).first()
        if not ingredient_node:
            ingredient_node = Node("Ingredient", name=ingredient)
            graph.create(ingredient_node)

        # 建立 Dish -> Ingredient 关系
        rel = Relationship(dish_node, "CONTAINS", ingredient_node)
        graph.create(rel)

print("知识图谱创建完成！")
