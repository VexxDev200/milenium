# milenium

Установка — одна команда, работает из **любой** папки:

```bash
pip install milenium
# или из исходников:
pip install .
```

После установки:

```bash
milenium --help
milenium library paths
milenium user some_nick
milenium library sync --folder "бд"
milenium library grab-best --min-size-mb 50 --max-files 200
milenium library build --min-size-mb 50 --max-files 200
milenium library build-full --min-size-mb 50 --max-files 500
```

Данные и сессии **не** лежат в репозитории — создаются автоматически:

| Путь | Назначение |
|------|------------|
| `~/.milenium/data/` | аккаунты TG, дампы, отчёты |
| `~/.milenium/config.json` | пользовательские настройки |
| `~/.milenium/*.session` | Telethon-сессии |
| `~/.milenium/milenium.log` | лог CLI |

Переопределить каталог данных: `MILENIUM_DATA_DIR=/path/to/data`

Если запускаешь из клона с `./data/tg_accounts.json` — используется `./data` (dev).

## Python

```python
import milenium

milenium.paths()
milenium.tools()
milenium.modules(flat=True)
milenium.databases()

milenium.run_osint(username="nick")
milenium.sync_library(folder="бд")
milenium.csv_search("/path/to/file.csv", "query")
```

## Команды

- **OSINT:** `user`, `email_cmd`, `ip_cmd`, `url_cmd`, `leak`, `company`, `phone_info`, `fssp`, `tg`, `img`
- **БД:** `db_neon`, `csv import|search|exact|stats`
- **TG:** `tg_grab`, `tg_scan_folder`, `tg_search`, `tg_reupload`, `library sync`, `library grab-best`, `library build`, `library build-full`
- **Система:** `config_cmd`, `tui`, `bot`, `library tools|modules|databases|paths`

TG multi-account: отредактируй `~/.milenium/data/tg_accounts.json` (шаблон создаётся при первом запуске).

Архив библиотеки: `milenium.TG_LIBRARY_TARGET`.
