#!/usr/bin/python

import sys

import Correlate
import Image

AffineSolver = True
SimpleSolver = False
AttitudeBiasSolver = False
YawBiasSolver = False

defaultShutterLatency = 0.67    # measured by the shutter latency solver
defaultRollBias = -0.8          # measured by the attitude bias solver
defaultPitchBias = -2.0
defaultYawBias = -3.9          # measured by the yaw bias solver

def usage():
    print "Usage: " + sys.argv[0] + " <flight_data_dir> <raw_image_dir> <ground_alt_m>"
    exit()


# start of 'main' program
if len(sys.argv) != 4:
    usage()

flight_dir = sys.argv[1]
image_dir = sys.argv[2]
ground_alt_m = float(sys.argv[3])
geotag_dir = image_dir + "-geotag"

# create the image group
ig = Image.ImageGroup( max_features=800, detect_grid=4, match_ratio=0.5 )

# set up Samsung NX210 parameters
ig.setCameraParams(horiz_mm=23.5, vert_mm=15.7, focal_len_mm=30.0)

# load images, keypoints, descriptors, matches, etc.
ig.load( image_dir=geotag_dir )

# compute matches if needed
ig.computeMatches()
#ig.showMatches()

# correlate shutter time with trigger time (based on interval
# comaparison of trigger events from the flightdata vs. image time
# stamps.)
c = Correlate.Correlate( flight_dir, image_dir )
best_correlation, best_camera_time_error = c.test_correlations()

# tag each image with the camera position (from the flight data
# parameters) at the time the image was taken
ig.computeCamPositions(c, delay=defaultShutterLatency, 
                       rollbias=defaultRollBias, pitchbias=defaultPitchBias,
                       yawbias=defaultYawBias)

# compute a central lon/lat for the image set.  This will be the (0,0)
# point in our local X, Y, Z coordinate system
ig.computeRefLocation()

# initial placement
ig.computeKeyPointGeolocation( ground_alt_m )
print "Global error (start): %.2f" % ig.globalError()


def AffineSolver(steps=10, gain=0.5):
    for i in xrange(steps):
        ig.affineTransformImages(gain=gain)
        ig.generate_ac3d(c, ground_alt_m, geotag_dir, ref_image=None, base_name="quick-3d", version=i )
        print "Global error (%d) = %.2f: " % (i, ig.globalError())

def SimpleSolver(steps=10, gain=0.25):
    for i in xrange(steps):
        ig.rotateImages(gain=gain)
        ig.computeKeyPointGeolocation( ground_alt_m )
        ig.shiftImages(gain=gain)
        ig.generate_ac3d(c, ground_alt_m, geotag_dir, ref_image=None, base_name="quick-3d", version=i )
        print "Global error (%d) = %.2f: " % (i, ig.globalError())

def ShutterLatencySolver(min, max, stepsize):
    best_result = None
    best_value = None
    value = min
    while value <= max + (stepsize*0.1):
        # test fit image set with specified parameters
        ig.computeCamPositions(c, delay=value,
                               rollbias=defaultRollBias,
                               pitchbias=defaultPitchBias,
                               yawbias=defaultYawBias)
        ig.computeKeyPointGeolocation( ground_alt_m )
        error = ig.globalError()
        print "Global error (delay): %.2f %.2f" % (value, error)
        if best_result == None or error < best_result:
            best_result = error
            best_value = value
        value += stepsize
    return best_value

def AttitudeBiasSolver(rollmin, rollmax, rollstep,
                       pitchmin, pitchmax, pitchstep):
    best_result = None
    best_pitch = None
    best_roll = None
    pitchvalue = pitchmin
    while pitchvalue <= pitchmax + (pitchstep*0.1):
        rollvalue = rollmin
        while rollvalue <= rollmax + (rollstep*0.1):
            # test fit image set with specified parameters
            ig.computeCamPositions(c, delay=defaultShutterLatency,
                                   rollbias=rollvalue, pitchbias=pitchvalue,
                                   yawbias=defaultYawBias )
            ig.computeKeyPointGeolocation( ground_alt_m )
            error = ig.globalError()
            print "Global error (attitude): %.2f %.2f %.2f" % (pitchvalue, rollvalue, error)
            if best_result == None or error < best_result:
                best_result = error
                best_pitch = pitchvalue
                best_roll = rollvalue
            rollvalue += rollstep
        pitchvalue += pitchstep
    return best_roll, best_pitch

def YawBiasSolver(min, max, stepsize):
    best_result = None
    best_value = None
    value = min
    while value <= max+ (stepsize*0.1):
        # test fit image set with specified parameters
        ig.computeCamPositions(c, delay=defaultShutterLatency,
                               rollbias=defaultRollBias,
                               pitchbias=defaultPitchBias,
                               yawbias=value )
        ig.computeKeyPointGeolocation( ground_alt_m )
        error = ig.globalError()
        print "Global error (yaw): %.2f %.2f" % (value, error)
        if best_result == None or error < best_result:
            best_result = error
            best_value = value
        value += stepsize
    return best_value

#print "Best shutter latency: " + str(ShutterLatencySolver(0.0, 1.0, 0.1))
#print "Best shutter latency: " + str(ShutterLatencySolver(0.6, 0.8, 0.01))

#bestroll, bestpitch = AttitudeBiasSolver(-5.0, 5.0, 1.0, -5.0, 5.0, 1.0)
#bestroll, bestpitch = AttitudeBiasSolver(-2.0, 0.0, 0.1, -3.0, -1.0, 0.1)
#print "Best roll: %.2f pitch: %.2f" % (bestroll, bestpitch)

#print "Best yaw: " + str(YawBiasSolver(-5, -3, 0.1))

AffineSolver(steps=20)
