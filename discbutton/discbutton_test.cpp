// Tests DiscButton's summon-button handling (X by default) against a patched disc script DLL.
// Usage: discbutton_test.exe <folder containing the patched 38965d90a823f03f.dll>
#include "discbutton_core.h"
#include "minhook/include/MinHook.h"
#include <cstdio>
#include <string>

using namespace discbutton;

static int failures = 0, checks = 0;
static void check(const char* label, bool ok) {
    checks++;
    if (!ok) failures++;
    printf("%s %s\n", ok ? "PASS" : "FAIL", label);
}

// Stand-in for the runtime's ovr_GetInputState, hooked the same way as the plugin.
static unsigned fakeButtons = 0;
static __declspec(noinline) int __cdecl fakeGetInputState(void*, unsigned, InputState* input) {
    input->timeInSeconds = 1.0;
    input->buttons = fakeButtons;
    input->touches = 0;
    return 0;
}
using GetInputStateFn = int(__cdecl*)(void*, unsigned, InputState*);
static GetInputStateFn realGetInputState = nullptr;
static State hooked;
static ULONGLONG hookedNow = 1000;
static int __cdecl detour(void* session, unsigned type, InputState* input) {
    int r = realGetInputState(session, type, input);
    if (r >= 0) processInput(hooked, type, input, hookedNow);
    return r;
}

int wmain(int argc, wchar_t** argv) {
    if (argc < 2) { printf("usage: discbutton_test <folder with patched 38965d90a823f03f.dll>\n"); return 2; }
    InputState in{};
    State s;

    in.buttons = kButtonX;
    check("no disc script loaded: press reported as NoScript", processInput(s, 3, &in, 1000) == Press::NoScript);
    State names;
    check("settings names: A/B right, X/y left, unknown refused",
          setButton(names, L"A") && names.button == kButtonA && names.hand == kRightTouch && setButton(names, L"y") &&
              names.button == kButtonY && names.hand == kLeftTouch && !setButton(names, L"Q") && !setButton(names, L"XX"));
    State off;
    InputState offIn{};
    offIn.buttons = kButtonX | kButtonA;
    check("button=OFF: nothing summons and nothing is hidden",
          setButton(off, L"off") && off.button == 0 && processInput(off, 3, &offIn, 1000) == Press::None &&
              offIn.buttons == (kButtonX | kButtonA) && std::wcscmp(buttonName(off), L"OFF") == 0);

    std::wstring dll = std::wstring(argv[1]) + L"\\38965d90a823f03f.dll";
    HMODULE module = LoadLibraryExW(dll.c_str(), nullptr, DONT_RESOLVE_DLL_REFERENCES);
    if (!module) { printf("cannot load %ls (error %lu)\n", dll.c_str(), GetLastError()); return 2; }
    s = State{};
    Summon* summon = findSummon(s);
    check("finds the summon block in the patched disc script", summon && summon->magic == kSummonMagic);
    if (!summon) return 1;
    check("summon block starts with no presses", summon->presses == 0);

    ULONGLONG now = 5000;
    in.buttons = kButtonA;
    check("A does nothing now: it's Echo's again", processInput(s, 3, &in, now - 1000) == Press::None && summon->presses == 0 &&
                                                      in.buttons == kButtonA);
    in.buttons = 0;
    processInput(s, 3, &in, now - 900);
    in.buttons = kButtonX;
    check("X down on Touch (3): press sent", processInput(s, 3, &in, now) == Press::Sent && summon->presses == 1);
    uint64_t tick = *reinterpret_cast<volatile uint64_t*>(0x7FFE0320ull);
    check("press tick is the current tick", summon->pressTick <= tick && tick - summon->pressTick < 4);
    check("X still held next frame: no repeat", processInput(s, 3, &in, now + 11) == Press::None && summon->presses == 1);
    in.buttons = 0;
    processInput(s, 3, &in, now + 22);
    in.buttons = kButtonX;
    check("quick re-press within 200 ms is debounced", processInput(s, 3, &in, now + 100) == Press::Debounced && summon->presses == 1);
    in.buttons = 0;
    processInput(s, 3, &in, now + 150);
    in.buttons = kButtonX;
    check("press after 200 ms counts", processInput(s, 3, &in, now + 400) == Press::Sent && summon->presses == 2);
    in.buttons = 0;
    processInput(s, 3, &in, now + 500);

    in.buttons = kButtonX;
    check("right controller only (2) is ignored for X", processInput(s, 2, &in, now + 1000) == Press::None && summon->presses == 2);
    in.buttons = kButtonX;
    check("Xbox controller (0x10) is ignored", processInput(s, 0x10, &in, now + 1300) == Press::None && summon->presses == 2);
    in.buttons = kButtonX;
    check("left controller (1) counts", processInput(s, 1, &in, now + 1600) == Press::Sent && summon->presses == 3);
    in.buttons = 0;
    processInput(s, 1, &in, now + 1700);
    in.buttons = kButtonX;
    check("Active (0xFFFFFFFF) counts", processInput(s, 0xFFFFFFFFu, &in, now + 2000) == Press::Sent && summon->presses == 4);
    in.buttons = 0;
    processInput(s, 1, &in, now + 2100);

    in.buttons = kButtonA | kButtonB | kButtonX;
    processInput(s, 3, &in, now + 2500);
    check("hide_from_echo=0: Echo still sees every button", in.buttons == (kButtonA | kButtonB | kButtonX));
    in.buttons = 0;
    processInput(s, 3, &in, now + 2600);
    s.hideFromEcho = true;
    in.buttons = kButtonA | kButtonB | kButtonX;
    processInput(s, 3, &in, now + 3000);
    check("hide_from_echo=1: X removed, A and B kept", in.buttons == (kButtonA | kButtonB) && summon->presses == 6);

    // Echo Arcade's FREEZE: while its event is set, A is left alone (no summon, not hidden).
    in.buttons = 0;
    processInput(s, 3, &in, now + 3300);
    HANDLE freeze = CreateEventW(nullptr, TRUE, TRUE, kArcadeControllerEvent);
    s.arcadeLookedAt = 0;  // look for the event now
    in.buttons = kButtonX | kButtonB;
    check("FREEZE on: X doesn't summon", processInput(s, 3, &in, now + 3600) == Press::None && summon->presses == 6);
    check("FREEZE on: X isn't hidden (the arcade plays it)", in.buttons == (kButtonX | kButtonB));
    ResetEvent(freeze);
    check("FREEZE off with X still held: no summon", processInput(s, 3, &in, now + 3900) == Press::None && summon->presses == 6);
    in.buttons = 0;
    processInput(s, 3, &in, now + 4000);
    in.buttons = kButtonX;
    check("FREEZE off: X summons again", processInput(s, 3, &in, now + 4300) == Press::Sent && summon->presses == 7);
    CloseHandle(freeze);
    in.buttons = 0;
    processInput(s, 3, &in, now + 4400);

    // The same MinHook detour the plugin installs, on a stand-in function.
    MH_STATUS st = MH_Initialize();
    if (st == MH_OK) st = MH_CreateHook(reinterpret_cast<void*>(&fakeGetInputState), reinterpret_cast<void*>(&detour),
                                        reinterpret_cast<void**>(&realGetInputState));
    if (st == MH_OK) st = MH_EnableHook(reinterpret_cast<void*>(&fakeGetInputState));
    check("MinHook installs the detour", st == MH_OK);
    auto volatile call = &fakeGetInputState;
    uint64_t before = summon->presses;
    fakeButtons = kButtonX;
    InputState out{};
    int r = call(nullptr, 3, &out);
    check("hooked call returns the runtime's result and buttons", r == 0 && out.buttons == kButtonX);
    check("hooked call sends the press", summon->presses == before + 1);
    MH_DisableHook(MH_ALL_HOOKS);
    MH_Uninitialize();

    printf("\n%d/%d passed\n", checks - failures, checks);
    return failures ? 1 : 0;
}
