from loguru import logger
import numpy as np
from csv import DictWriter
import pandas as pd

from tracks_import import read_from_csv


def cut_in_extraction(tracks, cut_in_events):

    cut_in_events_meta = cut_in_events
    for track in tracks:
        # find candidates that was both rear car and left-rear car
        rear_list = np.unique(np.array(track['rearId']))
        left_rear_list = np.unique(np.array(track['leftRearId']))
        for candidate_id in np.intersect1d(rear_list, left_rear_list):
            # emit -1 value
            if not candidate_id == -1:
                potential_track = tracks[candidate_id]

                # find the last point of ego car where the candidate was left-rear car
                left_rear_point_id_list = np.where(track['leftRearId'] == candidate_id)
                max_left_rear_point_id = max(left_rear_point_id_list[0])

                # find the first point of ego car where the candidate became rear car
                rear_point_id_list = np.where(track['rearId'] == candidate_id)
                min_rear_point_id = min(rear_point_id_list[0])

                # a = tracks[candidate_id]['leadTTC'][min_rear_point_id:]

                # make sure the candidate turns from left-rear to rear (ego car changes lane)
                # make sure the candidate did not change its lane
                if not sum(potential_track['laneChange']) and min_rear_point_id > max_left_rear_point_id:
                    # find the time frame where ego car change lane
                    time_change_lane = track['frame'][min_rear_point_id]

                    # find the point of candidate where ego car change lane
                    min_candidate_point_id = np.where(tracks[candidate_id]['frame'] == time_change_lane)
                    ttc_list = list(tracks[candidate_id]['leadTTC'][min_candidate_point_id[0][0]:])
                    ttc_list = list(filter(is_positive, ttc_list))
                    if len(ttc_list) > 0:
                        min_ttc = min(ttc_list)
                    else:
                        min_ttc = -1

                    # save meta info. of cut-in events: cut-in track id, rear track id, minimal TTC
                    cut_in_events_meta.append({'LCId': track['trackId'],
                                               'rearID': candidate_id,
                                               'ttc': min_ttc,
                                               'LCLanelet': list(filter(is_positive, np.unique(track['laneletId']))),
                                               'rearLanelet': list(filter(is_positive, np.unique(tracks[candidate_id]['laneletId'])))}
                                              )

    return cut_in_events_meta


def save_event_meta(data):

    fileds_names = ('LCId', 'rearID', 'ttc', 'LCLanelet', 'rearLanelet')
    with open('../output/event_meta.csv', 'w', encoding='utf-8', newline='') as outfile:
        writer = DictWriter(outfile, fileds_names)
        writer.writeheader()
        writer.writerows(data)


def is_positive(n):
    if n > 0:
        return True
    else:
        return False


def main():

    dataset_dir = "D:/OneDrive - tongji.edu.cn/Desktop/Study/4_Material/1_Dataset/7_exiD-dataset-v2.0/exiD-dataset-v2" \
                  ".0/data" + "/"
    cut_in_events = []

    for i in range(93):

        recording = str(i)

        recording = "{:02d}".format(int(recording))

        logger.info("Loading recording {} from dataset {}", recording, "exid")

        # Create paths to csv files
        tracks_file = dataset_dir + recording + "_tracks.csv"
        tracks_meta_file = dataset_dir + recording + "_tracksMeta.csv"
        recording_meta_file = dataset_dir + recording + "_recordingMeta.csv"

        # Load csv files
        logger.info("Loading csv files {}, {} and {}", tracks_file, tracks_meta_file, recording_meta_file)
        tracks, static_info, meta_info = read_from_csv(tracks_file, tracks_meta_file, recording_meta_file,
                                                       include_px_coordinates=True)
        # Get cut-in events
        cut_in_events = cut_in_extraction(tracks, cut_in_events)
    save_event_meta(cut_in_events)


if __name__ == '__main__':
    main()
