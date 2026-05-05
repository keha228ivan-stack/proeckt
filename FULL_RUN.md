# FULL RUN (PowerShell): единый локальный backend + 3 клиента

> Актуально на **2026-05-05**. В репозитории директории клиентов (`hrrepozik`, `hrrepozik-modile-2`, `repozik-desktop2`) пока без исходников, поэтому ниже — полностью рабочий PowerShell runbook + чек-лист корректной клиентской логики и команды проверки API.

---

## 0) Что уже проверено

- Backend запускается локально на `http://127.0.0.1:8000`.
- Модель доступа по ролям реализована на API.
- Для проверки клиентов добавлен контракт, какие endpoint’ы и как вызывать.

---

## 1) Подготовка окружения (PowerShell)

```powershell
Set-Location C:\workspace\proeckt
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Проверка синтаксиса backend:

```powershell
python -m compileall backend\app
```

---

## 2) Запуск backend (PowerShell)

```powershell
Set-Location C:\workspace\proeckt
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Локальные адреса:
- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

Локальная БД: `hr_local.db`.

---

## 3) Единая настройка API для клиентов

Во всех клиентах должен быть **один base URL**:

```env
API_BASE_URL=http://127.0.0.1:8000
```

Если клиент запускается не напрямую на хосте Windows:
- Android Emulator: `http://10.0.2.2:8000`
- iOS Simulator: `http://127.0.0.1:8000`
- Docker Desktop: `http://host.docker.internal:8000`

---

## 4) Правильная логика загрузки данных по ролям (исправлять клиентов по этому контракту)

### 4.1 Web (менеджер, `hrrepozik`)
Использует:
- `POST /manager/assign/{user_id}/{course_id}`
- `GET /employee_courses/{user_id}`
- (опционально каталог) `GET /course_library`

Не должен использовать:
- `GET /stats*` как основной UI (это мобильный админ сценарий).
- `GET /my_courses*` (это employee-десктоп сценарий).

### 4.2 Mobile (админ, `hrrepozik-modile-2`)
Использует только агрегаты:
- `GET /stats`
- `GET /stats/{department}`

Не должен использовать:
- `GET /my_courses*`
- `POST /manager/assign/*`
- персональные employee-детали.

### 4.3 Desktop (сотрудник, `repozik-desktop2`)
Использует:
- `GET /my_courses`
- `GET /my_courses/{id}/progress`
- `GET /my_courses/{id}/test` (только после 100% прогресса)
- (опционально каталог) `GET /course_library`

Ключевая бизнес-логика:
- Назначенный менеджером курс должен показываться в «Курсах в процессе», т.к. создаётся `CourseAssignment(status="in-progress")`.
- Назначения не должны отображаться как «просто библиотека» без статуса.

---

## 5) PowerShell smoke tests (проверка backend + сценариев клиентов)

> Открой второй PowerShell, backend должен уже работать.

### 5.1 Регистрация тестовых пользователей

```powershell
$base = "http://127.0.0.1:8000"
$headers = @{ "Content-Type" = "application/json" }

Invoke-RestMethod -Method Post -Uri "$base/auth/register" -Headers $headers -Body (@{name="Manager 1"; email="manager@local.dev"; department="HR"; role="manager"; password="pass1234"} | ConvertTo-Json)
Invoke-RestMethod -Method Post -Uri "$base/auth/register" -Headers $headers -Body (@{name="Admin 1"; email="admin@local.dev"; department="HQ"; role="admin"; password="pass1234"} | ConvertTo-Json)
Invoke-RestMethod -Method Post -Uri "$base/auth/register" -Headers $headers -Body (@{name="Employee 1"; email="employee@local.dev"; department="Sales"; role="employee"; password="pass1234"} | ConvertTo-Json)
```

### 5.2 Получение JWT токенов

```powershell
function Get-Token($email, $password) {
  $resp = Invoke-RestMethod -Method Post -Uri "$base/auth/login" -ContentType "application/x-www-form-urlencoded" -Body "username=$email&password=$password"
  return $resp.access_token
}

$managerToken = Get-Token "manager@local.dev" "pass1234"
$adminToken   = Get-Token "admin@local.dev" "pass1234"
$employeeToken= Get-Token "employee@local.dev" "pass1234"
```

### 5.3 Проверка manager API

```powershell
$authManager = @{ Authorization = "Bearer $managerToken" }
Invoke-RestMethod -Method Get -Uri "$base/employee_courses/3" -Headers $authManager
```

### 5.4 Проверка admin API

```powershell
$authAdmin = @{ Authorization = "Bearer $adminToken" }
Invoke-RestMethod -Method Get -Uri "$base/stats" -Headers $authAdmin
Invoke-RestMethod -Method Get -Uri "$base/stats/Sales" -Headers $authAdmin
```

### 5.5 Проверка employee API

```powershell
$authEmployee = @{ Authorization = "Bearer $employeeToken" }
Invoke-RestMethod -Method Get -Uri "$base/my_courses" -Headers $authEmployee
```

---

## 6) Запуск клиентов в отдельных PowerShell окнах

Так как в текущем репозитории нет клиентского кода, команды запуска ниже — шаблон:

### Web
```powershell
Set-Location C:\workspace\proeckt\hrrepozik
# npm install
# $env:API_BASE_URL="http://127.0.0.1:8000"
# npm run dev
```

### Mobile
```powershell
Set-Location C:\workspace\proeckt\hrrepozik-modile-2
# npm install
# $env:API_BASE_URL="http://10.0.2.2:8000"   # если Android Emulator
# npm run android
# или flutter run
```

### Desktop
```powershell
Set-Location C:\workspace\proeckt\repozik-desktop2
# npm install
# $env:API_BASE_URL="http://127.0.0.1:8000"
# npm run dev
# или cargo tauri dev
```

---

## 7) Частые ошибки интеграции (и как исправить в клиентах)

1. **Используется `localhost` внутри Android Emulator** → заменить на `10.0.2.2`.
2. **Mobile запрашивает employee endpoint’ы** → оставить только `/stats*`.
3. **Desktop показывает библиотеку вместо назначений** → источник блока «В процессе» только `/my_courses`.
4. **Нет JWT в заголовке** → всегда `Authorization: Bearer <token>`.
5. **Тест открывается до 100%** → UI должен учитывать `403` и блокировать кнопку до завершения.

