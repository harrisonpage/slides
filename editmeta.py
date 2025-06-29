#!/usr/bin/env python3

import sys
import json
import subprocess

from textual.app import App, ComposeResult
from textual.widgets import Input, TextArea, Button, Static
from textual.containers import Vertical

class MetadataEditor(App):
    CSS = "#main { background: navy; }\n"

    def __init__(self, json_path: str, **kwargs):
        super().__init__(**kwargs)
        self.json_path = json_path
        self.metadata = {}

    def on_mount(self):
        try:
            with open(self.json_path, "r") as f:
                self.metadata = json.load(f)
        except Exception as e:
            self.exit(message=f"Failed to load JSON: {e}")

        # Populate fields
        self.query_one("#title", Input).value = self.metadata.get("title", "")
        self.query_one("#description", TextArea).text = self.metadata.get("description", "")
        self.query_one("#tags", Input).value = ", ".join(self.metadata.get("tags", []))
        self.query_one("#date", Input).value = self.metadata.get("date", "")
        self.query_one("#color", Input).value = self.metadata.get("color", "")

    def compose(self) -> ComposeResult:
        yield Vertical(
            Button("View Images", id="view-images"),
            Static("Edit Title"),
            Input(id="title"),
            Static("Edit Tags (comma-separated)"),
            Input(id="tags"),
            Static("Edit Date"),
            Input(id="date"),
            Static("Edit Color"),
            Input(id="color"),
            Static("Edit Description"),
            TextArea(id="description"),
            Button("Save", id="save"),
            id="main",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            title_input = self.query_one("#title", Input)
            desc_area = self.query_one("#description", TextArea)
            tags_input = self.query_one("#tags", Input)
            date_input = self.query_one("#date", Input)
            color_input = self.query_one("#color", Input)

            self.metadata["title"] = title_input.value
            self.metadata["description"] = desc_area.text
            self.metadata["tags"] = [t.strip() for t in tags_input.value.split(",") if t.strip()]
            self.metadata["date"] = date_input.value
            self.metadata["color"] = color_input.value

            with open(self.json_path, "w") as f:
                json.dump(self.metadata, f)
            self.exit(message="✅ Metadata updated")

        elif event.button.id == "view-images":
            images = self.metadata.get("images", [])
            for path in images:
                try:
                    subprocess.run(["open", path], check=True)
                except Exception as e:
                    self.exit(message=f"Failed to open image: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python metadata_editor.py <metadata.json>")
        sys.exit(1)

    json_path = sys.argv[1]
    app = MetadataEditor(json_path=json_path)
    app.run()
