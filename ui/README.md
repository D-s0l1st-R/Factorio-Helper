Factorio Helper UI (CustomTkinter)

1. Install into your .venv:
   .\.venv\Scripts\python.exe -m pip install customtkinter

2. Copy factorio_items.json and factorio_recipes.json into the data/ folder.

3. Run from the project root:
   .\.venv\Scripts\python.exe main.py

Tabs:
- Предметы: search prototype data and show recipes that produce the item.
- Рецепты: search recipes and inspect ingredients/results/category/time.
- Производство / сек: recursively estimate raw input rates and machine counts.

Calculation assumptions / limitations:
- Selects one available recipe automatically (fewest listed ingredients).
- Chooses the fastest compatible crafting machine found in the prototype dump.
- Uses recipe energy_required and machine crafting_speed.
- Does not yet model modules, beacons, research bonuses, quality, fluids/power,
  mining drill placement/ore richness, or exact alternate recipe selection.
- For amount_min/amount_max outputs, uses their average.
