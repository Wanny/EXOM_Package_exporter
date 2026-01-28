import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,QHBoxLayout, QSpacerItem, QSizePolicy,
    QPushButton, QFileDialog, QMessageBox, QTabWidget,QTableWidget,QTableWidgetItem, QLabel,QFileDialog
)
from PySide6.QtGui import QFont, QColor,QBrush
from PySide6.QtCore import Qt

import pandas as pd
import xlsxwriter

# Importing functions from the CLI module
from EXOM_PE_CLI import (
    load_config, parse_titles, parse_titles_reverse, parse_titles_supernova,
    parse_titles_sequential,read_consecutive_blocks, block_to_package, build_difficulties
)

# Background colors for difficulties. Shamelessly taken from Remywiki.
DIFF_COLORS = {
    "beginner": QColor("#81E9FF"), 
    "light": QColor("#FFFFAA"),    
    "standard": QColor("#FFAAAA"),  
    "heavy": QColor("#00FF7F"),     
    "challenge": QColor("#DDAAFF") 
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DDR Extreme Omnimix Package Creator GUI")

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Extract tab
        self.tab_extract = QWidget()
        self.tabs.addTab(self.tab_extract, "Export")

        layout = QVBoxLayout()

        # Label to show the gane name
        self.lbl_game = QLabel("Game: **NO FILE LOADED**")
        layout.addWidget(self.lbl_game)

        self.btn_load = QPushButton("Load binary file")
        self.btn_load.setStyleSheet("""
            QPushButton {
                background-color: #131380;
                color: white;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton:pressed {
                background-color: #2c2c47;
            }
        """)
        self.btn_load.clicked.connect(self.load_file)

        self.btn_export_excel = QPushButton("Export to Excel")
        self.btn_export_excel.setEnabled(False)
        self.btn_export_excel.setStyleSheet("""
            QPushButton:enabled {
                background-color: #075e07;
                color: white;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton:disabled {
                background-color: #042f04;
            }                                            
            QPushButton:pressed {
                background-color: #042f04;
            }
        """)
        self.btn_export_excel.clicked.connect(self.export_to_excel)

        self.btn_extract = QPushButton("Export Packages")
        self.btn_extract.setEnabled(False)
        self.btn_extract.setStyleSheet("""
            QPushButton:enabled {
                background-color: #914e0a;
                color: white;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton:disabled {
                background-color: #442211;
            }                                            
            QPushButton:pressed {
                background-color: #442211;
            }
        """)
        self.btn_extract.clicked.connect(self.extract_songs)

        #group buttons in the same line
        bottom_layout = QHBoxLayout()
        
        bottom_layout.addWidget(self.btn_load)
        bottom_layout.addWidget(self.btn_extract)
        bottom_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        bottom_layout.addWidget(self.btn_export_excel) 
        layout.addLayout(bottom_layout)

        # Song table
        self.song_table = QTableWidget()
        self.song_table.setColumnCount(13)
        self.song_table.setHorizontalHeaderLabels([
            "ID", "Title", "BPM",
            "SP Beg", "SP Lgt", "SP Std", "SP Hvy", "SP Chl",
            "DP Beg", "DP Lgt", "DP Std", "DP Hvy", "DP Chl"
        ])
        self.song_table.setFont(QFont("Segoe UI", 10)) 
        layout.addWidget(self.song_table)

        # Ajdjust column width
        self.song_table.setColumnWidth(0, 45)   # ID
        self.song_table.setColumnWidth(1, 250)  # Título
        self.song_table.setColumnWidth(2, 65)   # BPM
        for c in range(3, 13):
            self.song_table.setColumnWidth(c, 50) #difficulties

        self.tab_extract.setLayout(layout)

        # State
        self.current_file = None
        self.current_config = None
        self.titles_map = {}
        self.bloques = []

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose binary file")
        if not file_path:
            return

        # Load config.json
        try:
            cfg_all = load_config("config.json")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"config.json couldn't be read\n{e}")
            return

        basename = os.path.basename(file_path)
        if basename not in cfg_all:
            QMessageBox.warning(self, "Game not found",
                                f"There's no config for '{basename}'")
            return

        self.current_file = file_path
        self.current_config = cfg_all[basename]

        # Show gane name.
        game_name = self.current_config.get("game", basename)
        self.lbl_game.setText(f"Game: {game_name}")

        # enable the Export to Excel button.
        self.btn_extract.setEnabled(True)
        self.btn_export_excel.setEnabled(True)

        # Read the entire file
        with open(file_path, "rb") as f:
            data = f.read()

        # Read binary blocks
        bloques = read_consecutive_blocks(file_path, self.current_config)

        # Parse titles
        ts, te = self.current_config.get("titles_offset_start"), self.current_config.get("titles_offset_end")
        titles_map = {}
        if isinstance(ts, int) and isinstance(te, int) and te > ts:
            parser_name = self.current_config.get("titles_parser", "parse_titles")
            if parser_name == "parse_titles":
                titles_map = parse_titles(data, ts, te)
            elif parser_name == "parse_titles_reverse":
                titles_map = parse_titles_reverse(data, ts, te)
            elif parser_name == "parse_titles_supernova":
                titles_map = parse_titles_supernova(data, ts, te)
            elif parser_name == "parse_titles_sequential":
                titles_list = parse_titles_sequential(data, ts, te)
                titles_map = {}
                for i, b in enumerate(bloques):
                    mid = b["music_id"].lower()
                    if i < len(titles_list):
                        titles_map[mid] = (titles_list[i], titles_list[i])
                    else:
                        titles_map[mid] = ("Title goes here", "Title goes here")


        # Filter titles only for valid IDs
        valid_ids = {b["music_id"] for b in bloques}
        titles_map = {k: v for k, v in titles_map.items() if k in valid_ids}

        # Manual Overrides
        manual_titles = self.current_config.get("manual_titles", {})
        for b in bloques:
            mid = b["music_id"]
            if mid in manual_titles:
                titles_map[mid] = (manual_titles[mid], manual_titles[mid])

        # Show table
        self.song_table.setRowCount(len(bloques))
        for row, b in enumerate(bloques):
            mid = b["music_id"]
            raw_titles = titles_map.get(mid, ["Title goes here"])
            if isinstance(raw_titles, tuple):
                raw_titles = list(raw_titles)
            title = raw_titles[0]

            bpm1, bpm2 = b.get("bpm1", 0), b.get("bpm2", 0)
            bpm_str = str(bpm1) if bpm1 == bpm2 else f"{bpm2}-{bpm1}"

            diffs = build_difficulties(b, self.current_config)
            sp = diffs["single"]
            dp = diffs["double"]

            # ID, title and BPM
            self.song_table.setItem(row, 0, QTableWidgetItem(mid))
            self.song_table.setItem(row, 1, QTableWidgetItem(title))
            self.song_table.setItem(row, 2, QTableWidgetItem(bpm_str))

            # SP con colores
            self._fill_diffs(sp, row, 3)
            # DP con colores
            self._fill_diffs(dp, row, 8)

        # Save state
        self.titles_map = titles_map
        self.bloques = bloques
        self.btn_extract.setEnabled(True)

    def _fill_diffs(self, d, row, col_start):
        levels = ["beginner", "light", "standard", "heavy", "challenge"]
        text_colors = {
            "beginner": QColor(0, 0, 0),   
            "light": QColor(0, 0, 0),      
            "standard": QColor(0, 0, 0), 
            "heavy": QColor(0, 0, 0),    
            "challenge": QColor(0, 0, 0) 
        }

        for i, lvl in enumerate(levels):
            val = d.get(lvl, 0)
            text = str(val) if val != 0 else "-"
            item = QTableWidgetItem(text)
            item.setBackground(DIFF_COLORS[lvl])
            item.setTextAlignment(Qt.AlignCenter)
            font = QFont("Cascadia Mono", 11)
            font.setBold(True)
            item.setFont(font)
            item.setForeground(QBrush(text_colors[lvl]))  # text color
            self.song_table.setItem(row, col_start + i, item)

    def extract_songs(self):
        if not self.current_file or not self.current_config:
            QMessageBox.warning(self, "Error", "No file loaded.")
            return

        basename = os.path.basename(self.current_file)
        json_data = []
        for b in self.bloques:
            pkg = block_to_package(b, self.current_config, basename, self.titles_map)
            json_data.append(pkg)

        outdir = f"{self.current_config.get('game', basename)}_packages"
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "songs.json"), "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

        for pkg in json_data:
            folder = os.path.join(outdir, pkg["music_id"])
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "package.json"), "w", encoding="utf-8") as f:
                json.dump(pkg, f, indent=4, ensure_ascii=False)

        QMessageBox.information(self, "Done!",
                                f"Exported {len(json_data)} packages to '{outdir}'")
    
    def export_to_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save table...",
            f"{self.current_config.get('game','DDR')}_songs.xlsx",
            "Excel file (*.xlsx)"
        )
        if not file_path:
            return

        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet("Songs")

        # Formats
        header_fmt = workbook.add_format({"bold": True, "align": "left", "bg_color": "#366092", "font_color": "white"})
        num_fmt = workbook.add_format({"bold": False, "align": "left"})
        # Colors per difficulty, same as in the GUI
        diff_formats = {
            "beginner": workbook.add_format({"bold": True, "align": "center", "bg_color": "#81E9FF"}),
            "light": workbook.add_format({"bold": True, "align": "center", "bg_color": "#FFFFAA"}),
            "standard": workbook.add_format({"bold": True, "align": "center", "bg_color": "#FFAAAA"}),
            "heavy": workbook.add_format({"bold": True, "align": "center", "bg_color": "#00FF7F"}),
            "challenge": workbook.add_format({"bold": True, "align": "center", "bg_color": "#DDAAFF"})
        }

        # Column widths 

        # ID, Title, BPM
        worksheet.set_column(0, 0, 7)   # ID
        worksheet.set_column(1, 1, 60)   # Title
        worksheet.set_column(2, 2, 8)    # BPM

        # Difficulties
        worksheet.set_column(3, 7, 6)    # SP 
        worksheet.set_column(8, 12, 6)   # DP 

        # Save headers
        headers = [self.song_table.horizontalHeaderItem(c).text() for c in range(self.song_table.columnCount())]
        for col, h in enumerate(headers):
            worksheet.write(0, col, h, header_fmt)

        # Save lines
        for r in range(self.song_table.rowCount()):
            for c in range(self.song_table.columnCount()):
                item = self.song_table.item(r, c)
                text = item.text() if item else ""

                # Detect difficulty column, to set color
                col_name = headers[c].lower()
                if "beg" in col_name:
                    fmt = diff_formats["beginner"]
                elif "lgt" in col_name:
                    fmt = diff_formats["light"]
                elif "std" in col_name:
                    fmt = diff_formats["standard"]
                elif "hvy" in col_name:
                    fmt = diff_formats["heavy"]
                elif "chl" in col_name:
                    fmt = diff_formats["challenge"]
                else:
                    fmt = num_fmt

                # Store values as numbers when possible, so Excel doesn't bother with "number stored as text" when you open the file.
                try:
                    num_val = int(text) if text != "-" else None
                except ValueError:
                    num_val = None

                if num_val is not None:
                    worksheet.write_number(r+1, c, num_val, fmt)
                else:
                    worksheet.write(r+1, c, text, fmt)

        worksheet.freeze_panes(1, 0)
        
        workbook.close()

        QMessageBox.information(self, "Done!", f"Table exported to '{file_path}'")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())