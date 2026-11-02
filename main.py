import asyncio
from pathlib import Path

from core.data_loader import FactorioDataLoader
from ui.main_window import FactorioHelperApp


BASE_DIR = Path(__file__).resolve().parent


def main():
    loader = FactorioDataLoader(
        items_path=BASE_DIR / "data" / "factorio_items.json",
        recipes_path=BASE_DIR / "data" / "factorio_recipes.json",
    )
    asyncio.run(loader.load())

    app = FactorioHelperApp(loader)
    app.mainloop()


if __name__ == "__main__":
    main()
