# Round guard payload

`round_guard.c` is the freestanding x64 source embedded by the standalone installer. It has no imported libraries or DLL entry point. It uses the game's existing expression getters and event dispatcher. The installer appends separate executable/read-only/writable sections, merges the unwind table, and redirects the supported call sites; existing game code remains available to the wrappers.

The shipped payload was compiled using MSVC 14.51.36231 with:

```bat
cl /nologo /O2 /GS- /Zl /TC /c round_guard.c /Fo:round_guard.obj
link /nologo /DLL /NOENTRY /NODEFAULTLIB /FIXED /DYNAMICBASE:NO /OUT:round_guard.dll round_guard.obj
```

Run these in an x64 Visual Studio developer command prompt. The result is a payload for the patch builder, **not** a replacement for either game DLL. Rebuilding alone does not update the installer's embedded payload, expected hashes, or restoration metadata. Those must be regenerated and the native-code and installer checks repeated before distributing a changed patch.

`configuration` is populated separately for each target DLL. The allowlist distinguishes pre/post-round states and actual `PAUSED` timeouts from round stoppages such as goals. The persistent controller watcher dispatches normal enable/disable events only when availability changes. The actor wrapper checks `is_local_disc` before changing personal-disc respawn behavior.

The v3.0.1 builder places the first appended section immediately after the original image, subtracting the payload first-section RVA from the image shift. v3.0.0 left a 4096-byte gap, which Windows rejects with ERROR_BAD_EXE_FORMAT (193). Regression checks use LoadLibraryExW with DONT_RESOLVE_DLL_REFERENCES to validate image mapping without running game entry points.
