/* SDL2-CS exposes desktop/Android APIs on every target. These entry points
 * cannot perform platform work on iOS and return platform-neutral defaults.
 */
#include <stddef.h>
void SDL_SetWindowsMessageHook(void *callback, void *userdata) {}
void *SDL_AndroidGetJNIEnv(void) { return NULL; }
void *SDL_AndroidGetActivity(void) { return NULL; }
int SDL_GetAndroidSDKVersion(void) { return 0; }
int SDL_IsAndroidTV(void) { return 0; }
int SDL_IsChromebook(void) { return 0; }
int SDL_IsDeXMode(void) { return 0; }
void SDL_AndroidBackButton(void) {}
const char *SDL_AndroidGetInternalStoragePath(void) { return NULL; }
int SDL_AndroidGetExternalStorageState(void) { return 0; }
const char *SDL_AndroidGetExternalStoragePath(void) { return NULL; }
int SDL_AndroidRequestPermission(const char *permission) { return 0; }
int SDL_WinRTGetDeviceFamily(void) { return 0; }
int SDL_WinRTRunApp(void *main_function, void *reserved) { return 0; }
