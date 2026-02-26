import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QComboBox, QLineEdit, QMessageBox, QFileDialog, QInputDialog, QLabel, QSpacerItem, QSizePolicy
)

from PySide6.QtCore import Qt


# This class is used to save the config.json in a compact way. Has to be defined before anything else.
class CompactJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs['indent'] = 4
        kwargs['ensure_ascii'] = False
        super().__init__(*args, **kwargs)

    def iterencode(self, o, _one_shot=False):
        yield self.encode(o)

    def encode(self, o):
        # Serializaction
        if isinstance(o, list):
            # Other lists, indented
            return "[\n" + ",\n".join("        " + self.encode(el) for el in o) + "\n]"
        elif isinstance(o, dict):
            # For dicts, respect indent.
            items = []
            for k, v in o.items():
                if k == "fields"  and isinstance(v, list) and v and isinstance(v[0], list):
                    # I want to see one field per line.
                    compact_list = lambda lst: "[" + ",".join(json.dumps(x, ensure_ascii=False) for x in lst) + "]"
                    field_str = "[\n" + ",\n".join("        " + compact_list(el) for el in v) + "\n    ]"
                    items.append(f"{json.dumps(k)}: {field_str}")
                else:
                    items.append(f"{json.dumps(k)}: {self.encode(v)}")
            result= "{\n" + ",\n".join("    " + i for i in items) + "\n    }"
        else:
            result= json.dumps(o, ensure_ascii=False)

        # Prettify 
        return result.replace("    },\n    \"SL","},\n\n\"SL").replace("\"\n],","\"\n    ],").replace("    }\n    }","}\n\n}")

# We define the fields we need so we don't have to type them multiple times.    
FIELDS_DEF=[
            ("music_id",5,"string"),
            ("bpm1",2,"u16_le"),
            ("bpm2",2,"u16_le"),
            ("memcard_link_id",2,"u16_le"),

            # These are used with the old difficulty scale (1-10)
            ("single_difficulties",4,"bytes"),
            ("double_difficulties",4,"bytes"),

            # These are used with the new difficulty scale from DDR X onwards (1-20)
            ("single_beginner",1,"u8"),
            ("single_light",1,"u8"),
            ("single_standard",1,"u8"),
            ("single_heavy",1,"u8"),
            ("single_challenge",1,"u8"),
            ("double_beginner",1,"u8"),
            ("double_light",1,"u8"),
            ("double_standard",1,"u8"),
            ("double_heavy",1,"u8"),
            ("double_challenge",1,"u8"),

            ("voltage_single_light",2,"u16_le"),
            ("voltage_single_standard",2,"u16_le"),
            ("voltage_single_heavy",2,"u16_le"),
            ("voltage_single_challenge",2,"u16_le"),
            ("voltage_double_light",2,"u16_le"),
            ("voltage_double_standard",2,"u16_le"),
            ("voltage_double_heavy",2,"u16_le"),
            ("voltage_double_challenge",2,"u16_le"),
            ("voltage_single_beginner",2,"u16_le"),

            ("stream_single_light",2,"u16_le"),
            ("stream_single_standard",2,"u16_le"),
            ("stream_single_heavy",2,"u16_le"),
            ("stream_single_challenge",2,"u16_le"),
            ("stream_double_light",2,"u16_le"),
            ("stream_double_standard",2,"u16_le"),
            ("stream_double_heavy",2,"u16_le"),
            ("stream_double_challenge",2,"u16_le"),
            ("stream_single_beginner",2,"u16_le"),

            ("air_single_light",2,"u16_le"),
            ("air_single_standard",2,"u16_le"),
            ("air_single_heavy",2,"u16_le"),
            ("air_single_challenge",2,"u16_le"),
            ("air_double_light",2,"u16_le"),
            ("air_double_standard",2,"u16_le"),
            ("air_double_heavy",2,"u16_le"),
            ("air_double_challenge",2,"u16_le"),
            ("air_single_beginner",2,"u16_le"),

            ("chaos_single_light",2,"u16_le"),
            ("chaos_single_standard",2,"u16_le"),
            ("chaos_single_heavy",2,"u16_le"),
            ("chaos_single_challenge",2,"u16_le"),
            ("chaos_double_light",2,"u16_le"),
            ("chaos_double_standard",2,"u16_le"),
            ("chaos_double_heavy",2,"u16_le"),
            ("chaos_double_challenge",2,"u16_le"),
            ("chaos_single_beginner",2,"u16_le"),

            ("freeze_single_light",2,"u16_le"),
            ("freeze_single_standard",2,"u16_le"),
            ("freeze_single_heavy",2,"u16_le"),
            ("freeze_single_challenge",2,"u16_le"),
            ("freeze_double_light",2,"u16_le"),
            ("freeze_double_standard",2,"u16_le"),
            ("freeze_double_heavy",2,"u16_le"),
            ("freeze_double_challenge",2,"u16_le"),
            ("freeze_single_beginner",2,"u16_le")
        ]

class ConfigEditorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()        
            
        # Button to load config.json
        self.btn_load_cfg = QPushButton("Load config.json")
        self.btn_load_cfg.setObjectName("load_cfg")
        layout.addWidget(self.btn_load_cfg)

        # Config selection, and buttons for new/copy/delete
        top_layout = QHBoxLayout()
        self.cmb_configs = QComboBox()
        self.btn_new = QPushButton("New")
        self.btn_copy = QPushButton("Copy")
        self.btn_delete = QPushButton("Delete")
        top_layout.addWidget(QLabel("Config for:   "))
        top_layout.addWidget(self.cmb_configs)
        self.cmb_configs.setFixedWidth(150)
        top_layout.addWidget(self.btn_new)
        self.btn_new.setObjectName("new_cfg")
        top_layout.addWidget(self.btn_copy)
        self.btn_copy.setObjectName("copy_cfg")
        top_layout.addWidget(self.btn_delete)
        self.btn_delete.setObjectName("del_cfg")
        top_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.addLayout(top_layout)

        # Main ("header") fields
        grid_layout = QGridLayout()
        self.txt_game = QLineEdit()
        self.txt_offset = QLineEdit()
        self.txt_end_offset = QLineEdit()
        self.txt_block_size = QLineEdit()
        self.txt_titles_start = QLineEdit()
        self.txt_titles_end = QLineEdit()

        # First row
        grid_layout.addWidget(QLabel("Game:"), 0, 0)
        grid_layout.addWidget(self.txt_game, 0, 1)

        grid_layout.addWidget(QLabel("Start Offset:"), 0, 2)
        grid_layout.addWidget(self.txt_offset, 0, 3)

        grid_layout.addWidget(QLabel("End Offset:"), 0, 4)
        grid_layout.addWidget(self.txt_end_offset, 0, 5)

        # Second row
        grid_layout.addWidget(QLabel("Block Size:"), 1, 0)
        grid_layout.addWidget(self.txt_block_size, 1, 1)

        grid_layout.addWidget(QLabel("Titles Start:"), 1, 2)
        grid_layout.addWidget(self.txt_titles_start, 1, 3)

        grid_layout.addWidget(QLabel("Titles End:"), 1, 4)
        grid_layout.addWidget(self.txt_titles_end, 1, 5)

        # Definitios for comboboxes
        self.cmb_difficulty = QComboBox()
        self.cmb_difficulty.addItems(["1_10", "1_20"])
        self.cmb_titles_parser = QComboBox()
        self.cmb_titles_parser.addItems([
            "parse_titles", "parse_titles_reverse",
            "parse_titles_supernova", "parse_titles_sequential"
        ])

        # Third  row
        grid_layout.addWidget(QLabel("Titles Parser:"), 2, 0)
        grid_layout.addWidget(self.cmb_titles_parser, 2, 1)

        grid_layout.addWidget(QLabel("Difficulty Scale:"), 2, 2)
        grid_layout.addWidget(self.cmb_difficulty, 2, 3)

        layout.addLayout(grid_layout)

        # Table with fields
        self.fields_table = QTableWidget()
        self.fields_table.setColumnCount(4)
        self.fields_table.setHorizontalHeaderLabels(["Field name", "Offset (hex)", "Byte size", "Type"])
        self.fields_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("Fields"))
        layout.addWidget(self.fields_table)

        self.fields_table.setRowCount(len(FIELDS_DEF))
        for r, (name, length, dtype) in enumerate(FIELDS_DEF):
            self.fields_table.setItem(r, 0, QTableWidgetItem(name))         # Name (non editable)
            self.fields_table.item(r, 0).setFlags(Qt.ItemIsEnabled)         # Block editiong
            self.fields_table.setItem(r, 1, QTableWidgetItem(""))           # Offset (editable)
            self.fields_table.setItem(r, 2, QTableWidgetItem(str(length)))  # Size in bytes (auto)
            self.fields_table.item(r, 2).setFlags(Qt.ItemIsEnabled)         # Block editiong
            self.fields_table.setItem(r, 3, QTableWidgetItem(dtype))        # Type (auto)
            self.fields_table.item(r, 3).setFlags(Qt.ItemIsEnabled)         # Block editiong

        # Update visibility of fields based on difficulty scale
        self.cmb_difficulty.currentTextChanged.connect(self.update_fields_visibility)

        # Save button
        self.btn_save = QPushButton("Save changes")
        self.btn_save.setObjectName("save_cfg")
        layout.addWidget(self.btn_save)

        self.setLayout(layout)

        # Disable te buttons until a config is loaded
        self.btn_new.setEnabled(False)
        self.btn_copy.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.btn_save.setEnabled(False)        

        # Internal state
        self.cfg_data = {}
        self.current_key = None

        # Connections
        self.btn_load_cfg.clicked.connect(self.load_config_file)
        self.btn_new.clicked.connect(self.new_config)
        self.btn_copy.clicked.connect(self.copy_config)
        self.btn_delete.clicked.connect(self.delete_config)
        self.cmb_configs.currentIndexChanged.connect(self.load_selected_config)
        self.btn_save.clicked.connect(self.save_changes)

    def load_config_file(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self, "Choose config.json", "config.json", filter="JSON files (*.json)"
            )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.cfg_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"I couldn't read config.json:\n{e}")
            return

        self.cmb_configs.clear()
        self.cmb_configs.addItems(self.cfg_data.keys())
        QMessageBox.information(self, "Success!", f"{len(self.cfg_data)} configurations found.")

        # Now we're sure that the config is loaded, enable the buttons
        self.btn_new.setEnabled(True)
        self.btn_copy.setEnabled(True)
        self.btn_delete.setEnabled(True)
        self.btn_save.setEnabled(True)        

    def update_fields_visibility(self, scale):
        for r in range(self.fields_table.rowCount()):
            name = self.fields_table.item(r, 0).text()
            if scale == "1_10":
                if name in ["single_difficulties", "double_difficulties"]:
                    self.fields_table.setRowHidden(r, False)
                elif name.startswith("single_") or name.startswith("double_"):
                    self.fields_table.setRowHidden(r, True)
                else:
                    self.fields_table.setRowHidden(r, False)
            elif scale == "1_20":
                if name in ["single_difficulties", "double_difficulties"]:
                    self.fields_table.setRowHidden(r, True)
                elif name.startswith("single_") or name.startswith("double_"):
                    self.fields_table.setRowHidden(r, False)
                else:
                    self.fields_table.setRowHidden(r, False)


    def load_selected_config(self):
        key = self.cmb_configs.currentText()
        if not key:
            return
        self.current_key = key
        cfg = self.cfg_data.get(key, {})

        # Force default values if missing
        cfg.setdefault("titles_offset_start", 0)
        cfg.setdefault("titles_offset_end", 0)
        cfg.setdefault("difficulty_scale", "1_10")
        cfg.setdefault("titles_parser", "parse_titles")

        # Update widgets for "header" fields
        self.txt_game.setText(cfg.get("game", ""))
        self.txt_offset.setText(str(cfg.get("offset", "")))
        self.txt_end_offset.setText(str(cfg.get("end_offset", "")))
        self.txt_block_size.setText(str(cfg.get("block_size", "")))
        self.txt_titles_start.setText(str(cfg.get("titles_offset_start", "")))
        self.txt_titles_end.setText(str(cfg.get("titles_offset_end", "")))

        self.cmb_difficulty.setCurrentText(cfg.get("difficulty_scale", "1_10"))
        self.cmb_titles_parser.setCurrentText(cfg.get("titles_parser", "parse_titles"))

        # Load fields
        self.fields_table.setRowCount(len(FIELDS_DEF))
        for r, (fname, length, dtype) in enumerate(FIELDS_DEF):
            self.fields_table.setItem(r, 0, QTableWidgetItem(fname))
            self.fields_table.item(r, 0).setFlags(Qt.ItemIsEnabled)
            self.fields_table.setItem(r, 2, QTableWidgetItem(str(length)))
            self.fields_table.item(r, 2).setFlags(Qt.ItemIsEnabled)
            self.fields_table.setItem(r, 3, QTableWidgetItem(dtype))
            self.fields_table.item(r, 3).setFlags(Qt.ItemIsEnabled)

            # Buscar si este campo existe en el JSON
            offset = ""
            for f in cfg.get("fields", []):
                if f[0] == fname:
                    offset = f[1]  # usar el offset del JSON
                    break
            self.fields_table.setItem(r, 1, QTableWidgetItem(offset))

        self.update_fields_visibility(self.cmb_difficulty.currentText())



    def save_changes(self):
        if not self.current_key:
            return

        cfg = self.cfg_data.get(self.current_key, {})

        # Update values
        cfg["game"] = self.txt_game.text()
        cfg["offset"] = int(self.txt_offset.text()) if self.txt_offset.text() else 0
        cfg["end_offset"] = int(self.txt_end_offset.text()) if self.txt_end_offset.text() else 0
        cfg["block_size"] = int(self.txt_block_size.text()) if self.txt_block_size.text() else 0
        cfg["titles_offset_start"] = int(self.txt_titles_start.text()) if self.txt_titles_start.text() else 0
        cfg["titles_offset_end"] = int(self.txt_titles_end.text()) if self.txt_titles_end.text() else 0
        cfg["titles_parser"] = self.cmb_titles_parser.currentText()
        cfg["difficulty_scale"] = self.cmb_difficulty.currentText()

        # Reconstruct fields
        new_fields = []
        for r in range(self.fields_table.rowCount()):
            if self.fields_table.isRowHidden(r):
                continue
            name = self.fields_table.item(r, 0).text()
            offset = self.fields_table.item(r, 1).text().strip()
            length = int(self.fields_table.item(r, 2).text())
            dtype = self.fields_table.item(r, 3).text()
            new_fields.append([name, offset, length, dtype])
        cfg["fields"] = new_fields

        # OCD moment: Reorder "header" fields. We want them at the top.
        ordered_cfg = {
            "game": cfg.get("game"),
            "offset": cfg.get("offset"),
            "end_offset": cfg.get("end_offset"),
            "block_size": cfg.get("block_size"),
            "titles_offset_start": cfg.get("titles_offset_start"),
            "titles_offset_end": cfg.get("titles_offset_end"),
            "titles_parser": cfg.get("titles_parser"),
            "difficulty_scale": cfg.get("difficulty_scale"),
        }

        # Add the rest of the important data (manual_titles, why_is_this, fields, etc.)
        for k, v in cfg.items():
            if k not in ordered_cfg:
                ordered_cfg[k] = v

        # Save the informacion in unr order.
        self.cfg_data[self.current_key] = ordered_cfg

        # Write file
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.cfg_data, f, cls=CompactJSONEncoder)

        QMessageBox.information(self, "Done!", f"Config '{self.current_key}' updated.")

    def new_config(self):
        name, ok = QInputDialog.getText(self, "New config", "Input the file name (ej. SLPM_624.27):")
        if not ok or not name:
            return
        game, ok = QInputDialog.getText(self, "New config", "Input the name of the game:")
        if not ok:
            return

        new_fields = [[fname, "", length, dtype] for fname, length, dtype in FIELDS_DEF]

        self.cfg_data[name] = {
            "game": game,
            "offset": 0,
            "end_offset": 0,
            "block_size": 0,
            "titles_offset_start": 0,
            "titles_offset_end": 0,
            "difficulty_scale": "1_10",
            "titles_parser": "parse_titles",
            "fields": new_fields
        }        

        self.cmb_configs.addItem(name)
        self.cmb_configs.setCurrentText(name)
        self.load_selected_config()

    def copy_config(self):
        if not self.current_key:
            return
        name, ok = QInputDialog.getText(self, "Copy config", "New file name:")
        if not ok or not name:
            return
        game, ok = QInputDialog.getText(self, "Copy config", "Input the name of the game:")
        if not ok:
            return

        import copy
        new_cfg = copy.deepcopy(self.cfg_data[self.current_key])
        new_cfg["game"] = game
        self.cfg_data[name] = new_cfg
        self.cmb_configs.addItem(name)
        self.cmb_configs.setCurrentText(name)

    def delete_config(self):
        if not self.current_key:
            return
        reply = QMessageBox.question(
            self, "Delete config",
            f"Are you REALLY sure you want to delete '{self.current_key}',\nfor {self.txt_game.text()}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.cfg_data.pop(self.current_key, None)
            self.cmb_configs.removeItem(self.cmb_configs.currentIndex())
            self.current_key = None