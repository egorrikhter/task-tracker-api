# Asynchronous Task Tracker API

[![CI](https://github.com/egorrikhter/task-tracker-api/actions/workflows/ci.yml/badge.svg)](https://github.com/egorrikhter/task-tracker-api/actions/workflows/ci.yml)
![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-005571?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)
![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

Полнофункциональный, асинхронный REST API трекера задач с поддержкой проектов, тегов (Many-to-Many), пагинации, фильтрации, фоновыми задачами через очередь Redis и автоматизированным CI/CD пайплайном.

---

## 🛠 Стек технологий

- **Backend:** FastAPI, Pydantic v2, Python 3.14
- **База данных & ORM:** PostgreSQL 16, SQLAlchemy 2.0 (async), asyncpg, Alembic (миграции)
- **Очереди & Фоновые задачи:** Redis 7, Arq (асинхронный воркер)
- **Контейнеризация:** Docker, Docker Compose (многоконтейнерная оркестрация)
- **Тестирование:** Pytest, pytest-asyncio, pytest-cov (покрытие кода 85%+)
- **CI/CD:** GitHub Actions (автоматический запуск тестов в изолированном PostgreSQL сервисе)
- **Безопасность:** JWT-авторизация (Access & Refresh), хеширование паролей через bcrypt, защита от timing attacks

---

## 🏗 Архитектурные особенности

1. **Чистый Async/Await стек:** Полностью асинхронный пайплайн от эндпоинта до драйвера базы данных (`asyncpg`).
2. **Оптимизация производительности:** Реализована offset-пагинация, гибкая фильтрация и составные индексы в базе данных (`ix_task_project_id_status`) для предотвращения full-table scan.
3. **Безопасность данных и целостность:** Перехват сетевых исключений драйвера БД (`IntegrityError`) на уровне базы с возвратом корректного статуса `409 Conflict` при нарушении уникальности.
4. **Разделение ответственности (Background Workers):** Тяжелые операции (например, отправка уведомлений при создании задач) вынесены из HTTP-цикла "запрос-ответ" в асинхронный воркер через брокер сообщений Redis.

---

## 🚀 Быстрый старт (Одна команда)

Самый простой способ запустить проект локально со всеми зависимостями (API, База данных, Redis, Воркер) — использовать Docker Compose.

1. **Клонировать репозиторий:**
   ```bash
   git clone [https://github.com/egorrikhter/task-tracker-api.git](https://github.com/egorrikhter/task-tracker-api.git)
   cd task-tracker-api
