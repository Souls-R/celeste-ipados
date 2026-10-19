#import <UIKit/UIKit.h>
#import <objc/runtime.h>
#include <stdio.h>

// SDL's legacy Siri Remote fallback also sees iPadOS controller UIPress events.
// These have no UIKey and must not become Enter/Escape/arrow keyboard events:
// GameController already delivers their complete state through SDL's MFi driver.
static int CelesteScancodeFromPress(id view, SEL selector, UIPress *press)
{
    UIKey *key = press.key;
    if (key != nil) {
        return (int)key.keyCode;
    }
    static unsigned logged;
    if (logged < 16) {
        ++logged;
        fprintf(stdout, "[Input] ignored controller UIKit keyboard duplicate type=%ld\n", (long)press.type);
        fflush(stdout);
    }
    return 0; // SDL_SCANCODE_UNKNOWN: ignored by SDL_SendKeyboardKey.
}

int CelesteInstallUIKitInputFix(void)
{
    Class view = objc_getClass("SDL_uikitview");
    Method method = class_getInstanceMethod(view, sel_registerName("scancodeFromPress:"));
    if (method == NULL) {
        return 0;
    }
    method_setImplementation(method, (IMP)CelesteScancodeFromPress);
    return 1;
}
