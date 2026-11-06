"""
Authentication API Router for Scrolls of Agora.
Issues signed HMAC session tokens for player accounts.
"""

from fastapi import APIRouter, HTTPException, status
from src.models import AuthLoginRequest
from src.database import get_db_cursor, execute_sql, row_to_dict
from src.auth import create_player_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login")
def api_login(req: AuthLoginRequest):
    with get_db_cursor() as cur:
        if req.player_id:
            execute_sql(cur, "SELECT player_id, username, faction, character_class, level, is_banned FROM players WHERE player_id = ?;", (req.player_id,))
        elif req.username:
            execute_sql(cur, "SELECT player_id, username, faction, character_class, level, is_banned FROM players WHERE username = ?;", (req.username,))
        else:
            # Default to Aurelius Goldhand (1005)
            execute_sql(cur, "SELECT player_id, username, faction, character_class, level, is_banned FROM players WHERE player_id = 1005;")

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found.")

        player = row_to_dict(row)
        if player.get("is_banned"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is banned by the Inquisitor.")

        token = create_player_token(player["player_id"], player["username"])

    return {
        "success": True,
        "token": token,
        "token_type": "Bearer",
        "player": player,
        "message": f"Authenticated as {player['username']} (ID: {player['player_id']}).",
    }
