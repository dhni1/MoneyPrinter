from fastapi import APIRouter


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = ["V1"]
    router.prefix = "/api/v1"
    # 한국어로 번역된 설명입니다.
    if dependencies:
        router.dependencies = dependencies
    return router
