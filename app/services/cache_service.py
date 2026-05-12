# app/services/cache_headers.py
from fastapi import Response
from hashlib import md5
from typing import Any


def generate_etag(content: Any) -> str:
    """Генерирует ETag на основе содержимого"""
    content_str = str(content).encode('utf-8')
    return md5(content_str).hexdigest()


def add_cache_headers(response: Response, etag: str, max_age: int = 3600):
    """Добавляет Cache-Control и ETag"""
    response.headers["ETag"] = f'"{etag}"'
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    # Если хочешь агрессивнее кэширование:
    # response.headers["Cache-Control"] = f"public, max-age={max_age}, immutable"