import json
import re

data_path = "data/entities_item_mimini.json"

category_data = {}
dish_data = {}

step_pattern = """食材准备：
{}
{}
{}

开始制作：
{}
"""

with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)
    for key, value in data.items():
        if re.match("^[0-9]", key):
            key = key.split("-")[-1].strip()
            category_data[key] = []
            # print(key, value)
            for dish in value["子菜品"]:
                dish = dish.split(".")[-1].strip()
                category_data[key].append(dish)
        else:
            Step = step_pattern.format("\n".join(data[key].get("主料", ""))
                               , "\n".join(data[key].get("辅料", "")),
                               "\n".join(data[key].get("配料", "")),
                               "\n".join(data[key].get("制作步骤", "")))
            Ingredient = data[key].get("主料", []) + data[key].get("辅料", []) + data[key].get("配料", [])
            Ingredient = [_.split(":")[0].strip() for _ in Ingredient]
            for _ in data[key].get("特色", []):
                if "口味" in _:
                    Flavor = _.split(":")[-1].strip()
                elif "工艺" in _:
                    Technique = _.split(":")[-1].strip()
                elif "耗时" in _:
                    Time = _.split(":")[-1].strip()
                elif "难度" in _:
                    Difficulty = _.split(":")[-1].strip()
            dish_data[key] = {
                "Step": Step,
                "Ingredient": Ingredient,
                "Flavor": Flavor,
                "Technique": Technique,
                "Time": Time,
                "Difficulty": Difficulty
            }

with open("data/category_data.json", "w", encoding="utf-8") as f:
    json.dump(category_data, f, ensure_ascii=False, indent=4)

with open("data/dish_data.json", "w", encoding="utf-8") as f:
    json.dump(dish_data, f, ensure_ascii=False, indent=4)


