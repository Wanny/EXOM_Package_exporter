# EXOM_Package_exporter

This tool helps in exporting Packages from PS2 DDR and PC-based arcade DDR games, to make things a little easier when creating Packages for the DDR Extreme Omnimix.

## DDR Extreme Omnimix? What the F is that?

It's a project made by someone else, to build a custom DDR Extreme Mix with whatever songs you like (up to the maximum allowed by the game engine)
The project is hosted privately and therefore I cannot provide more details... if you know, you know (sorry! ^^; )

## Why this?
Story time!

First of all, songs that can be used in the game are called "packages" in the Extreme Omnimix toolset

I was manually creating packages for songs that weren't included in the released Omnimix pack, and the radars were empty... and they look bad.

A friend made a tool to get almost perfect values but it calculates them from an `.sm` file (not the game's `.ssq` format), which  adds an extra hassle.

And then, by reading the code of the Omnimix tool, it mentions that the radar values ARE atored in the game data. I managed to find them in the game I was taking the song from and they worked!

So I was like "hmm, if they are all stored in the same position for each entry of the game, why not a tool that gets them from all the songs at once?

tl;dr: This helps on making "packages" from DDR games.

## Oh kay... I have questions, tell me more.

### What does this ACTUALLY do?

Simply put, It creates the `package.json` file (for each song present in a game) needed by the Omnimix toolset.

### Oh, and what do I need?

Only one file!

* For PS2 games, you need the executable. It is the `SLPM_xxx.yy`/`SLUS_xxx.yy`/`SLES_xxx.yy` file that's on the root of the game's disc
* For arcade games (only DDR X3 supported for now) you need the `ddr.dll` file.

### What about the actual files? You know, the audio, step data, etc?

You have to source them yourself, as that's out of the scope of this tool.

## Usage

### For the CLI version:

```bash
EXOM_PE_CLI.py [-h] [--config CONFIG] [--debug] file
```

Where:

* `file` is the only required file (see above)  
* `-h`shows the help
* `--config` loads a specific sonfiguration file. By default it uses `config.json` (included)
* `--debug` prints debut information. Useful if you want to see the titles of the exported songs (assuming I didn't mess up when making the configuration for a game)

### For the GUI version:

* Launch it with `py EXOM_PE_GUI.py`
* On the window that opens, click on "Load binary file" and choose your desired file.
* See the list populate neatly (any resemblance to certain Wiki is absolutely intentional)
* Click on  "Export packages"
* Additioanlly, you can export the contents of the table to an Excel file with the "Export to Excel" button.

#### Important 
The GUI version uses existing functions from the CLI version.
You must download **both** versions.
