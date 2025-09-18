# PhySO Service

Сервис для символьной регрессии на базе PhySO с простым биллингом и REST API.

## Возможности
- обучение моделей символьной регрессии через `PhySO`
- тарификация по количеству эпох (`base_price + epoch_price * epochs`)
- хранение пользователей, моделей и транзакций в SQLite
- синхронный FastAPI сервис (`main_sync.py`)
- Telegram-бот, который использует тот же API
- опциональное Streamlit-приложение для просмотра результатов

## Структура
```
PhySO-Service/
├── config/              # Конфигурационные модули (репозитории и т.п.)
├── core/
│   ├── entities/        # Pydantic-модели домена
│   └── repositories/    # Абстракции репозиториев
├── infra/
│   ├── db/              # Реализации репозиториев на SQLite
│   └── physo/           # Интеграция с PhySO
├── data/                # Папка для артефактов обучения (создаётся автоматически)
├── main_sync.py         # Основной FastAPI сервис
└── streamlit_app.py     # Пример Streamlit UI (опционально)
```

## Запуск
1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Запустите API (порт по умолчанию `53251`):
   ```bash
   python main_sync.py
   ```

После старта сервис предоставляет REST API по адресу `http://127.0.0.1:53251/api/v1`.

## Пример запроса
```python
import requests

payload = {
    "user_id": 1,
    "input_data": "x,y\n1,2\n2,4\n3,6\n4,8",
    "y_name": "y",
    "x_names": ["x"],
    "epochs": 50,
    "run_config": "config0"
}

response = requests.post(
    "http://127.0.0.1:53251/api/v1/predictions/",
    headers={"X-API-KEY": "your-api-key"},
    json=payload,
)

result = response.json()
print(result["best_formula"], result["best_r2"])

if result.get("pareto_csv"):
    print("Pareto CSV:", result["pareto_csv"]["filename"])
```

При успешном обучении в папке `data/` появятся файлы `SR_curves_pareto.csv`, `SR_curves_data.csv` и `SR.log`. Значение `pareto_csv` в ответе содержит содержимое `SR_curves_pareto.csv`.

## Telegram-бот
Каталог `../PhySO-Telegram-Bot` содержит Telegram бота, который обращается к этому API. Перед запуском убедитесь, что сервис работает и доступен по адресу, указанному в `PHYSO_API_BASE_URL` (по умолчанию `http://localhost:53251/api/v1`).
