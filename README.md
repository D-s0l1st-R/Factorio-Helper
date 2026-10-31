# Factorio-Helper

Use lib: 
    customtkinter 6.0.0 # ui
    Nuitka        4.3.3 # builder

my_app/
├── .venv/              # Виртуальное окружение (не в Git)
├── .gitignore
├── README.md
├── main.py             # Точка входа
├── ui/                 # Папка с интерфейсом (окна, виджеты)
│   ├── main_window.py
│   └── widgets.py
├── core/               # Папка с логикой и работой с JSON
│   ├── data_manager.py
│   └── utils.py
├── assets/             # Иконки, шрифты, картинки
│   └── icon.ico
└── data/               # Папка для JSON файлов (пользовательские данные)
    └── settings.json