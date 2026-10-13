# Echo VR Personal Disc Everywhere v3.0.1

> **Local build: v3.5 goal+launcher+tunnel A-button, no popup.** This copy also allows the personal disc from a goal until the tunnel opens, in public and private matches. That covers the goal, the replay, the "get to your launcher" wait (`team_room_wait`), the move into the tunnel, and the tunnel countdown, which also happens at the start of each round. As play (`main_loop`) begins, the mod runs the stock disable, which hides the disc. Live play, overtime and sudden death stay blocked. `INSTALL.cmd` upgrades v3.0.1, v3.1, v3.3 or v3.4 in place, and `RESTORE.cmd` still restores the original game files. The unmodified v3.0.1 files are in `backup-v3.0.1-original\`.
>
> **v3.5 keeps the disc at "get to your launcher".** After the replay the game enters `team_room_wait`, and entering it sends `nevt_disable_local_disc`. v3.4 didn't allow that state, so the disable went through and hid your disc. v3.5 allows it, which blocks that disable.
>
> **X button (`discbutton\`).** `DiscButton.dll` is an EchoLoader plugin. It hooks `ovr_GetInputState` and passes presses of the left controller's X button (or another one: `[summon] button=` A, B, X or Y in `plugins\DiscButton\settings.ini`) to the patch through a summon block in `38965d90a823f03f.dll`. The patch sets the same `requested_teleport` flag the arm popup's `evt_respawn_local_disc` sets, only while the disc is allowed and only for presses under about a second old. Build it with `discbutton\build_discbutton.cmd`, and install or remove it with `py -3 discbutton\install_discbutton.py [--uninstall]`. Every other button, A included, works in Echo as it always did; `hide_from_echo=1` would also hide the summon button from Echo. While Echo Arcade's FREEZE has the controllers, the button plays RetroArch instead. The log is at `%LOCALAPPDATA%\DiscButton\discbutton.log`.
>
> **v3.4 has no arm popup**, so there is no sound, vibration or popup on enable or disable. Nodes `0x9d959ce0` and `0x49eb587d` are skipped. That popup was the stock summon button (its `event` is `evt_respawn_local_disc`), so **v3.4 needs DiscButton.dll: without it the disc can't be summoned.** For the popup back, install v3.3 or v3.1.
>
> | DLL | v3.5 SHA256 |
> | --- | --- |
> | `351c49438bd38225.dll` | `6924f10fda85dfec36028ce1153b7de0fd72e154ab7bf57ffe710101b9a1d53f` |
> | `38965d90a823f03f.dll` | `e8bb4fbcfae83f35fbc3ab76fa3f5b6c4f6a09fb7b19cf5ca777b7aaa032f12e` |
>
> **Untested in game:** the hide as the tunnel opens. It's the stock disable path (`evt_disable_local_disc`, which sends `evt_glb_hide_local_disc`), but check it in a private match: a disc you're holding when the gates open should vanish, not carry into play.

Spawn the personal disc outside the usual court regions in **Windows PC Echo VR**, with **v3 round restrictions** to prevent abuse during matches. Apply the patch once; no background app is required.

## v3.0.1 loading fix

v3.0.0 produced invalid DLL section layouts that Windows rejects with error 193, causing reported "failed to load level" errors. v3.0.1 fixes the layout and supports direct upgrades from v3.0.0, including partially upgraded pairs. Close Echo VR and run this version of `INSTALL.cmd`. To recover without installing the fix, run `RESTORE.cmd`.

Both fixed DLLs pass Windows executable-image loading checks. In-game loading and round/timeout behavior still need confirmation.

## Why v3 restricts spawning

The unrestricted v2 patch allowed spawning during play. The project owner reported that spawning and grabbing a personal disc could immediately set the player's speed to **4.7 m/s**, creating a cheating opportunity. **Upgrade from v2 to v3.** This version disables personal-disc spawning throughout a round, with an exception for actual timeouts.

| Game situation | Personal-disc spawning |
| --- | --- |
| Social lobby / supported pre-match waiting states | Enabled |
| Round start, launch/countdown, active play, overtime | Disabled |
| Goal scored, replay, and the next launch | Stays disabled (**v3.1+: enabled until the tunnel opens**; v3.5 also through "get to your launcher") |
| Timeout requested but not yet active | Stays disabled |
| Actual timeout (`PAUSED`) | Enabled |
| Timeout ends / game becomes unpaused | Disabled again |
| Round over and supported post-round / post-match states | Enabled |
| Missing or unrecognized match state | Disabled |

The patch uses round and timeout state, rather than whether the clock is moving. **A goal does not re-enable the control or trigger another activation ding.** It also rejects personal-disc respawn requests while disabled, clears queued requests, and cancels requests waiting for permission to teleport when play resumes. Normal match discs retain their original request behavior.

This is a restriction in the patched client, not server-enforced anti-cheat. It cannot prevent someone from running an older or independently modified client.

## Requirements

- Windows PC Echo VR; this does not patch the Quest APK.
- Python 3.8 or newer. No extra Python packages are needed.
- The supported versions of **both** DLLs listed below. Compatibility is checked automatically.
- Echo VR completely closed while installing or restoring.

Combat maps that do not load the personal-disc controller are not covered.

## Install or upgrade from v2

1. [Download the repository ZIP](https://github.com/nmdurkee/EchoVR-Personal-Disc-Everywhere/archive/refs/heads/main.zip).
2. Extract it to a folder. Do not run from inside the ZIP.
3. Install Python 3 if needed, with the Python launcher or `python` command available.
4. Close Echo VR completely.
5. Double-click **`INSTALL.cmd`**.
6. If prompted, paste your Echo VR game folder or the path to `echovr.exe`.
7. Wait for **`Personal Disc v3.0.1 installed and verified.`** Then start Echo VR.

For **Access denied**, right-click `INSTALL.cmd` and choose **Run as administrator**.

The installer upgrades the exact v2 controller automatically; there is no need to restore first. It validates both DLLs and their backups before modifying the installed files, verifies the result, and attempts to roll back the pair if an installation fails. If rollback cannot finish, it reports the affected files: close Echo VR and run `RESTORE.cmd` before launching it.

### How it finds the game

The script checks Windows Program Files locations for standard **Meta Horizon** and **Oculus** installations, plus its own folder and the current working folder. It does not depend on a particular Windows username.

If no installation is found, or multiple installations are found, it asks for a path. You can specify one explicitly:

```powershell
py -3 patch_personal_disc.py --target "D:\Games\EchoVR"
```

Accepted paths include the game folder, `echovr.exe`, `bin\win10`, the `scripts` folder, or `351c49438bd38225.dll`. The second DLL must be in the same scripts folder.

## Uninstall / restore

Close Echo VR and run **`RESTORE.cmd`**, as administrator if needed. Wait for **`Original DLLs restored and verified.`** Both files are restored to stock, including when you originally upgraded from v2.

Verified backups are stored beside the game DLLs:

```text
bin\win10\scripts\351c49438bd38225.dll.personal-disc.original
bin\win10\scripts\38965d90a823f03f.dll.personal-disc.original
```

If backups are missing, the patcher can reconstruct and hash-check the originals from the exact supported v3 files or the v2 controller. Unknown revisions and mismatched backups are rejected.

## Command line

The Python script works by itself; the launchers are optional.

```powershell
# Install or upgrade, detecting the game or prompting for its location
py -3 patch_personal_disc.py

# Check both DLLs without changing files
py -3 patch_personal_disc.py --check

# Install to a custom location
py -3 patch_personal_disc.py --target "D:\Games\EchoVR"

# Restore both originals
py -3 patch_personal_disc.py --restore
```

If your system uses `python` instead of `py`, replace `py -3` with `python`.

## Validation and limitations

**v3.0.1 passed Windows loader checks, 9 isolated native-code tests, and 15 installer tests. In-game loading and round/timeout behavior have not yet been confirmed for this fix.** v2 spawning was previously confirmed in game. Multiplayer replication and behavior across all maps/modes remain unverified.

- **9 native-code tests:** round/goal/replay transitions without repeated activation, actual timeout versus requested timeout, timeout resume, round over, active-round joins, pending activation cancellation, queued respawn cancellation, social availability, non-personal-disc behavior, and PE section/unwind integrity.
- **15 installer tests:** Windows loader acceptance (and rejection of the broken v3.0.0 files), v3.0.0 upgrade/restoration, mixed-version repair, parity with the tested payload, stock install, v2 upgrade, repeat installation, restore with and without backups, unsupported files, mismatched backups, read-only checking, running-game rejection, partial-install repair, custom paths, and rollback after simulated failures.

For in-game validation, check that spawning works before a round, stays unavailable through play and a goal/replay, becomes available only once a timeout is active, stops on unpause, and returns after round over. Check normal arena-disc behavior and whether a personal disc held at timeout end remains usable; that carry-over case is not established by the isolated tests.

The installer uses only the Python standard library. It requires no network access, Frida, MCP, or Revault. The embedded payload is built from [src/round_guard.c](src/round_guard.c); no complete game DLL is distributed.

| DLL | Original SHA256 | v3.0.1 SHA256 |
| --- | --- | --- |
| `351c49438bd38225.dll` (controller) | `a8a8e156223ba10246f867e4513d272f5d89f0c3b5bd1a3167682176a429c4c1` | `5421de8a34703d9872df0fa3841443eee8a28577fb50461cc5c01e2911bcd911` |
| `38965d90a823f03f.dll` (disc actor) | `777653b7547925b2c86bf5f343848564b3c07c6efd8df421acbb629604ed67ed` | `deca1e86cd437116a1afab07bcf228274d9d51274b385a92ab7568d346759c75` |

## Troubleshooting

| Message / issue | Action |
| --- | --- |
| Python not found | Install Python 3 and reopen the launcher. |
| Access denied | Run the install/restore launcher as administrator. |
| Close Echo VR completely | Exit the game before patching. |
| Cannot find DLL / missing second DLL | Select the actual installation containing both supported scripts. |
| Unsupported or modified DLL | The revision differs or another modification changed it; the patcher refuses to overwrite it. |
| Existing backup does not match | Preserve that backup and investigate the conflicting modification. |
| No spawning during play or after a goal | Expected in v3. Wait for an actual timeout or round over. |
| Unexpected behavior | Close Echo VR and run `RESTORE.cmd`; report the map/mode and round/timeout state. |
