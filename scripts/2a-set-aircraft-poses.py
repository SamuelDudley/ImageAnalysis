#!/usr/bin/python

import sys
sys.path.insert(0, "/usr/local/lib/python2.7/site-packages/")

import argparse
import commands
import cv2
import fnmatch
import os.path

sys.path.append('../lib')
import Pose
import ProjectMgr

# for all the images in the project image_dir, detect features using the
# specified method and parameters

parser = argparse.ArgumentParser(description='Set the aircraft poses from flight data.')
parser.add_argument('--project', required=True, help='project directory')
parser.add_argument('--sentera', help='use the specified sentera image-metadata.txt file (lat,lon,alt,yaw,pitch,roll)')
parser.add_argument('--pix4d', help='use the specified pix4d csv file (lat,lon,alt,roll,pitch,yaw)')

args = parser.parse_args()

proj = ProjectMgr.ProjectMgr(args.project)
print "Loading image info..."
proj.load_image_info()

pose_set = False
if args.sentera != None:
    Pose.setAircraftPoses(proj, args.sentera, order='ypr')
    pose_set = True
elif args.pix4d != None:
    Pose.setAircraftPoses(proj, args.pix4d, order='rpy')
    pose_set = True

if not pose_set:
    print "Error: no flight data specified or problem with flight data"
    print "No poses computed"
    exit

# compute the project's NED reference location (based on average of
# aircraft poses)
proj.compute_ned_reference_lla()
print "NED reference location:", proj.ned_reference_lla

proj.save()
    
