import solvingrt.solve as srt

PATH_TO_VIDS = "/home/samleb/Videos/Training videos/"

ath = srt.Athlete(185, 90, 0.3, 15, "left")
ex = srt.Exercise("Preacher curl", "biceps", PATH_TO_VIDS + "5- Biceps/Preacher curl.mp4", ath, ["angles", "work"])

ex.play_video()
