[app]

title = THE_FX.TRADER BOT
package.name = thefxtraderbot
package.domain = org.thefxtrader

source.dir = .
source.include_exts = py,png,jpg,jpeg,wav,mp3

version = 1.0

requirements = python3,kivy,websocket-client

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,VIBRATE,WAKE_LOCK

android.api = 35
android.minapi = 23
android.archs = arm64-v8a

android.allow_backup = True
android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 0
