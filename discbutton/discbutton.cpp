// DiscButton.dll -- EchoLoader plugin: the Oculus X button summons the personal disc.
//
// Hooks ovr_GetInputState in the Oculus runtime (LibOVRRT64_1.dll) and passes presses of
// the summon button to the Personal Disc Everywhere patch, which only accepts them while the
// personal disc is allowed (lobby, timeouts, and from a goal until the launcher countdown ends).
//
// Settings: plugins\DiscButton\settings.ini
//   [summon] button=X          A, B (right controller), X or Y (left), or OFF
//            hide_from_echo=0  1 = Echo no longer sees that button
// Re-read when the file changes (the arcade tablet's SETTINGS page writes it).
// Log: %LOCALAPPDATA%\DiscButton\discbutton.log
#include "discbutton_core.h"
#include "minhook/include/MinHook.h"
#include <cstdarg>
#include <cstdio>
#include <mutex>
#include <share.h>
#include <string>

namespace {

discbutton::State state;
std::mutex logLock;
FILE* logFile = nullptr;

void logf(const char* format, ...) {
    std::lock_guard<std::mutex> lock(logLock);
    if (!logFile) {
        wchar_t base[MAX_PATH];
        if (!GetEnvironmentVariableW(L"LOCALAPPDATA", base, MAX_PATH)) return;
        std::wstring dir = std::wstring(base) + L"\\DiscButton";
        CreateDirectoryW(dir.c_str(), nullptr);
        logFile = _wfsopen((dir + L"\\discbutton.log").c_str(), L"a", _SH_DENYNO);
        if (!logFile) return;
    }
    fprintf(logFile, "%llu ", GetTickCount64());
    va_list args;
    va_start(args, format);
    vfprintf(logFile, format, args);
    va_end(args);
    fputc('\n', logFile);
    fflush(logFile);
}

using GetInputStateFn = int(__cdecl*)(void* session, unsigned controllerType, discbutton::InputState* input);
GetInputStateFn realGetInputState = nullptr;

std::wstring settingsIni;
FILETIME settingsStamp{};
ULONGLONG settingsCheckedAt = 0;

FILETIME stampOf(const std::wstring& path) {
    WIN32_FILE_ATTRIBUTE_DATA a{};
    return GetFileAttributesExW(path.c_str(), GetFileExInfoStandard, &a) ? a.ftLastWriteTime : FILETIME{};
}

void readSettings() {
    wchar_t button[8] = L"X";
    GetPrivateProfileStringW(L"summon", L"button", L"X", button, 8, settingsIni.c_str());
    if (!discbutton::setButton(state, button)) discbutton::setButton(state, L"X");
    state.hideFromEcho = GetPrivateProfileIntW(L"summon", L"hide_from_echo", 0, settingsIni.c_str()) != 0;
    state.previousDown = true;  // a button already held doesn't count as a press
}

// Once a second, on the game's input thread: settings.ini changed? Read it again.
void watchSettings() {
    ULONGLONG now = GetTickCount64();
    if (now - settingsCheckedAt < 1000) return;
    settingsCheckedAt = now;
    FILETIME stamp = stampOf(settingsIni);
    if (CompareFileTime(&stamp, &settingsStamp) == 0) return;
    settingsStamp = stamp;
    readSettings();
    logf("settings.ini changed: button %ls, hide_from_echo=%d", discbutton::buttonName(state), state.hideFromEcho);
}

int __cdecl hookedGetInputState(void* session, unsigned controllerType, discbutton::InputState* input) {
    int result = realGetInputState(session, controllerType, input);
    watchSettings();
    if (result >= 0) {  // OVR_SUCCESS
        switch (discbutton::processInput(state, controllerType, input, GetTickCount64())) {
            case discbutton::Press::Sent:
                logf("summon button pressed: request %llu sent", state.summon->presses);
                break;
            case discbutton::Press::NoScript:
                logf("summon button pressed: personal disc script not loaded (or not patched)");
                break;
            default:
                break;
        }
    }
    return result;
}

DWORD WINAPI install(LPVOID pluginPath) {
    std::wstring dir = static_cast<const wchar_t*>(pluginPath);
    delete[] static_cast<wchar_t*>(pluginPath);
    dir.resize(dir.find_last_of(L"\\/"));
    settingsIni = dir + L"\\DiscButton\\settings.ini";
    settingsStamp = stampOf(settingsIni);
    readSettings();
    state.previousDown = false;
    logf("DiscButton starting (pid %lu): button %ls, hide_from_echo=%d", GetCurrentProcessId(), discbutton::buttonName(state),
         state.hideFromEcho);
    // The game loads the Oculus runtime shortly after start.
    HMODULE ovr = nullptr;
    for (int i = 0; i < 600 && !ovr; i++) {
        ovr = GetModuleHandleW(L"LibOVRRT64_1.dll");
        if (!ovr) Sleep(100);
    }
    void* target = ovr ? reinterpret_cast<void*>(GetProcAddress(ovr, "ovr_GetInputState")) : nullptr;
    if (!target) { logf("Oculus runtime (LibOVRRT64_1.dll) not found; summon button inactive"); return 0; }
    MH_STATUS init = MH_Initialize();
    MH_STATUS s = (init == MH_OK || init == MH_ERROR_ALREADY_INITIALIZED)
                      ? MH_CreateHook(target, reinterpret_cast<void*>(hookedGetInputState),
                                      reinterpret_cast<void**>(&realGetInputState))
                      : init;
    if (s == MH_OK) s = MH_EnableHook(target);
    logf("ovr_GetInputState hook %s", s == MH_OK ? "installed" : MH_StatusToString(s));
    return 0;
}

void start(HMODULE self) {
    static std::once_flag once;
    std::call_once(once, [self] {
        auto* path = new wchar_t[MAX_PATH];
        GetModuleFileNameW(self, path, MAX_PATH);
        // Hooking happens off the loader thread; it runs once the loader lock is released.
        HANDLE t = CreateThread(nullptr, 0, install, path, 0, nullptr);
        if (t) CloseHandle(t);
        else delete[] path;
    });
}

}  // namespace

// EchoLoader calls PluginInit only for entries with "args"; DllMain covers the rest.
extern "C" __declspec(dllexport) void PluginInit(const char*) {
    HMODULE self = nullptr;
    GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                       reinterpret_cast<LPCWSTR>(&PluginInit), &self);
    start(self);
}

BOOL WINAPI DllMain(HINSTANCE self, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(self);
        HMODULE pinned = nullptr;  // never unload while the hook points into us
        GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
                           reinterpret_cast<LPCWSTR>(&DllMain), &pinned);
        start(self);
    }
    return TRUE;
}
