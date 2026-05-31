from fastapi import APIRouter, Request

router = APIRouter()


@router.get(
    "/ping",
    tags=["Health Check"],
    description="서비스 상태를 확인합니다.",
    response_description="pong",
)
def ping(request: Request) -> str:
    return "pong"
