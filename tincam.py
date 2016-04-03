from dropbox import Dropbox
from picamera import PiCamera as Camera
from gpiozero import Button
from datetime import datetime
import os
import time
import threading

button = Button(4)
camera = Camera()

upload_queue = []
queue_lock = threading.Lock()

DBX_API_KEY = 'YOUR_DROPBOX_API_KEY_HERE'
dbx = Dropbox(DBX_API_KEY)

def wait_for_press():
	raw_input('press: ')


def wait_for_release():
	raw_input('release: ')


def main():
	upload_thread = threading.Thread(target=upload_worker)
	connect_thread = threading.Thread(target=dropbox_connect_worker)

	upload_thread.start()
	connect_thread.start()

	while True:
		print('Press for photo capture stream')
		print('Hold and release for video')

		button.wait_for_press()
		startTime = time.time()

		button.wait_for_release()
		elapsedTime = time.time() - startTime

		if elapsedTime > 1:
			print('Video capture started, press to halt')
			process_video_capture()
		else:
			print('Photo stream started, press to halt')
			process_photo_stream()

	upload_thread.stop()


def dropbox_connect_worker():
	dropbox_connected = False
	while dropbox_connected is False:
		try:
			print('Attempting Dropbox connection...')
			dbx.users_get_current_account()
			dropbox_connected = True

			print('Dropbox connected')
		except:
			print('Dropbox failed to connect, retrying...')
			time.sleep(3)


def upload_worker():
	while True:
		if not upload_queue:
			time.sleep(2)
			continue

		target_filename = None
		with queue_lock:
			target_filename = upload_queue[0]

		print('Attempting to upload ' + target_filename)
		target_file = open(target_filename, 'r')

		try:
			dbx.files_upload(target_file, '/' + target_filename)
			with queue_lock:
				upload_queue.pop(0)
				try:
					os.remove(target_filename)
				except:
					pass

			print('Upload successful')
		except:
			print('Upload failed, will retry later.')

		time.sleep(2)


def get_timestamp():
	return datetime.now().isoformat()


def get_filename(extension):
	return get_timestamp() + '.' + extension


def process_video_capture():
	camera.resolution = (640, 480)

	filename = get_filename('h264')
	camera.start_recording(filename)
	button.wait_for_press()
	camera.stop_recording()
	button.wait_for_release()

	with queue_lock:
		upload_queue.append(filename)

	print('Video captured to ' + filename)


def process_photo_stream():
	camera.resolution = (1280, 1024)
	capture_enabled = True

	while capture_enabled:
		filename = get_filename('jpg')
		camera.capture(filename)

		with queue_lock:
			upload_queue.append(filename)

		print('Photo captured to ' + filename)
		time.sleep(1)

		if button.is_pressed:
			capture_enabled = False
			button.wait_for_release()

if __name__ == "__main__":
	main()
