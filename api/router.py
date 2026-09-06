"""Корневой роутер JSON API."""

from fastapi import APIRouter

from api.contacts import router as contacts_router


router = APIRouter(prefix="/api")
router.include_router(contacts_router)
