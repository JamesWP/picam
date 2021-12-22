#!/usr/bin/python3.7
import io
import os
import sys
import subprocess
import datetime
import argparse
import shutil

def get_exposure():
    now = datetime.datetime.today().time()
    night_start = datetime.time(20,0)
    night_end = datetime.time(5,0)
    assert night_end < night_start
    at_night = now > night_start or now < night_end

    return "night" if at_night else "auto" 

def parse_args():
    parser = argparse.ArgumentParser(description="stopmotion service")                          
    parser.add_argument("photoname", default="outside")
    parser.add_argument("--output_directory", default="/var/photos")
    parser.add_argument("--raspistill", default="/usr/bin/raspistill")
    parser.add_argument("--ffmpeg", default="/usr/bin/ffmpeg")
    parser.add_argument("--photo_height", default=1080)
    parser.add_argument("--photo_width", default=1920)
    parser.add_argument("--min_photo_count", default=60, help="min number of latest photos to keep")
    parser.add_argument("--max_photo_count", default=120, help="max number of latest photos to keep")
    parser.add_argument("--annotate_photos", action="store_true", help="add timestamp to output")
    return parser.parse_args()

def take_photo(args):
    photo_time = datetime.datetime.today().strftime('%Y%m%d-%H%M%S')
    photo_path = os.path.join(args.output_directory, f"{args.photoname}.{photo_time}.jpg")

    assert not os.path.exists(photo_path)

    print("writing output to", photo_path)

    exposure = get_exposure()

    print("exposure setting", exposure)

    print("photo height", args.photo_height)

    annotation=""
    if args.annotate_photos:
        date = datetime.datetime.utcnow()

        output = io.StringIO()

        print("{:%A}".format(date), file=output)
        print("{:%H:%M:%S %d/%m/%Y UTC %B}".format(date), file=output)

        annotation = output.getvalue().strip()
    command = [args.raspistill, "--annotate", annotation, "-o", photo_path, "-ex", exposure, "--nopreview", "-w", str(args.photo_width), "-h", str(args.photo_height)]

    print("Calling", " ".join("'" + a + "'" for a in command))
    subprocess.run(command, check=True)

    assert os.path.exists(photo_path)

def get_all_photos(args):
    """ returns an ordered list of photos taken, ordered by filename 
        smaller indexes are older photos, largest indexes are newest
    """
    for f in sorted(os.listdir(args.output_directory)):
        if not f.startswith(args.photoname):
            continue
        if not f.endswith(".jpg"):
            continue
        yield os.path.join(args.output_directory, f)


def rollup_photos(args, photos):
    """/usr/bin/ffmpeg -pattern_type glob -i '/home/pi/cvt/testing*.jpg' /home/pi/cvt/part.mp4"""
    
    assert photos

    first_photo_name = os.path.basename(photos[0])

    assert first_photo_name.endswith(".jpg")
    first_photo_no_ext = first_photo_name.rsplit(".", maxsplit=1)[0]
    
    output_filename = f"{first_photo_no_ext}.mp4"

    output_filename = os.path.join(args.output_directory, output_filename)

    assert not os.path.exists(output_filename)
   
    print("encoding into", output_filename)

    p = subprocess.Popen([args.ffmpeg, "-f", "image2pipe", "-i", "-", output_filename], stdin=subprocess.PIPE)

    for photo in photos:
        print("opening", photo)
        with open(photo, "rb") as input_photo:
            print("writing photo")
            shutil.copyfileobj(input_photo, p.stdin)
            p.stdin.flush()
            print("flushing")

    p.stdin.close()
    p.wait() 

    assert os.path.exists(output_filename)

    print("encoding complete", output_filename)


def main():
    args = parse_args()

    assert os.path.isdir(args.output_directory)
    
    take_photo(args)

    assert args.min_photo_count < args.max_photo_count

    photos = list(get_all_photos(args))

    print("found", len(photos), "photos")

    if len(photos) > args.max_photo_count:
        num_to_rollup = len(photos) - args.min_photo_count
        selected_photos = photos[0:num_to_rollup]
        assert len(photos) - len(selected_photos) >= args.min_photo_count

        print("rolling up photos into mp4")
        rollup_photos(args, selected_photos)

        for photo in selected_photos:
            os.remove(photo)
        print("removed processed photos")


if __name__ == '__main__':
    sys.exit(main())
