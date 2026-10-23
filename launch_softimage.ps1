# Starts Blender with the Softimage Workflow Kit loaded from this folder and the Softimage workspace built. Nothing is installed.
# Usage:  powershell -File launch_softimage.ps1
#         powershell -File launch_softimage.ps1 -Blender "C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
#         powershell -File launch_softimage.ps1 -Factory      (Blender's factory settings instead of your own)
param([string]$Blender = "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe", [switch]$Factory)
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path $Blender)) { "Blender not found at $Blender. Pass -Blender <path to blender.exe>."; exit 1 }
$args = @()
if ($Factory) { $args += "--factory-startup" }
$args += "--python"; $args += "`"$root\launch_softimage.py`""
Start-Process $Blender -ArgumentList $args
"Started Blender. The Softimage workspace is built a couple of seconds after it opens (its tab is called Softimage)."
