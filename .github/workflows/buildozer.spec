[app]
title = SaveUp
package.name = saveup
package.domain = org.saveup
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 1.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,sqlite3
orientation = portrait
fullscreen = 0
android.permissions = POST_NOTIFICATIONS,VIBRATE,WAKE_LOCK
android.api = 33
android.minapi = 24
android.accept_sdk_license = True
android.ndk = 25b
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1