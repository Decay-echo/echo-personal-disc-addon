// Summon-button handling shared by DiscButton.dll and its test. Counts presses of one Touch
// button (X on the left controller by default; settings.ini [summon] button=) and hands
// them to the Personal Disc Everywhere patch: the summon block in the disc actor script
// (38965d90a823f03f.dll). The patch accepts a press only when the personal disc is
// allowed, so pressing it in live play does nothing. Every other button, A included, is
// left to Echo as it always was.
#pragma once
#include <windows.h>
#include <cstdint>

namespace discbutton {

constexpr uint64_t kSummonMagic = 0x4E4F5454554B5344ull;  // round_guard.c Summon.magic
constexpr uint64_t kSummonVersion = 1;
constexpr unsigned kButtonA = 0x00000001, kButtonB = 0x00000002;   // ovrButton_*: right controller
constexpr unsigned kButtonX = 0x00000100, kButtonY = 0x00000200;   // left controller
constexpr unsigned kLeftTouch = 0x00000001, kRightTouch = 0x00000002;  // ovrControllerType_*; both set in Touch and Active
constexpr ULONGLONG kDebounceMs = 200;
constexpr const wchar_t* kDiscScript = L"38965d90a823f03f.dll";

struct Summon {
    uint64_t magic, version;
    volatile uint64_t presses;
    uint64_t consumed;  // written by the patch only
    volatile uint64_t pressTick;
};

// ovrInputState (OVR_CAPI.h): only the leading fields are used.
struct InputState {
    double timeInSeconds;
    unsigned buttons;
    unsigned touches;
};

struct State {
    unsigned button = kButtonX;   // the summon button
    unsigned hand = kLeftTouch;   // the controller it is on
    bool hideFromEcho = false;    // remove it from what Echo sees
    bool previousDown = false;
    ULONGLONG lastPress = 0;
    HMODULE discModule = nullptr;
    Summon* summon = nullptr;
    HANDLE arcadeEvent = nullptr;  // Echo Arcade's FREEZE event, once it exists
    ULONGLONG arcadeLookedAt = 0;
};

// Echo Arcade's FREEZE: while this event is set the Touch controllers play RetroArch, so A
// must neither summon the disc nor be hidden (the arcade needs it). Same name as
// arcade::CONTROLLER_EVENT in echo-arcade's native/shared/arcade_ipc.h.
constexpr const wchar_t* kArcadeControllerEvent = L"Local\\EchoArcade.ControllerMode";

// settings.ini button= name: A or B (right controller), X or Y (left), or OFF (no summon
// button: every button is Echo's). False if unknown.
inline bool setButton(State& s, const wchar_t* name) {
    if (name && _wcsicmp(name, L"OFF") == 0) { s.button = 0; s.hand = 0; return true; }
    wchar_t c = name && name[0] && !name[1] ? wchar_t(name[0] & ~0x20) : 0;  // one letter, any case
    switch (c) {
        case L'A': s.button = kButtonA; s.hand = kRightTouch; return true;
        case L'B': s.button = kButtonB; s.hand = kRightTouch; return true;
        case L'X': s.button = kButtonX; s.hand = kLeftTouch; return true;
        case L'Y': s.button = kButtonY; s.hand = kLeftTouch; return true;
        default: return false;
    }
}

inline const wchar_t* buttonName(const State& s) {
    return s.button == kButtonA ? L"A" : s.button == kButtonB ? L"B" : s.button == kButtonX ? L"X" : s.button == kButtonY ? L"Y" : L"OFF";
}

inline bool arcadeHasControllers(State& s, ULONGLONG nowMs) {
    if (!s.arcadeEvent && (s.arcadeLookedAt == 0 || nowMs - s.arcadeLookedAt >= 2000)) {
        s.arcadeLookedAt = nowMs;  // not created yet (no arcade, or never switched on): look again later
        s.arcadeEvent = OpenEventW(SYNCHRONIZE, FALSE, kArcadeControllerEvent);
    }
    return s.arcadeEvent && WaitForSingleObject(s.arcadeEvent, 0) == WAIT_OBJECT_0;
}

// The patch's summon block lives in a writable section appended to the script DLL.
inline Summon* scanForSummon(HMODULE module) {
    auto* base = reinterpret_cast<unsigned char*>(module);
    auto* dos = reinterpret_cast<IMAGE_DOS_HEADER*>(base);
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) return nullptr;
    auto* nt = reinterpret_cast<IMAGE_NT_HEADERS64*>(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return nullptr;
    IMAGE_SECTION_HEADER* section = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++, section++) {
        if (!(section->Characteristics & IMAGE_SCN_MEM_WRITE)) continue;
        unsigned char* start = base + section->VirtualAddress;
        DWORD size = section->Misc.VirtualSize;
        for (DWORD at = 0; at + sizeof(Summon) <= size; at += 8) {
            auto* candidate = reinterpret_cast<Summon*>(start + at);
            if (candidate->magic == kSummonMagic && candidate->version == kSummonVersion) return candidate;
        }
    }
    return nullptr;
}

inline Summon* findSummon(State& s) {
    HMODULE module = GetModuleHandleW(kDiscScript);
    if (module != s.discModule) {
        s.discModule = module;
        s.summon = module ? scanForSummon(module) : nullptr;
    }
    return s.summon;
}

enum class Press { None, Debounced, NoScript, Sent };

inline Press onPress(State& s, ULONGLONG nowMs) {
    if (s.lastPress && nowMs - s.lastPress < kDebounceMs) return Press::Debounced;
    s.lastPress = nowMs;
    Summon* summon = findSummon(s);
    if (!summon) return Press::NoScript;
    // Same tick source the patch reads (KUSER_SHARED_DATA TickCountQuad), so it can
    // drop presses that waited too long. The increment publishes the tick.
    summon->pressTick = *reinterpret_cast<volatile uint64_t*>(0x7FFE0320ull);
    InterlockedIncrement64(reinterpret_cast<volatile LONG64*>(&summon->presses));
    return Press::Sent;
}

// Called after the runtime filled the state. Returns the press outcome for logging.
inline Press processInput(State& s, unsigned controllerType, InputState* input, ULONGLONG nowMs) {
    if (!input || !s.button || !(controllerType & s.hand)) return Press::None;
    if (arcadeHasControllers(s, nowMs)) {  // FREEZE: hands off, and a press still held doesn't count afterwards
        s.previousDown = true;
        return Press::None;
    }
    bool down = (input->buttons & s.button) != 0;
    Press result = Press::None;
    if (down && !s.previousDown) result = onPress(s, nowMs);
    s.previousDown = down;
    if (s.hideFromEcho) input->buttons &= ~s.button;
    return result;
}

}  // namespace discbutton
