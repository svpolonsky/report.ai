import pathlib

path_to_testset='/home/stas/Projects/faces/YouTubeFaces_05d/frame_images_DB'
# for video: which frame to select
frame_number=30

def video_paths(fname):
    # example of lines in fname
    # /home/stas/Projects/faces/YouTubeFaces_05d/frame_images_DB/Aaron_Sorkin/3/%05d.jpg
    with open(fname) as f:
        paths = f.readlines() # as strings
    return paths

def frame_path(video, frame_number):
    path=video.strip() % frame_number
    return pathlib.Path(path)

# fname's lines give paths to images
def image_paths(fname):
    videos=video_paths(fname)
    paths = [image_path(video,frame_number) for video in videos]
    return paths

def read_bounding_box(image_path):
    # given image path get face's bounding box
    box_path=image_path.with_suffix('.txt')
    with open(box_path,'r') as f:
        line=f.readline()
    xcenter,ycenter,width,height=map(float,line.split(','))
    return {'xcenter':xcenter, 'ycenter':ycenter, 'xwidth':width, 'yheight':height}

# extract true person's name from path to image
def person_name(path):
    name=str(path).split("/")[-3]
    return name
