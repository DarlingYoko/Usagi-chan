import os

os.chdir('files\\Downloads')
for file in os.listdir('..\\ffmpeg'):
    print(file)
