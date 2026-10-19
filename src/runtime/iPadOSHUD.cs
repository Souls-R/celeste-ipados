using System;
using System.Runtime.InteropServices;

namespace Celeste;

internal static class iPadOSHUD
{
    [DllImport("__Internal")]
    private static extern int CelesteApplyMetalHUDToWindow(IntPtr window);
    internal static bool Pending = true;
    private static int attempts;

    internal static void Apply()
    {
        int layers = CelesteApplyMetalHUDToWindow(Monocle.Engine.Instance.Window.Handle);
        Pending = layers == 0 && ++attempts < 30;
        Console.WriteLine("[HUD] renderer ready; configured Metal layers=" + layers);
    }
}
