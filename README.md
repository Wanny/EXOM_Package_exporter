# EXOM_Package_exporter

This tool helps in exporting Packages from PS2 DDR and PC-based arcade DDR games, to make things a little easier when creating Packages for the DDR Extreme Omnimix.

## Extreme Omnimix? What's that? ##

It's a project made by someone else, to build a custom DDR Extreme Mix with the songs you like.<br>
The project is hosted privately and therefore I cannot provide more details... if you know, you know (sorry! ^^; )

## Why this? ##

Songs that can be used in the game are called "packages" in the Extreme Omnimix toolset.<br>
Thing is, old songs (from DDR 5th Mix and earlier) don't have the radar values and it's quite depressing to see an empty radar. Yes, I'm that picky.

A friend made a tool to get almost perfect values but it calculates them from an .sm file (not .ssq), what adds an extra hassle.<br>
And... many older songs do appear in CS games, so why not get the values from there?

And, most impòrtantly... the Omnimix "pack" that was released includes only a handful of CS songs (at the discretion of the tool's creator).


tl;dr: This helps on making "packages" from CS games.

## Oh kay... tell me more, what does this ACTUALLY do? ##

It exports the `package.json` file (for each song) needed by the Omnimix toolset.<br>
You'll have to get the actual files (song/preview mp3s, banner/bg, optional name card) yourself.



## Usage ##

### For the CLI version: ###

```bash
EXOM_PE_CLI.py [-h] [--config CONFIG] [--debug] file
```

Where:

* `file` is the only required file.
  * It can be a CS DDR executable (SLPM_xxx.yy/SLUS.xxx.yy/SLESxxx.yy) or an Arcade DDR `ddr.dll` file (only DDR X3 supported for now)
- `-h`shows the help
- `--config` loads a specific sonfiguration file. By default it uses `config.json` (included)
- `--debug` prints debut information. Useful if you want to see the titles of the exported songs (assuming I didn't mess up when making the configuration for a game)

### For the GUI version ###

* Launch it with `py EXOM_PE_GUI.py`
* On the window that opens, click on "Load binary file" and choose your desired file.
* See the list populate neatly (any reference to certain Wiki is absoolutely intentional)
* Click on  "Export packages"
