from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProductionPlan:
    target: str
    target_rate: float
    raw_resources: dict[str, float] = field(default_factory=dict)
    recipe_rates: dict[str, float] = field(default_factory=dict)
    machine_counts: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class ProductionCalculator:
    """Базовый рекурсивный расчёт цепочки производства Factorio.

    Расчёт учитывает время рецепта, количество результатов и скорость машины.
    Не учитывает модули, маяки, бонусы исследований, качество, ограничения
    жидкостей/энергии и побочные продукты при выборе альтернативного рецепта.
    """

    MACHINE_CATEGORIES = (
        "assembling-machine", "furnace", "rocket-silo", "lab",
        "agricultural-tower", "biochamber", "foundry", "electromagnetic-plant",
        "cryogenic-plant", "chemical-plant", "oil-refinery",
    )

    def __init__(self, loader):
        self.loader = loader
        self.machines = self._collect_machines()

    @staticmethod
    def _component_name(component: Any) -> str | None:
        if isinstance(component, str):
            return component
        if isinstance(component, dict):
            value = component.get("name")
            return value if isinstance(value, str) else None
        return None

    @staticmethod
    def _amount(component: Any) -> float:
        if not isinstance(component, dict):
            return 1.0
        if "amount" in component:
            return float(component["amount"])
        if "amount_min" in component or "amount_max" in component:
            low = float(component.get("amount_min", component.get("amount_max", 1)))
            high = float(component.get("amount_max", low))
            return (low + high) / 2
        return 1.0

    def _collect_machines(self) -> list[dict]:
        result = []
        prototypes = self.loader.items_data.get("prototypes", {})
        for category in self.MACHINE_CATEGORIES:
            for name, data in prototypes.get(category, {}).items():
                if not isinstance(data, dict):
                    continue
                speed = data.get("crafting_speed")
                categories = data.get("crafting_categories", [])
                if isinstance(speed, (int, float)) and speed > 0:
                    result.append({
                        "name": name,
                        "category": category,
                        "speed": float(speed),
                        "crafting_categories": categories if isinstance(categories, list) else [],
                    })
        # Добавим прочие прототипы-машины, если у них есть нужные поля.
        known = {m["name"] for m in result}
        for category, objects in prototypes.items():
            if not isinstance(objects, dict):
                continue
            for name, data in objects.items():
                if name in known or not isinstance(data, dict):
                    continue
                speed = data.get("crafting_speed")
                cats = data.get("crafting_categories", [])
                if isinstance(speed, (int, float)) and speed > 0 and isinstance(cats, list):
                    result.append({"name": name, "category": category, "speed": float(speed), "crafting_categories": cats})
                    known.add(name)
        return result

    def _choose_recipe(self, item_name: str) -> tuple[str, dict] | None:
        names = self.loader.result_index.get(item_name, [])
        candidates = [(name, self.loader.recipe_index[name]) for name in names if name in self.loader.recipe_index]
        if not candidates:
            return None

        # Для обычного производства исключаем рецепты переработки и скрытые рецепты.
        # Если обычного рецепта нет, оставляем остальные варианты как запасной вариант.
        normal = [
            pair for pair in candidates
            if pair[1].get("category") not in {"recycling", "recycling-or-hand-crafting"}
            and not pair[1].get("hidden", False)
        ]
        if normal:
            candidates = normal

        # Сначала предпочитаем обычные рецепты с меньшим числом ингредиентов.
        def recipe_priority(pair):
            category = pair[1].get("category")
            if category in {"recycling", "recycling-or-hand-crafting"}:
                category_rank = 3
            elif category in (None, "crafting", "basic-crafting", "smelting"):
                category_rank = 0
            else:
                category_rank = 1
            return (
                category_rank,
                pair[1].get("hidden", False),
                len(pair[1].get("ingredients", [])),
            )

        candidates.sort(key=recipe_priority)
        return candidates[0]

    def _choose_machine(self, recipe: dict) -> dict | None:
        category = recipe.get("category", "crafting")
        compatible = [m for m in self.machines if category in m["crafting_categories"]]
        if not compatible:
            return None
        return max(compatible, key=lambda m: m["speed"])

    def calculate(self, target: str, target_per_second: float) -> ProductionPlan:
        if target_per_second <= 0:
            raise ValueError("Производительность должна быть больше нуля")
        plan = ProductionPlan(target=target, target_rate=target_per_second)
        visiting: set[str] = set()

        def expand(item_name: str, required_rate: float):
            if required_rate <= 0:
                return
            if item_name in visiting:
                plan.raw_resources[item_name] = plan.raw_resources.get(item_name, 0.0) + required_rate
                plan.warnings.append(f"Обнаружен цикл рецептов для {item_name}; ресурс учтён как сырьё.")
                return

            selected = self._choose_recipe(item_name)
            if selected is None:
                plan.raw_resources[item_name] = plan.raw_resources.get(item_name, 0.0) + required_rate
                return

            recipe_name, recipe = selected
            results = recipe.get("results", [])
            output_amount = sum(
                self._amount(component)
                for component in results
                if self._component_name(component) == item_name
            )
            if output_amount <= 0:
                plan.raw_resources[item_name] = plan.raw_resources.get(item_name, 0.0) + required_rate
                return

            crafts_per_second = required_rate / output_amount
            plan.recipe_rates[recipe_name] = plan.recipe_rates.get(recipe_name, 0.0) + crafts_per_second
            machine = self._choose_machine(recipe)
            craft_time = float(recipe.get("energy_required", 0.5) or 0.5)
            if machine:
                count = crafts_per_second * craft_time / machine["speed"]
                plan.machine_counts[machine["name"]] = plan.machine_counts.get(machine["name"], 0.0) + count
            else:
                plan.warnings.append(f"Не найдена машина для категории рецепта '{recipe.get('category', 'crafting')}' ({recipe_name}).")

            visiting.add(item_name)
            for ingredient in recipe.get("ingredients", []):
                ingredient_name = self._component_name(ingredient)
                if ingredient_name:
                    expand(ingredient_name, crafts_per_second * self._amount(ingredient))
            visiting.remove(item_name)

        expand(target, target_per_second)
        return plan
