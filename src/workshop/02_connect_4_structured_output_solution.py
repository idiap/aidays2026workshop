"""Connect Four game with NiceGUI – Player 2 is an LLM agent using structured output."""

import argparse

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv
from nicegui import ui

from workshop.common import (
    pydantic_ai_build_model,
    pydantic_ai_build_high_reasoning_settings,
)

load_dotenv()

ROWS = 6
COLS = 7
EMPTY = "."
PLAYER_SYMBOLS = {1: "X", 2: "O"}
PLAYER_COLORS = {1: "#ef4444", 2: "#facc15"}  # red, yellow
BG_COLOR = "#1e3a5f"


# ── Structured output for the agent ────────────────────────
class ConnectFourMove(BaseModel):
    column: int = Field(
        ge=0, le=COLS - 1, description="Column index (0-6) to drop the piece"
    )


def build_agent(high_reasoning: bool = False) -> Agent[None, ConnectFourMove]:
    model = pydantic_ai_build_model()
    settings = pydantic_ai_build_high_reasoning_settings() if high_reasoning else None
    agent = Agent(
        model,
        output_type=ConnectFourMove,
        model_settings=settings,
        system_prompt=(
            "You are playing Connect Four as player O. "
            "The board is shown with '.' for empty, 'X' for player 1, 'O' for you. "
            "Column indices 0-6 are at the bottom. "
            "Pick the best column to play. Only choose a column that is not full (top row is '.')."
        ),
    )
    return agent


parser = argparse.ArgumentParser(description="Connect Four with LLM agent")
parser.add_argument(
    "--high-reasoning",
    action="store_true",
    help="Enable high reasoning effort for the LLM",
)
args, _ = parser.parse_known_args()

agent = build_agent(high_reasoning=args.high_reasoning)


# ── Pure game logic ─────────────────────────────────────────
def new_board() -> list[list[str]]:
    """Return an empty board (list of rows, top row first)."""
    return [[EMPTY] * COLS for _ in range(ROWS)]


def board_to_string(board: list[list[str]]) -> str:
    """Compact text representation suitable for an LLM prompt.

    Example output:
        . . . . . . .
        . . . . . . .
        . . . . . . .
        . . . . . . .
        . . . X . . .
        . . O X O . .
        0 1 2 3 4 5 6
    """
    lines = [" ".join(row) for row in board]
    lines.append(" ".join(str(c) for c in range(COLS)))
    return "\n".join(lines)


def drop_piece(board: list[list[str]], col: int, player: int) -> int | None:
    """Drop a piece in *col* for *player*. Return the row it landed on, or None if full."""
    symbol = PLAYER_SYMBOLS[player]
    for row in range(ROWS - 1, -1, -1):
        if board[row][col] == EMPTY:
            board[row][col] = symbol
            return row
    return None


def check_winner(board: list[list[str]], row: int, col: int) -> bool:
    """Check if the last move at (row, col) created four in a row."""
    symbol = board[row][col]
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        for sign in (1, -1):
            r, c = row + dr * sign, col + dc * sign
            while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == symbol:
                count += 1
                r += dr * sign
                c += dc * sign
        if count >= 4:
            return True
    return False


def is_draw(board: list[list[str]]) -> bool:
    return all(board[0][c] != EMPTY for c in range(COLS))


# ── Game state ──────────────────────────────────────────────
board = new_board()
current_player = 1
game_over = False
status_text = f"Player 1 ({PLAYER_SYMBOLS[1]})'s turn"


def _cell_color(row: int, col: int) -> str:
    sym = board[row][col]
    if sym == PLAYER_SYMBOLS[1]:
        return PLAYER_COLORS[1]
    if sym == PLAYER_SYMBOLS[2]:
        return PLAYER_COLORS[2]
    return BG_COLOR


# ── Refreshable board UI ───────────────────────────────────
@ui.refreshable
def board_ui() -> None:
    with ui.column().classes("gap-1 p-2 rounded-lg").style("background-color: #1a3a6a"):
        for r in range(ROWS):
            with ui.row().classes("gap-1"):
                for c in range(COLS):
                    ui.element("div").classes("rounded-full").style(
                        f"width: 60px; height: 60px; background-color: {_cell_color(r, c)};"
                    )


async def play_column(col: int) -> None:
    global current_player, game_over, status_text
    if game_over or current_player != 1:
        return

    row = drop_piece(board, col, current_player)
    if row is None:
        ui.notify("Column is full!", type="warning")
        return

    if check_winner(board, row, col):
        game_over = True
        status_text = f"Player 1 ({PLAYER_SYMBOLS[1]}) wins!"
    elif is_draw(board):
        game_over = True
        status_text = "It's a draw!"
    else:
        current_player = 2
        status_text = f"Player 2 ({PLAYER_SYMBOLS[2]}) is thinking…"

    status_label.text = status_text
    board_ui.refresh()
    print(board_to_string(board))

    # If it's now the agent's turn, let it play (async)
    if current_player == 2 and not game_over:
        await agent_turn()


async def agent_turn() -> None:
    """Ask the LLM agent to pick a column and play it."""
    global current_player, game_over, status_text

    board_str = board_to_string(board)
    result = await agent.run(f"Current board:\n{board_str}")
    col = result.output.column

    row = drop_piece(board, col, 2)
    if row is None:
        # Agent picked a full column – pick first available as fallback
        for fallback in range(COLS):
            row = drop_piece(board, fallback, 2)
            if row is not None:
                col = fallback
                break

    if row is None:
        return  # board is full

    if check_winner(board, row, col):
        game_over = True
        status_text = f"Player 2 ({PLAYER_SYMBOLS[2]}) wins!"
    elif is_draw(board):
        game_over = True
        status_text = "It's a draw!"
    else:
        current_player = 1
        status_text = f"Player 1 ({PLAYER_SYMBOLS[1]})'s turn"

    status_label.text = status_text
    board_ui.refresh()
    print(board_to_string(board))


def reset_game() -> None:
    global board, current_player, game_over, status_text
    board = new_board()
    current_player = 1
    game_over = False
    status_text = f"Player 1 ({PLAYER_SYMBOLS[1]})'s turn"
    status_label.text = status_text
    board_ui.refresh()


# ── UI ──────────────────────────────────────────────────────
with ui.column().classes("items-center w-full mt-8"):
    ui.label("Connect Four").classes("text-3xl font-bold mb-4")
    status_label = ui.label(status_text).classes("text-xl mb-2")

    # Column buttons
    with ui.row().classes("gap-0"):
        for c in range(COLS):
            ui.button(f"{c}", on_click=lambda _, col=c: play_column(col)).props(
                "flat dense"
            ).classes("w-16")

    # Board grid (refreshable)
    board_ui()

    ui.button("New Game", on_click=reset_game).classes("mt-4")

ui.run(title="Connect Four", port=1234)
