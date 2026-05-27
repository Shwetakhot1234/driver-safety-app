[app]

title = Driver Safety App
package.name = driversafety
package.domain = org.shweta

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,tflite,task,onnx,json

version = 1.0

requirements = python3==3.10.11,kivy==2.2.1,kivymd==1.1.1,numpy==1.24.4,pillow,plyer,fpdf2,opencv-python

orientation = portrait

fullscreen = 0

android.permissions = CAMERA,INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,RECORD_AUDIO

android.api = 33
android.minapi = 24
android.ndk = 23b

android.accept_sdk_license = True

p4a.branch = master

[buildozer]

log_level = 2
warn_on_root = 1
