#include <Windows.h>
#include <iostream>

typedef bool (*DeviceOpenFunc)();
typedef void (*DeviceCloseFunc)();
typedef void (*DelayFunc)(int ms);
typedef void (*KeyDownFunc)(int keyCode);
typedef void (*KeyUpFunc)(int keyCode);
typedef void (*MouseDownFunc)(int button);
typedef void (*MouseUpFunc)(int button);
typedef void (*MoveRFunc)(int dx, int dy, bool relative);
typedef void (*ScrollFunc)(int amount);

DeviceOpenFunc device_open;
DeviceCloseFunc device_close;
DelayFunc delay;
KeyDownFunc key_down;
KeyUpFunc key_up;
MouseDownFunc mouse_down;
MouseUpFunc mouse_up;
MoveRFunc moveR;
ScrollFunc scroll;

bool check_dll(HMODULE hDll) {
    if (!hDll) {
        DWORD error = GetLastError();
        std::cerr << "DLL is error: " << error << std::endl;
        return false;
    }

    device_open = (DeviceOpenFunc)GetProcAddress(hDll, "device_open");
    device_close = (DeviceCloseFunc)GetProcAddress(hDll, "device_close");
    delay = (DelayFunc)GetProcAddress(hDll, "delay");
    key_down = (KeyDownFunc)GetProcAddress(hDll, "key_down");
    key_up = (KeyUpFunc)GetProcAddress(hDll, "key_up");
    mouse_down = (MouseDownFunc)GetProcAddress(hDll, "mouse_down");
    mouse_up = (MouseUpFunc)GetProcAddress(hDll, "mouse_up");
    moveR = (MoveRFunc)GetProcAddress(hDll, "moveR");
    scroll = (ScrollFunc)GetProcAddress(hDll, "scroll");

    if (!device_open || !device_close || !key_down || !key_up) {
        std::cerr << "dll is error!" << std::endl;
        FreeLibrary(hDll);
        return false;
    }

    #define CHECK_FUNC(func) if (!func) {std::cout << #func << " not found\n"; return false;}
    CHECK_FUNC(device_open);
    CHECK_FUNC(device_close);
    CHECK_FUNC(key_down);
    CHECK_FUNC(key_up);
    CHECK_FUNC(mouse_down);
    CHECK_FUNC(mouse_up);
    CHECK_FUNC(moveR);
    CHECK_FUNC(scroll);

    if (!device_open()) {
        std::cerr << "device_open failed" << std::endl;
        return false;
    }

    return true;
}
