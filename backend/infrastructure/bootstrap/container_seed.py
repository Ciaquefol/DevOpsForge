"""Заполнение рабочих каталогов и шаблонов при старте приложения/контейнера."""

from pathlib import Path

from config import settings


def seed_container_workspace() -> dict[str, str]:
    """
    Создаёт структуру deploy_workspace при запуске (в т.ч. в Docker).
    Возвращает краткий отчёт о созданных путях.
    """
    root = Path(settings.deploy_workspace)
    created: list[str] = []

    dirs = [
        root,
        root / "git-cache",
        root / "container-init",
        root / "container-init" / "volumes",
        root / "seeds",
        root / "runtime",
    ]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))

    marker = root / "container-init" / ".initialized"
    if not marker.exists():
        (root / "container-init" / "default.env").write_text(
            "APP_ENV=development\nAPP_SEED=1\nLOG_LEVEL=info\n",
            encoding="utf-8",
        )
        (root / "container-init" / "volumes" / "README.txt").write_text(
            "Mount point templates for deployed containers.\n",
            encoding="utf-8",
        )
        (root / "seeds" / "welcome.json").write_text(
            '{"message": "DevOpsForge container workspace ready", "version": "1.0"}',
            encoding="utf-8",
        )
        (root / "runtime" / "bootstrap.sh").write_text(
            "#!/bin/sh\n"
            'echo "Container initialized by DevOpsForge"\n'
            'test -f /app/data/.env && export $(cat /app/data/.env | xargs)\n'
            "exec \"$@\"\n",
            encoding="utf-8",
        )
        marker.write_text("ok", encoding="utf-8")
        created.append("init-files")

    return {"workspace": str(root), "created": created}
