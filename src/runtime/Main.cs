using System;
using System.IO;
using Foundation;
using ObjCRuntime;
using SDL2;
using System.Runtime.InteropServices;

namespace CelesteiPadOS;

public static class Program
{
    static readonly SDL.SDL_main_func MainCallback = Run;
    [DllImport("__Internal")]
    static extern int CelesteInstallUIKitInputFix();
    [DllImport("__Internal")]
    static extern int CelesteNativeSettingsFlags();
    [DllImport("__Internal")]
    static extern void CelesteConfigureNativeLogging(string path);
    [DllImport("__Internal")]
    static extern void CelesteShowLaunchNotice();

    static void Main(string[] args)
    {
        var logs = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "Celeste");
        Directory.CreateDirectory(logs);
        int flags = CelesteNativeSettingsFlags(); // Configure Metal before creating a device.
        CelesteConfigureNativeLogging(Path.Combine(logs, "native.log"));
        TextWriter output = TextWriter.Null;
        if ((flags & 1) != 0)
            output = TextWriter.Synchronized(new StreamWriter(Path.Combine(logs, "runtime.log"), append:false) { AutoFlush = true });
        Console.SetOut(output);
        Console.SetError(output);
        AppDomain.CurrentDomain.UnhandledException += (_, e) => RecordFailure(e.ExceptionObject);
        Console.WriteLine("Celeste iPadOS: ARM64 AOT / Metal / FMOD 1.10");
        Console.WriteLine("Build 8 (original 16:9): settings flags=" + flags + "; UIKit controller keyboard duplicate filter: " +
            (CelesteInstallUIKitInputFix() != 0 ? "installed" : "FAILED"));
        Directory.SetCurrentDirectory(NSBundle.MainBundle.BundlePath);
        Environment.SetEnvironmentVariable("FNA_GRAPHICS_ENABLE_HIGHDPI", "1");
        Environment.SetEnvironmentVariable("FNA3D_FORCE_DRIVER", "Metal");
        Environment.SetEnvironmentVariable("FNA_AUDIO_DISABLE_SOUND", "1");
        SDL.SDL_SetHint("FNA3D_FORCE_DRIVER", "Metal");
        SDL.SDL_SetHint(SDL.SDL_HINT_MOUSE_TOUCH_EVENTS, "0");
        SDL.SDL_SetHint(SDL.SDL_HINT_TOUCH_MOUSE_EVENTS, "0");
        SDL.SDL_UIKitRunApp(0, IntPtr.Zero, MainCallback);
    }

    [MonoPInvokeCallback(typeof(SDL.SDL_main_func))]
    static int Run(int argc, IntPtr argv)
    {
        try
        {
            CelesteShowLaunchNotice();
            global::Celeste.Celeste.Main(new[] {"--graphics", "Metal", "--default-language", "schinese"});
            return 0;
        }
        catch (Exception ex)
        {
            RecordFailure(ex);
            return 1;
        }
    }

    static void RecordFailure(object error)
    {
        Console.WriteLine(error);
        // Keep errors even when normal diagnostic logs are turned off.
        try { Monocle.ErrorLog.Write(error?.ToString() ?? "Unknown native entry failure"); }
        catch { }
    }
}
