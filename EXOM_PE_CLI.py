#!/usr/bin/env python3
import argparse
import json
import os
import struct
from typing import Dict, List, Any

# ----------------------------
# Basic readers
# ----------------------------

def read_u8(chunk: bytes) -> int:
    return chunk[0]

def read_u16_le(chunk: bytes) -> int:
    return struct.unpack("<H", chunk)[0]

def read_u32_be(chunk: bytes) -> int:
    return struct.unpack(">I", chunk)[0]

# ----------------------------
# Difficulties per nibble
# Byte0: high=standard, low=light
# Byte1: high=challenge, low=heavy
# Byte2: low=beginner (high reserved. Double beginner?)
# Byte3: reserved
# ----------------------------

def parse_difficulties(raw_bytes: bytes) -> Dict[str, int]:
    if len(raw_bytes) != 4:
        raise ValueError("Difficulty block must be 4 bytes")
    b0, b1, b2, _ = raw_bytes
    standard  = (b0 >> 4) & 0xF
    light     = b0 & 0xF
    challenge = (b1 >> 4) & 0xF
    heavy     = b1 & 0xF
    beginner  = b2 & 0xF
    return {
        "beginner": beginner,
        "light": light,
        "standard": standard,
        "heavy": heavy,
        "challenge": challenge
    }

# -------------------
# Generic block parse
# -------------------

def parse_block(data: bytes, fields: List[List[Any]]) -> Dict[str, Any]:
    """
    Parser híbrido:
    - Formato secuencial: ["nombre", size, tipo]
    - Formato con offset: ["nombre", offset, size, tipo]
      El offset puede ser entero decimal o string "0x.." en hex.
    """
    result: Dict[str, Any] = {}
    offset = 0

    for field in fields:
        if len(field) == 3:
            # Formato secuencial
            name, size, ftype = field
            pos = offset
            offset += size
        elif len(field) == 4:
            # Formato con offset explícito
            name, pos, size, ftype = field
            # Convertir string "0x.." a entero
            if isinstance(pos, str):
                if pos.startswith("0x"):
                    pos = int(pos, 16)
                else:
                    pos = int(pos)  # por si viene como "12"
        else:
            raise ValueError(f"Formato de campo inválido: {field}")

        chunk = data[pos:pos+size]
        if len(chunk) != size:
            raise ValueError(f"Bloque incompleto al leer '{name}' (esperado {size}, got {len(chunk)})")

        if ftype == "string":
            result[name] = chunk.decode("ascii", errors="ignore").strip("\x00")
        elif ftype == "u8":
            result[name] = read_u8(chunk)
        elif ftype == "u16_le":
            result[name] = read_u16_le(chunk)
        elif ftype == "u32_be":
            result[name] = read_u32_be(chunk)
        elif ftype == "bytes":
            result[name] = chunk
        else:
            result[name] = chunk

    return result

# ----------------------------
# Radar block construction from individual values
# ----------------------------

def build_groove_radar(b: Dict[str, Any], include_single_beginner: bool = False) -> Dict[str, Any]:
    def grab(metric: str, mode: str, level: str) -> int:
        key = f"{metric}_{mode}_{level}"
        return b.get(key, 0)

    single = {
        "light": {
            "voltage": grab("voltage", "single", "light"),
            "stream":  grab("stream",  "single", "light"),
            "air":     grab("air",     "single", "light"),
            "chaos":   grab("chaos",   "single", "light"),
            "freeze":  grab("freeze",  "single", "light"),
        },
        "standard": {
            "voltage": grab("voltage", "single", "standard"),
            "stream":  grab("stream",  "single", "standard"),
            "air":     grab("air",     "single", "standard"),
            "chaos":   grab("chaos",   "single", "standard"),
            "freeze":  grab("freeze",  "single", "standard"),
        },
        "heavy": {
            "voltage": grab("voltage", "single", "heavy"),
            "stream":  grab("stream",  "single", "heavy"),
            "air":     grab("air",     "single", "heavy"),
            "chaos":   grab("chaos",   "single", "heavy"),
            "freeze":  grab("freeze",  "single", "heavy"),
        },
        "challenge": {
            "voltage": grab("voltage", "single", "challenge"),
            "stream":  grab("stream",  "single", "challenge"),
            "air":     grab("air",     "single", "challenge"),
            "chaos":   grab("chaos",   "single", "challenge"),
            "freeze":  grab("freeze",  "single", "challenge"),
        },
    }

    if include_single_beginner:
        single["beginner"] = {
            "voltage": grab("voltage", "single", "beginner"),
            "stream":  grab("stream",  "single", "beginner"),
            "air":     grab("air",     "single", "beginner"),
            "chaos":   grab("chaos",   "single", "beginner"),
            "freeze":  grab("freeze",  "single", "beginner"),
        }

    double = {
        "light": {
            "voltage": grab("voltage", "double", "light"),
            "stream":  grab("stream",  "double", "light"),
            "air":     grab("air",     "double", "light"),
            "chaos":   grab("chaos",   "double", "light"),
            "freeze":  grab("freeze",  "double", "light"),
        },
        "standard": {
            "voltage": grab("voltage", "double", "standard"),
            "stream":  grab("stream",  "double", "standard"),
            "air":     grab("air",     "double", "standard"),
            "chaos":   grab("chaos",   "double", "standard"),
            "freeze":  grab("freeze",  "double", "standard"),
        },
        "heavy": {
            "voltage": grab("voltage", "double", "heavy"),
            "stream":  grab("stream",  "double", "heavy"),
            "air":     grab("air",     "double", "heavy"),
            "chaos":   grab("chaos",   "double", "heavy"),
            "freeze":  grab("freeze",  "double", "heavy"),
        },
        "challenge": {
            "voltage": grab("voltage", "double", "challenge"),
            "stream":  grab("stream",  "double", "challenge"),
            "air":     grab("air",     "double", "challenge"),
            "chaos":   grab("chaos",   "double", "challenge"),
            "freeze":  grab("freeze",  "double", "challenge"),
        },
    }
    return {"single": single, "double": double}

# ------------------------------------------------------
# To build the difficulty block according to the old 1-10 scale or the modern 1-20 scale.
# The old difficulties were set with only 1 BIT, and nowadays they're set with a whole byte.
# Here a parameter is created to be set in the config.json file.
# 
# The field is called "difficulty_scale" and can be set to:
# - "1_10" (games prior to DDR X) or 
# - "1_20" (DDR X and later)
# ------------------------------------------------------

def build_difficulties(b: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    mode = cfg.get("difficulty_scale", "1_10")
    if mode == "1_10":
        single = parse_difficulties(b["single_difficulties"])
        double = parse_difficulties(b["double_difficulties"])
    elif mode == "1_20":
        single = {
            "beginner": b.get("single_beginner", 0),
            "light":    b.get("single_light", 0),
            "standard": b.get("single_standard", 0),
            "heavy":    b.get("single_heavy", 0),
            "challenge":b.get("single_challenge", 0),
        }
        double = {
            "beginner": b.get("double_beginner", 0),
            "light":    b.get("double_light", 0),
            "standard": b.get("double_standard", 0),
            "heavy":    b.get("double_heavy", 0),
            "challenge":b.get("double_challenge", 0),
        }
    else:
        raise ValueError(f"Unknown difficulty mode: {mode}")
    return {"single": single, "double": double}

# ----------------------------
# Function to parse titles from the file.
# This function is for games before DDR X, where the title is stored AFTER the short name
# ----------------------------

def parse_titles(data: bytes, start: int, end: int) -> dict:
    """
    Parser for classig games (short_first):
    - Short name (4–5 lowercase ASCII characters).
    - Then the title (ASCII text until a 0x00 character os found).
    - If what comex next doesn't look like a short name, it's considered as the Artist.
    - If what comes next DOES look like a short name, it's marked as orphan.
    """
    def skip_zeros(p: int) -> int:
        while p < end and data[p] == 0x00:
            p += 1
        return p

    def looks_like_short_name(data, pos, end):
        """Detexts if in 'pos' there os a valid short name (4–5 lowercase ASCII characters followed by NULLs)."""
        for ln in (4, 5):
            if pos + ln > end:
                continue
            chars = data[pos:pos+ln]
            if all((97 <= b <= 122) or (48 <= b <= 57) for b in chars):
                # contar nulos después
                zeros = 0
                j = pos + ln
                while j < end and data[j] == 0x00:
                    zeros += 1
                    j += 1
                if zeros >= 2:
                    return True
        return False

    pos = start
    titles_map = {}

    while pos < end:
        # read short name
        short_bytes = []
        while pos < end and data[pos] != 0x00:
            short_bytes.append(data[pos])
            pos += 1
        if not short_bytes:
            break
        short_name = bytes(short_bytes).decode("ascii", errors="ignore").strip().lower()

        # Skip 0x00s
        pos = skip_zeros(pos)

        # Check if what comes next is another short name (orphan)
        if looks_like_short_name(data, pos, end):
            titles_map[short_name] = ("Title goes here", "Title goes here")
            # Don't print debug info for orphans
            continue

        # Read title
        title_bytes = []
        while pos < end and data[pos] != 0x00:
            byte = data[pos]
            title_bytes.append(0x20 if byte == 0x0D else byte)
            pos += 1
        title = bytes(title_bytes).decode("ascii", errors="ignore").strip()

        # Skip 0x00s
        pos = skip_zeros(pos)

        artist = None
        # If what comes next  doesn't look like a short name, read it as the artist.
        if pos < end and not looks_like_short_name(data, pos, end):
            artist_bytes = []
            while pos < end and data[pos] != 0x00:
                artist_bytes.append(data[pos])
                pos += 1
            artist = bytes(artist_bytes).decode("ascii", errors="ignore").strip()
            pos = skip_zeros(pos)

        # Save
        if short_name:
            titles_map[short_name] = (title, title)
            # DEBUG only for exported songs

    return titles_map

# ----------------------------
# Function to parse titles from the file.
# This function is for games from DDR X nowards where the title is stored before the ahort name
# Be warned, the "title2" field may include other song's name because of "orphaned" titled.
# ----------------------------

def parse_titles_reverse(data: bytes, start: int, end: int) -> dict:
    """
     'title_first' table:
    - One or more titles (UTF-8/latin-1) termineted with 0x00
    - Then the short name (ASCII, 4–6 characters) terminated with 0x00
    - Repeat: title(s) -> short -> assign -> reset
    """
    def skip_zeros(p: int) -> int:
        while p < end and data[p] == 0x00:
            p += 1
        return p

    def read_c_string(buf, pos, limit):
        pos = skip_zeros(pos)
        if pos >= limit:
            return None, pos
        endpos = buf.find(b"\x00", pos, limit)
        if endpos == -1:
            return None, pos
        return buf[pos:endpos], endpos + 1

    def is_short_name(bs: bytes) -> bool:
        ln = len(bs)
        if ln < 4 or ln > 5:
            return False
        # Only lowercase letters and digits
        if not all((97 <= b <= 122 or 48 <= b <= 57) for b in bs):
            return False
        s = bs.decode("ascii", errors="ignore")
        # Avoid only numbers (unlikely but who knows)
        if s.isdigit():
            return False
        return True
    
    pos = start
    titles_map = {}
    acc_titles = []

    while pos < end:
        raw, newpos = read_c_string(data, pos, end)
        if raw is None:
            break

        if is_short_name(raw):
            short = raw.decode("ascii", errors="ignore").strip().lower()
            if acc_titles:
                # Save the complete list of titles.
                titles_map[short] = acc_titles[:]
            else:
                titles_map[short] = ["Title goes here"]
            acc_titles = []  # reset
        else:
            # Normalize control chars in the title.
            cleaned = bytes((0x20 if b in (0x0D, 0x0A) else b) for b in raw)
            try:
                t = cleaned.decode("utf-8").strip()
            except UnicodeDecodeError:
                t = cleaned.decode("latin-1").strip()
            if t:
                acc_titles.append(t)

        pos = newpos

    return titles_map

# ----------------------------
# Title Parser for SuperNOVA and SuperNOVA2. The stupid games use ONE 00 to separate music ID and title...
# and ONE 00 to separate the title from the next entry. Ugh.
# ----------------------------

def parse_titles_supernova(data: bytes, start: int, end: int) -> dict:
    """
    Parser para DDR Supernova:
    short name (ASCII) termanted with 0x00
    one ore more titles (UTF-8/latin-1) terminated with 0x00
    until the next short name appears.
    """
    def read_c_string(buf, pos, limit):
        endpos = buf.find(b"\x00", pos, limit)
        if endpos == -1:
            return None, pos
        return buf[pos:endpos], endpos + 1

    def is_short_name(bs: bytes) -> bool:
        # 4–5 lowercase ASCII characters
        return 4 <= len(bs) <= 5 and all((97 <= b <= 122) or (48 <= b <= 57) for b in bs)

    pos = start
    titles_map = {}

    while pos < end:
        # Read short name
        raw_short, pos = read_c_string(data, pos, end)
        if raw_short is None or len(raw_short) == 0:
            break
        if not is_short_name(raw_short):
            continue
        short_name = raw_short.decode("ascii", errors="ignore").strip().lower()

        # Read one or more titles untile another short name appears.
        titles = []
        while pos < end:
            raw, newpos = read_c_string(data, pos, end)
            if raw is None or len(raw) == 0:
                pos = newpos
                break
            if is_short_name(raw):
                # It's the next short name → exit the read loop.
                break
            try:
                title = raw.decode("utf-8").strip()
            except UnicodeDecodeError:
                title = raw.decode("latin-1").strip()
            titles.append(title)
            pos = newpos

        if titles:
            # Save all the titles.
            # The first found in a song is saved as main title and the second as alternate.
            if len(titles) == 1:
                titles_map[short_name] = (titles[0], titles[0])
            else:
                titles_map[short_name] = (titles[0], titles[1])
        else:
            titles_map[short_name] = ("Title goes here", "Title goes here")

    return titles_map

# ----------------------------
# Ewport: global (single file) and per song.
# ----------------------------
def block_to_package(b: Dict[str, Any], cfg: Dict[str, Any], slpm_name: str, titles_map: dict) -> Dict[str, Any]:
    include_beginner = bool(cfg.get("include_radar_single_beginner", False))
    music_id = b["music_id"].lower()

    # Titles from the table (if existing)
    raw_titles = titles_map.get(music_id, ["Title goes here"])
    # Normalize: if it's a tupla, convert to list
    if isinstance(raw_titles, tuple):
        raw_titles = list(raw_titles)
    # Ensure at least 2 elements
    if len(raw_titles) == 1:
        title, title2 = raw_titles[0], raw_titles[0]
    else:
        title, title2 = raw_titles[0], raw_titles[1]

    return {
        "music_id": music_id,
        "title": title,
        "title2": title2,
        "artist": "Artist goes here",
        "bpms": [b.get("bpm1", 0), b.get("bpm2", 0)],
        "memory_card_link_id": b.get("memcard_link_id", 0),
        "difficulties": build_difficulties(b, cfg),
        "groove_radar": build_groove_radar(b, include_single_beginner=include_beginner),
        "_origin": slpm_name,
        "data": {
            "title": f"{music_id}_nm.png",
            "background": f"{music_id}_bk.png",
            "banner_preview": f"{music_id}_ta.png",
            "banner": f"{music_id}_th.png",
            "chart": f"{music_id}.csq",
            "song": "song.mp3",
            "preview": "preview.mp3"
        },
        "album": cfg.get("game", "DDR CS"),
        "game_category": "DDR CS"
    }

# ----------------------------
# Consecutive block read
# ----------------------------
def read_consecutive_blocks(file_name: str, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    bloques: List[Dict[str, Any]] = []
    with open(file_name, "rb") as f:
        start = int(cfg["offset"])
        end = int(cfg["end_offset"])
        size = int(cfg["block_size"])

        if end < start:
            raise ValueError("end_offset cannot be lower than offset.")
        total = end - start
        if total % size != 0:
            print(f"WARNING: block range ({hex(start)}–{hex(end)}) is not an exact multiple of block_size {hex(size)}.")

        num_bloques = total // size
        f.seek(start)

        for _ in range(num_bloques):
            data = f.read(size)
            if not data or len(data) < size:
                break
            bloque = parse_block(data, cfg["fields"])
            bloques.append(bloque)

    return bloques

# ----------------------------
# External config. reading
# ----------------------------
def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------
# Main / CLI
# ----------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extracts data from binary DDR data to a single JSON and a package.json per song"
    )
    parser.add_argument("file", help="Binary file path (e.g. SLPM_624.27)")
    parser.add_argument("--config", default="config.json", help="JSON configuration file path")
    parser.add_argument("--debug", action="store_true", help="Ptint debug information")
    args = parser.parse_args()

    # Load config .json file and throw an error if there's no config for the input file.
    cfg_all = load_config(args.config)
    basename = os.path.basename(args.file)
    if basename not in cfg_all:
        print(
            f"There's no config set for '{basename}'.\n"
            f"Existing configurations:\n- " + "\n- ".join(cfg_all.keys())
        )
        return

    cfg = cfg_all[basename]

    # Read all the file in memory (for titles)
    with open(args.file, "rb") as f:
        data = f.read()

    # Pick titles parser from the config file
    titles_map = {}
    title_start = cfg.get("titles_offset_start")
    title_end   = cfg.get("titles_offset_end")
    if isinstance(title_start, int) and isinstance(title_end, int) and title_end > title_start:
        parser_name = cfg.get("titles_parser", "parse_titles")
        if parser_name == "parse_titles":
            titles_map = parse_titles(data, title_start, title_end)
        elif parser_name == "parse_titles_reverse":
            titles_map = parse_titles_reverse(data, title_start, title_end)
        elif parser_name == "parse_titles_supernova":
            titles_map = parse_titles_supernova(data, title_start, title_end)


    # Read binary blocks
    bloques = read_consecutive_blocks(args.file, cfg)

    # Normalide ID blocks
    for b in bloques:
        b["music_id"] = b["music_id"].strip().lower()

    # Filter titles only for existing music IDs
    valid_ids = {b["music_id"].lower() for b in bloques}
    titles_map = {k: v for k, v in titles_map.items() if k in valid_ids}

    # Manual overrides
    manual_titles = cfg.get("manual_titles", {})
    for b in bloques:
        mid = b["music_id"].lower()
        if mid in manual_titles:
            titles_map[mid] = (manual_titles[mid], manual_titles[mid])


    # Optional DEBUG output. Songs are listed in the orher they appear in the file.
    if args.debug:
        for b in bloques:
            mid = b["music_id"].lower()
            raw_titles = titles_map.get(mid, ["Title goes here"])
            # Normalize: tuple → list
            if isinstance(raw_titles, tuple):
                raw_titles = list(raw_titles)
            # Ensure at least 2 values
            if len(raw_titles) == 1:
                title, title2 = raw_titles[0], raw_titles[0]
            else:
                title, title2 = raw_titles[0], raw_titles[1]
            print(f"DEBUG short={mid!r}, title={title!r}")
        #Generate orphaned songs.
        orphans = [mid for mid, titles in titles_map.items() if titles[0] == "Title goes here"]
        print("")
        print(f"Total orphans detected: {len(orphans)}")
        print("Complete list:", orphans)
        print("")

    # Build global JSON and packages
    json_data = []
    for b in bloques:
        pkg = block_to_package(b, cfg, basename, titles_map)
        json_data.append(pkg)

    # Export per song
    game_name = cfg.get("game", os.path.splitext(basename)[0])
    root_outdir = f"{game_name}_packages"
    os.makedirs(root_outdir, exist_ok=True)

    # Export songs.json file with ALL the packagd for the songs in the folders.
    songs_path = os.path.join(root_outdir, "songs.json")
    with open(songs_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

    for pkg in json_data:
        folder = os.path.join(root_outdir, pkg["music_id"])
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "package.json"), "w", encoding="utf-8") as f:
            json.dump(pkg, f, indent=4, ensure_ascii=False)

    print(f"Exported {len(json_data)} blocks  to songs.json y packages per song to '{root_outdir}/<music_id>/'")

if __name__ == "__main__":
    main()