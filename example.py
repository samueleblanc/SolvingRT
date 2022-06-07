"""
    Simple example on how to use SolvingRT !
"""

import solvingrt.solve as srt

PATH_TO_VIDS = "/home/user/videos/training_videos/"

ath = srt.Athlete(height_meter=1.85, body_weight_kg=90, moving_limb_meter=0.3, weight_used_kg=15, side_seen="left")
ex = srt.Exercise(exercise_name="Preacher curl", muscle="biceps", path_to_video=PATH_TO_VIDS + "biceps/preacher_curl.mp4", 
                  athlete=ath, measures=["angles", "work"])

ex.video_resize(1280, 720)
ex.angle_with_gravity()

ex.play_video()
