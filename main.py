import multiprocessing
import sys
import os
import wave
from multiprocessing import Process
from multiprocessing import Value
from PyQt6.QtWidgets import QApplication
import interface
import numpy as np
import cv2
import pyautogui
import pyaudio
from PyQt6 import QtWidgets
import time
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.VideoFileClip import AudioFileClip


# Define class of application
class RecordingApp(QtWidgets.QMainWindow, interface.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.textEdit.setText('Установите время записи')
        self.pushButton.clicked.connect(self.recording)
        self.pushButton_2.clicked.connect(self.get_text)
        self.video_process = RecordingVideo()
        self.audio_process = RecordingAudio()


# Sending values from lineEdit widgets to processes
    def get_text(self):
        try:
            self.video_process.minutes.value = int(self.lineEdit.text())
            self.audio_process.minutes.value = int(self.lineEdit.text())
            self.textEdit.setText('Время записи утановлено! \nНажмите на кнопку старт')
        except Exception:
            self.textEdit.setText('Введено не верное значение')

# merging two files
    def concatination(self):
        self.textEdit.append('Идет подготовка выходного файла, подождите! \n')
        QApplication.processEvents()
        # Define the paths of the audio and video files
        audio_path = "output.wav"
        video_path = "output.avi"

        # Create instances of VideoFileClip and AudioFileClip
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)

        # Merge the audio and video clips
        video_clip_with_audio = video_clip.set_audio(audio_clip)

        # Write the merged video file to a new file
        video_clip_with_audio.write_videofile("merged.mp4")
        self.textEdit.append('Выходной файл готов! \n')

# removing separate files
    def remove_files(self):
        self.textEdit.append('Удаление временных файлов \n')
        QApplication.processEvents()
        os.remove("output.wav")
        os.remove("output.avi")
        self.textEdit.append('Все готово! \n')

# Starting processes
    def recording(self):
        self.textEdit.setText('Идет запись \n')
        QApplication.processEvents()
        time.sleep(1)
        self.textEdit.show()
        self.video_process.start()
        self.audio_process.start()
        self.video_process.join()
        self.audio_process.join()
        self.textEdit.append('Запись завершена \n')
        self.concatination()
        self.remove_files()


# Extending Process class to video recording in separate process
class RecordingVideo(Process):
    def __init__(self):
        Process.__init__(self)
        self.minutes = Value('i', 0)


# Overriding run() function
    def run(self) -> None:
        start = time.time()
        seconds = self.minutes
        screen_size = (1920, 1080)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')

        out = cv2.VideoWriter('output.avi', fourcc, 20.0, screen_size)
        while True:
            current_time = time.time()
            elapsed_time = current_time - start
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            out.write(frame)
            #cv2.imshow('live', frame)
            if elapsed_time > (seconds.value*60) or cv2.waitKey(1) == ord('q'):
                break
        #cv2.destroyWindow('live')
        out.release()


# Extending Process() class to audio recording in separate process
class RecordingAudio(Process):
    def __init__(self):
        Process.__init__(self)
        self.minutes = Value('i', 0)

# Overriding run() function
    def run(self) -> None:
        p = pyaudio.PyAudio()
        print("Доступные устройства:\n")
        for i in range(0, p.get_device_count()):
            info = p.get_device_info_by_index(i)
            print(str(info["index"]) + ": \t %s \n \t %s \n" % (
                info["name"].encode('CP1251').decode('UTF-8'), p.get_host_api_info_by_index(info["hostApi"])["name"]))

        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = 44100
        RECORD_SECONDS = self.minutes.value * 60
        WAVE_OUTPUT_FILENAME = "output.wav"

        SPEAKERS = p.get_default_output_device_info()["hostApi"]
        print(SPEAKERS)  # The modified part

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                        input_device_index=0)

        print("* recording")

        frames = []
        for i in range(0, int(RATE / CHUNK * float(RECORD_SECONDS)) + 1):
            data = stream.read(CHUNK)
            frames.append(data)

        print("* done recording")

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = RecordingApp()
    window.show()
    app.exec()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
