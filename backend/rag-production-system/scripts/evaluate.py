from __future__ import annotations

import asyncio
import sys

from app.api.dependencies import get_evaluation_runner


async def main() -> None:
    judge = sys.argv[1] if len(sys.argv) > 1 else None
    test_file = sys.argv[2] if len(sys.argv) > 2 else None
    path = await get_evaluation_runner().run("cli", judge, test_file)
    print(path)


if __name__ == "__main__":
    asyncio.run(main())
