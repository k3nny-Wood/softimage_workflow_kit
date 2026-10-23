# Starts Blender with tests/live_panels.py, which builds the Softimage workspace, then clicks some panel buttons with the real mouse.
# Usage: powershell -File tests\live_panels.ps1 [-Blender "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"]
param([string]$Blender = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
$root = Split-Path -Parent $PSScriptRoot
Remove-Item "$root\tests\live_panels_result.txt", "$root\tests\live_panels_points.json", "$root\tests\live_panels_marker.txt" -ErrorAction SilentlyContinue
Add-Type @"
using System; using System.Runtime.InteropServices;
public class In2 {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, int dx, int dy, uint d, UIntPtr e);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [StructLayout(LayoutKind.Sequential)] public struct PT { public int x; public int y; }
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref PT p);
}
"@
$p = Start-Process $Blender -ArgumentList "--factory-startup", "--python", "`"$root\tests\live_panels.py`"" -PassThru
$p.Refresh()
for ($i = 0; $i -lt 90 -and -not (Test-Path "$root\tests\live_panels_points.json"); $i++) { Start-Sleep -Milliseconds 500 }
if (-not (Test-Path "$root\tests\live_panels_points.json")) { "the workspace was not built in time"; Stop-Process -Id $p.Id -Force; exit 1 }
Start-Sleep 1
$pts = Get-Content "$root\tests\live_panels_points.json" -Raw | ConvertFrom-Json
[In2]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
$origin = New-Object In2+PT; [In2]::ClientToScreen($p.MainWindowHandle, [ref]$origin) | Out-Null   # where the window's client area starts on the screen
function Click($name) {
  $pt = $pts.$name
  if ($null -eq $pt) { "no target: $name"; return }
  [In2]::SetCursorPos($origin.x + [int]$pt[0], $origin.y + [int]$pt[1]); Start-Sleep -Milliseconds 400
  [In2]::mouse_event(0x0001, 1, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 150   # a real mouse move first: Blender hovers the panel under it
  [In2]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 120
  [In2]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 700
}
Click "MCP:Local"
Click "Command line / playback:Auto"
Click "MCP:Prop"
Click "Timeline:ruler"
Set-Content "$root\tests\live_panels_marker.txt" "done" -NoNewline
if (-not $p.WaitForExit(30000)) { "timed out"; Stop-Process -Id $p.Id -Force }
Get-Content "$root\tests\live_panels_result.txt"
