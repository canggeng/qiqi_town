from __future__ import annotations

from panda3d.core import Filename, loadPrcFileData

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name p3openal_audio")
loadPrcFileData("", "notify-level warning")

from direct.showbase.ShowBase import ShowBase  # noqa: E402

base = ShowBase()
print("sfx managers:", len(base.sfxManagerList), flush=True)
path = Filename.fromOsSpecific("src/qiqi_town/assets/audio/click.wav").getFullpath()
sound = base.loader.loadSfx(path)
print("sound:", sound, flush=True)
if sound is not None:
    sound.setVolume(0.5)
    sound.play()
    print("playing", flush=True)
base.graphicsEngine.renderFrame()
base.destroy()
