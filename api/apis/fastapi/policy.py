from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse


class PolicyAPIRouter:
    def __init__(self):

        # Initialize api router
        self.router = APIRouter()

        # Register routes
        self.router.add_api_route(
            "/{policy_id}",
            self.get_policy_raw,
            methods=["GET"],
            include_in_schema=False,
        )

    async def get_policy_raw(self, policy_id: str):
        path = (
            Path(__file__).parent.parent
            / "resources"
            / "policies"
            / f"{policy_id}.yaml"
        )
        if not path.exists():
            raise HTTPException(
                404, detail={"message": f"Policy '{policy_id}' not found"}
            )
        return PlainTextResponse(path.read_text())
