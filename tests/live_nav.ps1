# Starts Blender with tests/live_nav.py and sends real input: S + left drag, S + middle drag, S + right drag, and S alone.
# Usage: powershell -File tests\live_nav.ps1 [-Blender "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"]
param([string]$Blender = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
$root = Split-Path -Parent $PSScriptRoot
Remove-Item "$root\tests\live_result.txt", "$root\tests\live_area.txt" -ErrorAction SilentlyContinue
Add-Type @"
using System; using System.Runtime.InteropServices;
public class In {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, int dx, int dy, uint d, UIntPtr e);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte sc, uint f, UIntPtr e);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
}
"@
$p = Start-Process $Blender -ArgumentList "--factory-startup", "--python", "`"$root\tests\live_nav.py`"" -PassThru
Start-Sleep 5
$p.Refresh(); [In]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
# the 3D view: from Blender's own report (window x, y, area x, y, w, h); the window's client origin is roughly its top-left
$info = $null; for ($i = 0; $i -lt 20 -and -not $info; $i++) { if (Test-Path "$root\tests\live_area.txt") { $info = (Get-Content "$root\tests\live_area.txt").Split(' ') } else { Start-Sleep -Milliseconds 300 } }
if (-not $info) { "no area report"; Stop-Process -Id $p.Id -Force; exit 1 }
$wx = [int]$info[0]; $wy = [int]$info[1]; $ax = [int]$info[2]; $ay = [int]$info[3]; $aw = [int]$info[4]; $ah = [int]$info[5]; $ww = [int]$info[6]; $wh = [int]$info[7]
$cx = $wx + $ax + [int]($aw / 2) + 60; $cy = $wy + ($wh - ($ay + [int]($ah / 2))) - 40   # (Blender's y runs upward from the bottom of the window; the offsets keep the point off the cube and the gizmos)
"3D view centre on screen: $cx $cy"
Start-Sleep 2   # (the 'before' sample is taken at 6 s)
function Drag($down, $up, $dx) {
  [In]::SetCursorPos($cx, $cy); Start-Sleep -Milliseconds 150
  [In]::keybd_event(0x53, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 200   # S down
  [In]::mouse_event($down, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 100
  for ($k = 1; $k -le 24; $k++) { [In]::mouse_event(0x0001, [int]($dx / 24), 1, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 30 }   # relative moves, like a real mouse (Blender grabs the cursor while it navigates)
  [In]::mouse_event($up, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 150
  [In]::keybd_event(0x53, 0, 2, [UIntPtr]::Zero); Start-Sleep -Milliseconds 300   # S up
}
function Mark($n) { Set-Content "$root\tests\live_marker.txt" $n -NoNewline; Start-Sleep -Milliseconds 700 }
Set-Content "$root\tests\live_marker.txt" "0" -NoNewline
Start-Sleep 3
Drag 0x0002 0x0004 60     # a warm-up: the splash screen takes the very first clicks
Mark 1
Drag 0x0002 0x0004 120    # S + left drag: orbit
Mark 2
Drag 0x0020 0x0040 100    # S + middle drag: pan
Mark 3
Drag 0x0008 0x0010 90     # S + right drag: dolly
Mark 4
[In]::keybd_event(0x53, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 200; [In]::keybd_event(0x53, 0, 2, [UIntPtr]::Zero)   # S alone
Mark 5
if (-not $p.WaitForExit(30000)) { "timed out"; Stop-Process -Id $p.Id -Force }
Get-Content "$root\tests\live_result.txt"