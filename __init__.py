# -*- coding: utf-8 -*-
"""
Albert AppImage Launcher

Indexes AppImage files in a few common directories and lets you
launch them directly from Albert.
"""

import os
from pathlib import Path

from albert import *


md_iid = "5.0"
md_version = "1.0"
md_name = "AppImage Launcher"
md_description = "Find and launch AppImages"
md_license = "MIT"
md_authors = ["local"]
md_platforms = ["Linux"]


DEFAULT_DIRS = [
    Path.home() / "Applications",
    Path.home() / "AppImages",
    Path.home() / "Downloads",
    Path.home() / ".local/share/appimages",
]


class Plugin(PluginInstance, IndexQueryHandler):

    def __init__(self):
        PluginInstance.__init__(self)
        IndexQueryHandler.__init__(self)

        raw = self.readConfig("search_dirs", str)
        self._search_dirs = raw if raw else ""

    def defaultTrigger(self):
        return "app "

    @property
    def search_dirs(self):
        return self._search_dirs

    @search_dirs.setter
    def search_dirs(self, value):
        self._search_dirs = value
        self.writeConfig("search_dirs", value)

    def configWidget(self):
        return [
            {
                "type": "label",
                "text": (
                    "Comma-separated directories to scan recursively for "
                    "*.AppImage files. Leave empty for the default directories."
                ),
            },
            {
                "type": "lineedit",
                "label": "Search directories",
                "property": "search_dirs",
            },
        ]

    def _dirs(self):
        if self._search_dirs.strip():
            return [
                Path(p.strip()).expanduser()
                for p in self._search_dirs.split(",")
                if p.strip()
            ]
        return DEFAULT_DIRS

    def updateIndexItems(self):
        index_items = []
        seen = set()

        for directory in self._dirs():
            if not directory.is_dir():
                continue

            try:
                files = directory.rglob("*")
                for path in files:
                    if not path.is_file():
                        continue

                    if path.suffix.lower() != ".appimage":
                        continue

                    path = path.resolve()

                    if path in seen:
                        continue
                    seen.add(path)

                    item = StandardItem(
                        id=str(path),
                        text=path.stem,
                        subtext=str(path),
                        icon_factory=lambda path=path: Icon.fileType(path),
                        actions=[
                            Action(
                                "run",
                                "Run AppImage",
                                lambda path=path: self._run(path),
                            ),
                            Action(
                                "reveal",
                                "Open containing folder",
                                lambda path=path: runDetachedProcess(
                                    ["xdg-open", str(path.parent)]
                                ),
                            ),
                        ],
                    )

                    index_items.append(
                        IndexItem(
                            item=item,
                            string=path.stem,
                        )
                    )

            except Exception as exc:
                warning(
                    f"AppImage Launcher: failed to scan {directory}: {exc}"
                )

        info(
            f"AppImage Launcher: indexed {len(index_items)} AppImage(s)"
        )
        self.setIndexItems(index_items)

    def _run(self, path):
        try:
            # AppImages need their executable bit set before they can be
            # launched directly.
            if not os.access(path, os.X_OK):
                path.chmod(path.stat().st_mode | 0o111)

            pid = runDetachedProcess([str(path)])

            if not pid:
                warning(f"AppImage Launcher: failed to launch {path}")

        except Exception as exc:
            warning(f"AppImage Launcher: failed to launch {path}: {exc}")
