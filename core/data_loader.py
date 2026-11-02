import asyncio
import json
from collections import defaultdict
from pathlib import Path


class FactorioDataLoader:
    """Асинхронный загрузчик данных Factorio с индексами для быстрого поиска."""

    def __init__(self, items_path: str | Path, recipes_path: str | Path):
        self.items_path = Path(items_path)
        self.recipes_path = Path(recipes_path)

        self.items_data: dict = {}
        self.recipes_data: dict = {}

        # Индексы прототипов
        self.prototype_index: dict = {}
        self.prototype_name_index: dict = defaultdict(list)
        self.prototype_category_index: dict = defaultdict(list)

        # Индексы рецептов
        self.recipe_index: dict = {}
        self.recipe_category_index: dict = defaultdict(list)
        self.ingredient_index: dict = defaultdict(list)
        self.result_index: dict = defaultdict(list)

    # --------------------------------------------------
    # 1. Чтение и асинхронная загрузка JSON
    # --------------------------------------------------

    @staticmethod
    def _read_json(path: Path) -> dict:
        """Синхронно читает JSON; вызывается через asyncio.to_thread."""
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    async def load_json(self, path: str | Path) -> dict:
        """Асинхронно загружает JSON по указанному пути."""
        path = Path(path)

        if not path.is_file():
            raise FileNotFoundError(f"Файл не найден: {path}")

        try:
            data = await asyncio.to_thread(self._read_json, path)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Ошибка JSON в файле {path}: {error}"
            ) from error

        if not isinstance(data, dict):
            raise TypeError(f"Корень JSON-файла должен быть объектом: {path}")

        return data

    async def load(self):
        """Параллельно загружает оба файла, проверяет их и строит индексы."""
        self.items_data, self.recipes_data = await asyncio.gather(
            self.load_json(self.items_path),
            self.load_json(self.recipes_path),
        )

        self._validate_data()
        self.build_prototype_indexes()
        self.build_recipe_indexes()

        print("Данные Factorio успешно загружены.")
        print("Индексы успешно построены.")
        return self

    async def load_all(self):
        """Совместимость с прежним названием метода загрузки."""
        return await self.load()

    # --------------------------------------------------
    # 2. Проверка структуры данных
    # --------------------------------------------------

    def _validate_data(self):
        if not isinstance(self.items_data.get("prototypes"), dict):
            raise TypeError(
                "В factorio_items.json отсутствует или имеет неверный тип 'prototypes'"
            )

        if not isinstance(self.recipes_data.get("recipes"), dict):
            raise TypeError(
                "В factorio_recipes.json отсутствует или имеет неверный тип 'recipes'"
            )

    # --------------------------------------------------
    # 3. Индексация прототипов
    # --------------------------------------------------

    def build_prototype_indexes(self):
        """Создаёт индексы: (категория, имя), имя и категория -> прототипы."""
        self.prototype_index.clear()
        self.prototype_name_index.clear()
        self.prototype_category_index.clear()

        prototypes = self.items_data["prototypes"]

        for category, objects in prototypes.items():
            if not isinstance(objects, dict):
                continue

            for name, prototype in objects.items():
                self.prototype_index[(category, name)] = prototype
                record = {
                    "category": category,
                    "name": name,
                    "data": prototype,
                }
                self.prototype_name_index[name].append(record)
                self.prototype_category_index[category].append(record)

    # --------------------------------------------------
    # 4. Индексация рецептов
    # --------------------------------------------------

    @staticmethod
    def _get_component_name(component) -> str | None:
        """Извлекает имя ингредиента/результата из поддерживаемых форм."""
        if isinstance(component, dict):
            name = component.get("name")
            return name if isinstance(name, str) else None
        # В некоторых выгрузках элемент может быть представлен строкой.
        if isinstance(component, str):
            return component
        return None

    def build_recipe_indexes(self):
        """Создаёт индексы рецептов, категорий, ингредиентов и результатов."""
        self.recipe_index.clear()
        self.recipe_category_index.clear()
        self.ingredient_index.clear()
        self.result_index.clear()

        recipes = self.recipes_data["recipes"]

        for name, recipe in recipes.items():
            if not isinstance(recipe, dict):
                continue

            self.recipe_index[name] = recipe
            category = recipe.get("category", "unknown")
            self.recipe_category_index[category].append(name)

            for ingredient in recipe.get("ingredients", []):
                ingredient_name = self._get_component_name(ingredient)
                if ingredient_name:
                    self.ingredient_index[ingredient_name].append(name)

            for result in recipe.get("results", []):
                result_name = self._get_component_name(result)
                if result_name:
                    self.result_index[result_name].append(name)

    # --------------------------------------------------
    # 5. Получение прототипов и рецептов
    # --------------------------------------------------

    def get_prototype(self, name: str, category: str | None = None):
        """Возвращает прототип по имени; без категории возвращает все совпадения."""
        if category is not None:
            return self.prototype_index.get((category, name))
        return self.prototype_name_index.get(name, [])

    def get_recipe(self, name: str):
        return self.recipe_index.get(name)

    def get_recipes_by_category(self, category: str):
        return [
            self.recipe_index[name]
            for name in self.recipe_category_index.get(category, [])
        ]

    def get_recipes_by_ingredient(self, ingredient: str):
        return [
            self.recipe_index[name]
            for name in self.ingredient_index.get(ingredient, [])
        ]

    def get_recipes_by_result(self, result: str):
        return [
            self.recipe_index[name]
            for name in self.result_index.get(result, [])
        ]

    def get_recipe_ingredients(self, recipe_name: str):
        recipe = self.get_recipe(recipe_name)
        return recipe.get("ingredients", []) if recipe else []

    def get_recipe_results(self, recipe_name: str):
        recipe = self.get_recipe(recipe_name)
        return recipe.get("results", []) if recipe else []

    # --------------------------------------------------
    # 6. Статистика
    # --------------------------------------------------

    def get_statistics(self):
        return {
            "prototype_count": len(self.prototype_index),
            "prototype_categories": len(self.prototype_category_index),
            "recipe_count": len(self.recipe_index),
            "recipe_categories": len(self.recipe_category_index),
        }
