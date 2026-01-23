import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QLabel
)
from PySide6.QtGui import QFont, QColor,QBrush
from PySide6.QtCore import Qt

# Importa tus funciones del CLI
from EXOM_PE_CLI import (
    load_config, parse_titles, parse_titles_reverse, parse_titles_supernova,
    read_consecutive_blocks, block_to_package, build_difficulties
)

# Colores por dificultad - tal como en RemyWiki.
DIFF_COLORS = {
    "beginner": QColor("#81E9FF"),  # celeste
    "light": QColor("#FFFFAA"),     # amarillo
    "standard": QColor("#FFAAAA"),  # rojo
    "heavy": QColor("#00FF7F"),     # verde
    "challenge": QColor("#DDAAFF")  # lila
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DDR Extreme Omnimix Package Creator GUI")

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Pestaña Extracción
        self.tab_extract = QWidget()
        self.tabs.addTab(self.tab_extract, "Export")

        layout = QVBoxLayout()

        # Label para mostrar el juego
        self.lbl_game = QLabel("Game: (no file loaded)")
        layout.addWidget(self.lbl_game)

        self.btn_load = QPushButton("Load binary file")
        self.btn_load.clicked.connect(self.load_file)
        layout.addWidget(self.btn_load)

        # Tabla de canciones
        self.song_table = QTableWidget()
        self.song_table.setColumnCount(13)
        self.song_table.setHorizontalHeaderLabels([
            "ID", "Title", "BPM",
            "SP Beg", "SP Lgt", "SP Std", "SP Hvy", "SP Chl",
            "DP Beg", "DP Lgt", "DP Std", "DP Hvy", "DP Chl"
        ])
        self.song_table.setFont(QFont("Segoe UI", 10)) 
        layout.addWidget(self.song_table)

        # Ajustar anchos de columnas
        self.song_table.setColumnWidth(0, 45)   # ID
        self.song_table.setColumnWidth(1, 250)  # Título
        self.song_table.setColumnWidth(2, 65)   # BPM
        # SP y DP: compactos
        for c in range(3, 13):
            self.song_table.setColumnWidth(c, 50)



        self.btn_extract = QPushButton("Export Packages")
        self.btn_extract.setEnabled(False)
        self.btn_extract.clicked.connect(self.extract_songs)
        layout.addWidget(self.btn_extract)

        self.tab_extract.setLayout(layout)

        # Estado
        self.current_file = None
        self.current_config = None
        self.titles_map = {}
        self.bloques = []

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose binary file")
        if not file_path:
            return

        # Cargar config.json
        try:
            cfg_all = load_config("config.json")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer config.json\n{e}")
            return

        basename = os.path.basename(file_path)
        if basename not in cfg_all:
            QMessageBox.warning(self, "Juego no encontrado",
                                f"No hay configuración para '{basename}'")
            return

        self.current_file = file_path
        self.current_config = cfg_all[basename]

        # Mostrar nombre del juego
        game_name = self.current_config.get("game", basename)
        self.lbl_game.setText(f"Game: {game_name}")

        # Leer archivo completo
        with open(file_path, "rb") as f:
            data = f.read()

        # Parsear títulos
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

        # Leer bloques binarios
        bloques = read_consecutive_blocks(file_path, self.current_config)
        for b in bloques:
            b["music_id"] = b["music_id"].strip().lower()

        # Filtrar títulos solo para IDs válidos
        valid_ids = {b["music_id"] for b in bloques}
        titles_map = {k: v for k, v in titles_map.items() if k in valid_ids}

        # Overrides manuales
        manual_titles = self.current_config.get("manual_titles", {})
        for b in bloques:
            mid = b["music_id"]
            if mid in manual_titles:
                titles_map[mid] = (manual_titles[mid], manual_titles[mid])

        # Mostrar en tabla
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

            # ID, título y BPM
            self.song_table.setItem(row, 0, QTableWidgetItem(mid))
            self.song_table.setItem(row, 1, QTableWidgetItem(title))
            self.song_table.setItem(row, 2, QTableWidgetItem(bpm_str))

            # SP con colores
            self._fill_diffs(sp, row, 3)
            # DP con colores
            self._fill_diffs(dp, row, 8)

        # Guardar estado
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
            item.setForeground(QBrush(text_colors[lvl]))  # 👈 color del texto
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())