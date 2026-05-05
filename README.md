# Локальная HR-система: веб + мобильный + десктоп

## Что реализовано
- Общий локальный backend на FastAPI (`backend/app/main.py`) и SQLite (`hr_local.db`).
- Единая модель данных для трёх клиентов:
  - `hrrepozik` (web для менеджеров),
  - `hrrepozik-modile-2` (mobile для админов),
  - `repozik-desktop2` (desktop для сотрудников).
- JWT-аутентификация и role-based доступ.

## Анализ соответствия требованиям
1. **Связи данных**: `User` ↔ `CourseAssignment` ↔ `Course`, отдельно `Lesson`, `Progress`, `Test`.
2. **Сотрудник видит только свои курсы**: endpoint `/my_courses` фильтрует по `current.id`.
3. **Тест только после завершения**: `/my_courses/{id}/test` открыт только при `completion_percentage == 100`.
4. **Менеджер назначает курсы, но не видит персональный прогресс**: есть `/manager/assign/...`, нет manager-endpoint на детальный прогресс.
5. **Админ видит только агрегаты**: `/stats` и `/stats/{department}` без персональных деталей.
6. **Назначение попадает в “Курсы в процессе”**: создаётся `CourseAssignment(status="in-progress")`, а не запись в библиотеке.
7. **Библиотека синхронизируется web/desktop, не mobile**:
   - API `/course_library` доступен общим клиентам,
   - mobile-клиенту (админу) для сценария можно не подключать этот endpoint, оставляя только stats API.

## API
### Auth
- `POST /auth/register`
- `POST /auth/login`

### Менеджер
- `POST /manager/assign/{user_id}/{course_id}`
- `GET /employee_courses/{user_id}`

### Сотрудник
- `GET /my_courses`
- `GET /my_courses/{id}/progress`
- `GET /my_courses/{id}/test`

### Админ
- `GET /stats`
- `GET /stats/{department}`

### Общая библиотека (web+desktop)
- `GET /course_library`

## Запуск локально
```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Сервер будет доступен на `http://127.0.0.1:8000`.


Подробный сценарий полного локального запуска всех клиентов: `FULL_RUN.md`.
