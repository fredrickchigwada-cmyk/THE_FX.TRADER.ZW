import json
import os
import tempfile
from typing import Optional

from core.alert_config import AlertConfig


class AlertPersistence:
    """
    Saves and restores alert configuration locally.

    Signal-only:
    This module stores settings only.
    It cannot place, modify, or close trades.
    """

    DEFAULT_FILENAME = "alert_settings.json"

    def __init__(self, filepath: Optional[str] = None):
        if filepath:
            self.filepath = os.path.abspath(filepath)
        else:
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            self.filepath = os.path.join(
                project_root,
                "config",
                self.DEFAULT_FILENAME,
            )

    def save(self, config: AlertConfig) -> bool:
        os.makedirs(
            os.path.dirname(self.filepath),
            exist_ok=True,
        )

        data = config.to_dict()

        directory = os.path.dirname(self.filepath)

        fd, temp_path = tempfile.mkstemp(
            prefix=".alert_settings_",
            suffix=".tmp",
            dir=directory,
            text=True,
        )

        try:
            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=2,
                    sort_keys=True,
                )
                file.flush()
                os.fsync(file.fileno())

            os.replace(
                temp_path,
                self.filepath,
            )

            return True

        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

            return False

    def load(
        self,
        default: Optional[AlertConfig] = None,
    ) -> AlertConfig:

        if default is None:
            default = AlertConfig()

        if not os.path.exists(self.filepath):
            return default

        try:
            with open(
                self.filepath,
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

            if not isinstance(data, dict):
                return default

            return AlertConfig.from_dict(data)

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ):
            return default

    def exists(self) -> bool:
        return os.path.exists(
            self.filepath
        )

    def delete(self) -> bool:

        try:
            if os.path.exists(
                self.filepath
            ):
                os.remove(
                    self.filepath
                )

            return True

        except OSError:
            return False

    def path(self) -> str:
        return self.filepath


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 10E - Alert Persistence"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
