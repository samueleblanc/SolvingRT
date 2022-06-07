import solvingrt.solve as srt

PATH_TO_VIDS = "/home/user/videos/training_videos/"

ath = srt.Athlete(185, 90, 0.3, 15, "left")
ex = srt.Exercise("Preacher curl", "biceps", PATH_TO_VIDS + "biceps/preacher_curl.mp4", ath, ["angles", "work"])

ex.video_resize(1280, 720)
ex.angle_with_gravity()

ex.play_video()
