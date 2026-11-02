from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk

from core.production_calculator import ProductionCalculator


class FactorioHelperApp(ctk.CTk):
    def __init__(self, loader):
        super().__init__()
        self.loader = loader
        self.calculator = ProductionCalculator(loader)
        self.title("Factorio Helper")
        self.geometry("1180x760")
        self.minsize(920, 620)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.prototypes = loader.items_data.get("prototypes", {})
        self.item_names = self._get_item_names()
        self.recipe_names = sorted(loader.recipe_index.keys())

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=14)
        self.items_tab = self.tabs.add("Предметы")
        self.recipes_tab = self.tabs.add("Рецепты")
        self.calc_tab = self.tabs.add("Производство / сек")
        self._build_items_tab()
        self._build_recipes_tab()
        self._build_calculator_tab()

    def _get_item_names(self):
        names = set()
        for category in ("item", "item-with-entity-data", "item-with-label", "tool", "module", "ammo"):
            objects = self.prototypes.get(category, {})
            if isinstance(objects, dict):
                names.update(objects.keys())
        # Добавляем предметы, встречающиеся в рецептах, даже если прототип не найден.
        names.update(self.loader.result_index.keys())
        names.update(self.loader.ingredient_index.keys())
        return sorted(names)

    @staticmethod
    def _pretty(value):
        if isinstance(value, dict):
            return "\n".join(f"{k}: {FactorioHelperApp._pretty(v)}" for k, v in value.items())
        if isinstance(value, list):
            return "\n".join(f"• {FactorioHelperApp._pretty(v)}" for v in value)
        return str(value)

    def _build_items_tab(self):
        self.items_tab.grid_columnconfigure(1, weight=1)
        self.items_tab.grid_rowconfigure(1, weight=1)
        top = ctk.CTkFrame(self.items_tab)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.item_search = ctk.CTkEntry(top, placeholder_text="Поиск предмета по внутреннему имени…")
        self.item_search.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        ctk.CTkButton(top, text="Найти", command=self._search_items).pack(side="left", padx=8)

        self.item_list = ctk.CTkScrollableFrame(self.items_tab, width=280)
        self.item_list.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        self.item_details = ctk.CTkTextbox(self.items_tab, wrap="word")
        self.item_details.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))
        self._populate_item_list(self.item_names[:250])

    def _populate_item_list(self, names):
        for child in self.item_list.winfo_children():
            child.destroy()
        for name in names:
            ctk.CTkButton(self.item_list, text=name, anchor="w", command=lambda n=name: self._show_item(n)).pack(fill="x", padx=4, pady=2)

    def _search_items(self):
        query = self.item_search.get().strip().lower()
        matches = [name for name in self.item_names if query in name.lower()] if query else self.item_names
        self._populate_item_list(matches[:500])

    def _show_item(self, name):
        self.item_details.delete("1.0", "end")
        matches = self.loader.get_prototype(name)
        self.item_details.insert("end", f"ПРЕДМЕТ: {name}\n\n")
        if matches:
            for record in matches:
                self.item_details.insert("end", f"Категория прототипа: {record['category']}\n")
                self.item_details.insert("end", self._pretty(record["data"]) + "\n\n")
        else:
            self.item_details.insert("end", "Прототип не найден в выгрузке.\n")
        recipe_names = self.loader.result_index.get(name, [])
        self.item_details.insert("end", "\nРЕЦЕПТЫ ПРОИЗВОДСТВА:\n")
        self.item_details.insert("end", "\n".join(recipe_names) if recipe_names else "Нет найденных рецептов.")

    def _build_recipes_tab(self):
        self.recipes_tab.grid_columnconfigure(1, weight=1)
        self.recipes_tab.grid_rowconfigure(1, weight=1)
        top = ctk.CTkFrame(self.recipes_tab)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.recipe_search = ctk.CTkEntry(top, placeholder_text="Поиск рецепта…")
        self.recipe_search.pack(side="left", fill="x", expand=True, padx=8, pady=8)
        ctk.CTkButton(top, text="Найти", command=self._search_recipes).pack(side="left", padx=8)
        self.recipe_list = ctk.CTkScrollableFrame(self.recipes_tab, width=280)
        self.recipe_list.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        self.recipe_details = ctk.CTkTextbox(self.recipes_tab, wrap="word")
        self.recipe_details.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))
        self._populate_recipe_list(self.recipe_names[:300])

    def _populate_recipe_list(self, names):
        for child in self.recipe_list.winfo_children():
            child.destroy()
        for name in names:
            ctk.CTkButton(self.recipe_list, text=name, anchor="w", command=lambda n=name: self._show_recipe(n)).pack(fill="x", padx=4, pady=2)

    def _search_recipes(self):
        query = self.recipe_search.get().strip().lower()
        matches = [name for name in self.recipe_names if query in name.lower()] if query else self.recipe_names
        self._populate_recipe_list(matches[:500])

    def _show_recipe(self, name):
        recipe = self.loader.get_recipe(name) or {}
        self.recipe_details.delete("1.0", "end")
        self.recipe_details.insert("end", f"РЕЦЕПТ: {name}\n\n")
        self.recipe_details.insert("end", f"Категория: {recipe.get('category', 'не указана')}\n")
        self.recipe_details.insert("end", f"Время: {recipe.get('energy_required', 0.5)} сек.\n")
        self.recipe_details.insert("end", f"Ингредиенты:\n{self._pretty(recipe.get('ingredients', []))}\n\n")
        self.recipe_details.insert("end", f"Результаты:\n{self._pretty(recipe.get('results', []))}\n\n")
        self.recipe_details.insert("end", "Полные данные рецепта:\n" + self._pretty(recipe))

    def _build_calculator_tab(self):
        self.calc_tab.grid_columnconfigure(0, weight=1)
        self.calc_tab.grid_rowconfigure(2, weight=1)
        controls = ctk.CTkFrame(self.calc_tab)
        controls.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        controls.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(controls, text="Целевой предмет:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.target_combo = ctk.CTkComboBox(controls, values=self.item_names, width=320)
        self.target_combo.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        if self.item_names:
            self.target_combo.set("iron-gear-wheel" if "iron-gear-wheel" in self.item_names else self.item_names[0])
        ctk.CTkLabel(controls, text="Количество в секунду:").grid(row=0, column=2, padx=8, pady=8)
        self.rate_entry = ctk.CTkEntry(controls, width=100)
        self.rate_entry.insert(0, "1")
        self.rate_entry.grid(row=0, column=3, padx=8, pady=8)
        ctk.CTkButton(controls, text="Рассчитать", command=self._calculate).grid(row=0, column=4, padx=8, pady=8)

        self.calc_summary = ctk.CTkLabel(self.calc_tab, text="Укажи предмет и требуемое количество в секунду.", anchor="w")
        self.calc_summary.grid(row=1, column=0, sticky="ew", padx=14, pady=4)
        self.calc_output = ctk.CTkTextbox(self.calc_tab, wrap="word")
        self.calc_output.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

    def _calculate(self):
        target = self.target_combo.get().strip()
        try:
            rate = float(self.rate_entry.get().replace(",", "."))
            plan = self.calculator.calculate(target, rate)
        except (ValueError, TypeError) as error:
            self.calc_summary.configure(text=f"Ошибка расчёта: {error}")
            return

        self.calc_output.delete("1.0", "end")
        self.calc_summary.configure(text=f"План производства: {target} — {rate:g} шт./с")
        self.calc_output.insert("end", "СЫРЬЁ / РЕСУРСЫ В СЕКУНДУ\n")
        if plan.raw_resources:
            for name, amount in sorted(plan.raw_resources.items()):
                self.calc_output.insert("end", f"  {name}: {amount:.4f} /с\n")
        else:
            self.calc_output.insert("end", "  Не требуется или не удалось определить.\n")

        self.calc_output.insert("end", "\nРЕЦЕПТЫ И ЧАСТОТА ЗАПУСКА\n")
        for name, crafts in sorted(plan.recipe_rates.items()):
            self.calc_output.insert("end", f"  {name}: {crafts:.4f} крафтов/с\n")

        self.calc_output.insert("end", "\nПРОИЗВОДСТВЕННЫЕ МАШИНЫ\n")
        for name, count in sorted(plan.machine_counts.items()):
            self.calc_output.insert("end", f"  {name}: {count:.3f} шт. (округлить вверх: {int(count + 0.999999)})\n")
        if plan.warnings:
            self.calc_output.insert("end", "\nПРЕДУПРЕЖДЕНИЯ\n")
            for warning in plan.warnings:
                self.calc_output.insert("end", f"  • {warning}\n")
        self.calc_output.insert("end", "\nПримечание: расчёт базовый, без модулей, маяков, бонусов исследований и выбора альтернативных рецептов.")
