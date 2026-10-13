# Echo VR Personal Disc add-on (for the Echo Mods Pack)

The personal disc everywhere in Echo VR (lobby, timeouts, and from a goal until the launcher
countdown ends), summoned with a Touch button. Two parts:

- `patch_personal_disc.py` (INSTALL.cmd / RESTORE.cmd): the Personal Disc Everywhere patch, v3.5.
  It changes two script DLLs of your own game by a few bytes and keeps backups; RESTORE.cmd puts
  the originals back. Details and the exact rules: README.md.
- `discbutton\`: DiscButton.dll, an EchoLoader plugin. Press X (left controller; A, B or Y in its
  settings) and the disc comes to your hand. The arcade tablet's SETTINGS gets a DISC page.

## Install

Put **EchoPersonalDisc.zip** in your **EchoModsPack** folder (or unzip it there, or next to the
pack folder) and run the pack's **INSTALL.cmd**: it installs the disc along with the HUD and the
arcade. **UNINSTALL.cmd** takes it out again (RESTORE.cmd here does the DLLs alone). The pack's
CHECK.cmd shows whether the disc patch and the button are in.

Without the pack: close Echo VR, run `INSTALL.cmd` here, then `py -3 discbutton\install_discbutton.py`.

## Credits

The patch is [nmdurkee's Personal Disc Everywhere](https://github.com/nmdurkee/EchoVR-Personal-Disc-Everywhere)
(v3.0.1), continued here as v3.5 (the disc stays from a goal until the launcher countdown ends,
no arm popup). It is redistributed here without a licence from its author; it comes down the
day he asks. DiscButton by Decay-echo. [MinHook](https://github.com/TsudaKageyu/minhook) (BSD
2-Clause, `discbutton\minhook\LICENSE.txt`). No Echo VR files are included: the patch edits
your own game's DLLs on your PC.
