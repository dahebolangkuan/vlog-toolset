#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import glob
import os
import sys
from autosub import *


def extract_transcripts(
    source_path,
    src_language=DEFAULT_SRC_LANGUAGE,
    api_key=None,
):
    audio_filename, audio_rate = extract_audio(source_path, rate=48000)
    regions = find_speech_regions(audio_filename)

    converter = FLACConverter(source_path=audio_filename)
    recognizer = SpeechRecognizer(language=src_language, rate=audio_rate,
                                  api_key=GOOGLE_SPEECH_API_KEY)

    transcripts = []
    timed_subtitles = []

    try:
        if regions:
            extracted_regions = []
            for i, extracted_region in enumerate(pool.imap(converter, regions)):
                extracted_regions.append(extracted_region)

            for i, transcript in enumerate(pool.imap(recognizer, extracted_regions)):
                transcripts.append(transcript)

        timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]
    finally:
        os.remove(audio_filename)
    return timed_subtitles


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage: %s dir-with-video-files/' % sys.argv[0]
        sys.exit(1)

    dir_with_videos = sys.argv[1]
    output = dir_with_videos + '/videos.meta'

    concurrency = 32
    pool = multiprocessing.Pool(concurrency)

    f = open(output, 'w')

    for filename in sorted(glob.glob(dir_with_videos + '/0*.mp4')):
        print 'processing ' + filename
        try:
            for (start, end), t in extract_transcripts(filename, src_language='ru'):
                line = '\t'.join([os.path.basename(filename), '1.0', str(start), str(end), t.encode('utf-8')]) + '\n'
                f.write(line)
        except Exception as e:
            print 'failed to process ' + filename
            print e

    f.close()

    print 'terminating the pool'
    pool.terminate()
    pool.join()

    print 'done'
    print output
