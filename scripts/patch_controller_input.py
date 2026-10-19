import sys
import pathlib, plistlib, re
root=pathlib.Path(sys.argv[1]).resolve()
# Bounded, transition-only diagnostics distinguish keyboard duplicates from
# controller mapping errors on the real iPad without logging every frame.
p=root/'game/Monocle/MInput.cs'
s=p.read_text()
anchor='\t\tpublic void Update()\n\t\t{\n\t\t\tPreviousState = CurrentState;\n\t\t\tCurrentState = GamePad.GetState(PlayerIndex);'
if '[Input] pad=' not in s:
    s=s.replace('\t\tprivate float rumbleStrength;', '\t\tprivate int inputLogMask;\n\t\tprivate int inputLogCount;\n\n\t\tprivate float rumbleStrength;')
    assert anchor in s
    s=s.replace(anchor,anchor+'''
            int mask = (CurrentState.IsButtonDown(Buttons.A) ? 1 : 0)
                | (CurrentState.IsButtonDown(Buttons.B) ? 2 : 0)
                | (CurrentState.IsButtonDown(Buttons.Start) ? 4 : 0)
                | (CurrentState.IsButtonDown(Buttons.Back) ? 8 : 0)
                | (Keyboard.CurrentState.IsKeyDown(Keys.Enter) ? 16 : 0)
                | (Keyboard.CurrentState.IsKeyDown(Keys.Escape) ? 32 : 0);
            if (mask != inputLogMask && inputLogCount < 80)
            {
                Console.WriteLine("[Input] pad=" + PlayerIndex + " A/B/Start/Back/Enter/Escape mask=" + mask);
                inputLogCount++;
            }
            inputLogMask = mask;''')
    p.write_text(s)
print('Installed bounded controller input diagnostics')
