from re import search
from tdt import read_block
import pandas as pd
import os

# info -----------------------------------------------------------------------------------------------------------------
def tidy_tdt_info(data_tdt):
    # extracts info from tdt structure

    tidy_info = pd.DataFrame(
        {
            'blockname': [data_tdt.info.blockname],
            'tankpath': [data_tdt.info.tankpath],
            'start_date': [data_tdt.info.start_date],
            'utc_start_time': [data_tdt.info.utc_start_time],
            'stop_date': [data_tdt.info.stop_date],
            'utc_stop_time': [data_tdt.info.utc_stop_time],
            'duration': [data_tdt.info.duration],
            'stream_channel': [data_tdt.info.stream_channel],
            'snip_channel': [data_tdt.info.snip_channel]

        })

    return tidy_info

# streams --------------------------------------------------------------------------------------------------------------
def extract_stream_info(data_tdt_streams):
    # return info for an individual tdt stream

    tidy_streams_info = pd.DataFrame(
        {
            'name': data_tdt_streams.name,
            'code': data_tdt_streams.code,
            'size': [data_tdt_streams.size],
            'type': data_tdt_streams.type,
            'type_str': data_tdt_streams.type_str,
            'ucf': data_tdt_streams.ucf,
            'fs': data_tdt_streams.fs,
            'dform': data_tdt_streams.dform,
            'start_time': data_tdt_streams.start_time,
            'channel': data_tdt_streams.channel
        })

    return (tidy_streams_info)


def extract_stream_data(data_tdt_streams):
    # return data for an individual tdt stream

    tidy_streams_data = pd.DataFrame({
        'channel': data_tdt_streams.name,
        'raw_au': data_tdt_streams.data
    })

    return (tidy_streams_data)


def tidy_tdt_streams(data):
    # returns data and info from all streams within tdt structure

    first_concat = 1

    for stream in data.streams.keys():
        if (search('_\d\d\d[A-Za-z]', stream)):  # if stream contains _###C (id for fp channels; filters tdt preprocessed streams)
            if (first_concat):
                streams_info = extract_stream_info(data.streams[stream])
                streams_data = extract_stream_data(data.streams[stream])

                first_concat = 0;
            else:
                streams_info = pd.concat([streams_info, extract_stream_info(data.streams[stream])])
                streams_data = pd.concat([streams_data, extract_stream_data(data.streams[stream])])

    streams_info.insert(0, 'start_date', data.info.start_date)
    streams_info.insert(0, 'blockname', data.info.blockname)

    streams_data.insert(0, 'start_date', data.info.start_date)
    streams_data.insert(0, 'blockname', data.info.blockname)

    return (streams_info, streams_data)

# epochs ---------------------------------------------------------------------------------------------------------------
def extract_epoch_info(data_tdt_streams):
    # return info for an individual tdt epoc

    tidy_epoch_info = pd.DataFrame(
        {
            'name': data_tdt_streams.name,
            'type': data_tdt_streams.type,
            'type_str': data_tdt_streams.type_str,
            'dform': data_tdt_streams.dform,
            'size': [data_tdt_streams.size]
        })

    return (tidy_epoch_info)


def extract_epoch_data(data_tdt_streams):
    # return data for an individual tdt epoc

    tidy_epoch_data = pd.DataFrame(
        {'name': data_tdt_streams.name,
         'onset': data_tdt_streams.onset,
         'offset': data_tdt_streams.offset
         })

    return (tidy_epoch_data)


def tidy_tdt_epocs(data):
    for epoch in data.epocs.keys():
        if (epoch == list(data.epocs.keys())[0]):
            epocs_info = extract_epoch_info(data.epocs[epoch])
            epocs_data = extract_epoch_data(data.epocs[epoch])

        else:
            epocs_info = pd.concat([epocs_info, extract_epoch_info(data.epocs[epoch])])
            epocs_data = pd.concat([epocs_data, extract_epoch_data(data.epocs[epoch])])

    epocs_info.insert(0, 'start_date', data.info.start_date)
    epocs_info.insert(0, 'blockname', data.info.blockname)

    epocs_data.insert(0, 'start_date', data.info.start_date)
    epocs_data.insert(0, 'blockname', data.info.blockname)

    return (epocs_info, epocs_data)

# extract and tidy all files in raw directory that are not located in extracted directory ------------------------
def tidy_tdt_extract_and_tidy(dir_raw, dir_extracted):
    # return lists of files in raw and processed directories___
    raw_block_paths = os.listdir(dir_raw)
    processed_files = os.listdir(dir_extracted)

    # filter out hidden files from raw_block_paths
    raw_block_paths = list(filter(lambda raw_block_paths: raw_block_paths.find('.') == -1, raw_block_paths))

    # trim file names to blocknames
    processed_files = {x.replace('_streams_info.feather','') for x in processed_files}
    processed_files = {x.replace('_streams_data.feather','') for x in processed_files}
    processed_files = {x.replace('_epocs_info.feather','')   for x in processed_files}
    processed_files = {x.replace('_epocs_data.feather','')   for x in processed_files}
    processed_files = {x.replace('_info.feather','')         for x in processed_files}

    processed_files = list(processed_files)

    # remove files that have already been processed____________
    process_block_paths = raw_block_paths

    for processed_file in processed_files:
        try:
            while True:
                process_block_paths.remove(processed_file)
        except ValueError:
            pass
    

    if len(process_block_paths) >= 1:
        print('')
        print('extracting data from dir: ' + dir_raw + ' to dir: ' + dir_extracted)

        for process_block_path in process_block_paths:
            block_path = os.path.join(dir_raw, process_block_path)

            print("extracting blockpath: " + block_path)

            data = read_block(block_path, evtype = ['all'])

            data_info = tidy_tdt_info(data)
            streams_info, streams_data = tidy_tdt_streams(data)
            epocs_info, epocs_data = tidy_tdt_epocs(data)

            session_id = data_info['blockname'][0]

            data_info.to_feather(os.path.join(dir_extracted, session_id +'_info.feather'))

            streams_info.reset_index(drop = True).to_feather(os.path.join(dir_extracted, session_id + '_streams_info.feather'))
            streams_data.reset_index(drop = True).to_feather(os.path.join(dir_extracted, session_id + '_streams_data.feather'))

            epocs_info.reset_index(drop = True).to_feather(os.path.join(dir_extracted, session_id + '_epocs_info.feather'))
            epocs_data.reset_index(drop = True).to_feather(os.path.join(dir_extracted, session_id + '_epocs_data.feather'))
    else:
        print('no files to extract... all fp in dir :'+ dir_raw + ' has already been extracted to dir: ' + dir_extracted)

