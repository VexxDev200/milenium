Каталог данных milenium (pip install milenium).

Путь задаётся так:
  • по умолчанию: ~/.milenium/data
  • или переменная MILENIUM_DATA_DIR
  • если в текущей папке есть ./data/tg_accounts.json — используется ./data (режим разработки)

Файлы:
  tg_accounts.json   — несколько TG-аккаунтов для grab/scan
  tg_dumps/            — временные выкачки
  tg_folder_scan.json  — отчёт tg_scan_folder
  tg_search_results.json

Один аккаунт без файла: ключи TG_API_ID / TG_API_HASH из ~/.milenium/config.json (LOCKED в сборке).

Команды:
  milenium --help
  milenium library paths
  milenium config_cmd
