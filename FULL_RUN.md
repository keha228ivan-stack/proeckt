# FULL RUN: локальный запуск **всех клиентов** с единым backend

> Цель: поднять один локальный backend и подключить к нему:
> - `hrrepozik` (web для менеджеров)
> - `hrrepozik-modile-2` (mobile для админов)
> - `repozik-desktop2` (desktop для сотрудников)

---

## 1) Подготовка окружения

```bash
cd /workspace/proeckt
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Проверка, что FastAPI стартует:

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Остановить `Ctrl+C`.

---

## 2) Единый backend (локально)

Запуск backend:

```bash
cd /workspace/proeckt
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URL:
- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

SQLite-файл БД создаётся локально рядом с проектом: `hr_local.db`.

---

## 3) Конфиг для клиентов (единая точка API)

Во **всех трёх клиентах** должен быть один и тот же base URL:

```env
API_BASE_URL=http://127.0.0.1:8000
```

Если клиент запущен в эмуляторе/контейнере, используй:
- Android Emulator: `http://10.0.2.2:8000`
- iOS Simulator: `http://127.0.0.1:8000`
- Docker-контейнер: `http://host.docker.internal:8000`

---

## 4) Запуск web-клиента (`hrrepozik`)

```bash
cd /workspace/proeckt/hrrepozik
# пример для Node-проекта:
# npm install
# echo "API_BASE_URL=http://127.0.0.1:8000" > .env.local
# npm run dev
```

Ожидаемое поведение web (manager):
- логин менеджера;
- назначение курсов сотрудникам (`POST /manager/assign/{user_id}/{course_id}`);
- просмотр количества назначенных курсов по сотруднику (`GET /employee_courses/{user_id}`).

---

## 5) Запуск mobile-клиента (`hrrepozik-modile-2`)

```bash
cd /workspace/proeckt/hrrepozik-modile-2
# пример для React Native / Flutter (подставь свою команду):
# npm install && npm run android
# или flutter pub get && flutter run
```

Ожидаемое поведение mobile (admin):
- доступ только к агрегированной статистике;
- `GET /stats`
- `GET /stats/{department}`
- без детальных персональных карточек сотрудников.

---

## 6) Запуск desktop-клиента (`repozik-desktop2`)

```bash
cd /workspace/proeckt/repozik-desktop2
# пример для Electron/Tauri/PySide (подставь свою команду):
# npm install && npm run dev
# или cargo tauri dev
# или python main.py
```

Ожидаемое поведение desktop (employee):
- регистрация/логин сотрудника;
- раздел «Курсы в процессе» берёт данные из `GET /my_courses`;
- `GET /my_courses/{id}/progress`;
- `GET /my_courses/{id}/test` только после 100% прогресса.

---

## 7) Быстрая smoke-проверка API (curl)

### 7.1 Регистрация пользователей

```bash
curl -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" -d '{"name":"Manager 1","email":"manager@local","department":"HR","role":"manager","password":"pass1234"}'
curl -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" -d '{"name":"Admin 1","email":"admin@local","department":"HQ","role":"admin","password":"pass1234"}'
curl -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" -d '{"name":"Employee 1","email":"employee@local","department":"Sales","role":"employee","password":"pass1234"}'
```

### 7.2 Логин и получение JWT

```bash
curl -X POST http://127.0.0.1:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=manager@local&password=pass1234"
```

Скопируй `access_token` в переменную `TOKEN`.

### 7.3 Проверка role-based endpoint’ов

```bash
# manager
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/employee_courses/3

# admin (после логина админом)
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/stats

# employee (после логина сотрудником)
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/my_courses
```

---

## 8) Важные правила синхронизации

1. Назначение курса менеджером создаёт `CourseAssignment` со статусом `in-progress`.
2. Это назначение должно отображаться в desktop в «Курсах в процессе», а не в библиотеке.
3. `course_library` используется web+desktop как общий каталог.
4. mobile-клиент (admin) использует только статистические endpoint’ы.

---

## 9) Единая команда для параллельного запуска (опционально)

Если установлен `tmux`:

```bash
tmux new-session -d -s hr 'cd /workspace/proeckt && source .venv/bin/activate && uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000'
tmux split-window -t hr 'cd /workspace/proeckt/hrrepozik && echo "run your web command"'
tmux split-window -t hr 'cd /workspace/proeckt/hrrepozik-modile-2 && echo "run your mobile command"'
tmux split-window -t hr 'cd /workspace/proeckt/repozik-desktop2 && echo "run your desktop command"'
tmux attach -t hr
```

