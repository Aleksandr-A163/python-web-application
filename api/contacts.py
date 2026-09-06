"""API-роутер контактов."""

from fastapi import APIRouter


router = APIRouter(prefix="/contacts", tags=["contacts"])
