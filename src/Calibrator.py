import logging

import numpy as np
from pyquaternion import Quaternion
import logging
import math
from scipy.linalg import qr

class Calibrator:
    """ builds transformation matrices """

    def __init__(self):
        # transformation from calibrted to world
        self.trafo_matrix = np.asarray([ \
            [1.0, 0.0, 0.0, 0.0], \
            [0.0, 1.0, 0.0, 0.0], \
            [0.0, 0.0, 1.0, 0.0], \
            [0.0, 0.0, 0.0, 1.0]])

        # transformation from world to calibrated
        # use this to transform input data
        self.trafo_matrix_inv = np.linalg.inv(self.trafo_matrix)

        # scale of coordinate system
        self.scale = 1.0

        # target orientation
        self.target_rotation_matrix = None

    def set_target_rotation_matrix(self, m):
        """ target orientation (read from file?)"""
        self.target_rotation_matrix = m

    def set_trafo_matrix(self, a, b, c, log_matrix=False):
        """ set transformation matrix and inverse transformation matrix from calibration sensors
            a: Becken rechts (pelvis, right)
            b: Becken links (pelvis, left)
            c: Brustbein (sternum, caudal)
        """
        print("Setting transformation matrix...")
        # x
        m = np.multiply(0.5, np.add(a,b))
        x_axis = m
        x_axis_origin = np.subtract(m, c)
        x_axis_origin = x_axis_origin/np.linalg.norm(x_axis_origin)

        # z
        ca = np.subtract(a, c)
        cb = np.subtract(b, c)

        e = np.cross(ca, cb)
        z_axis_origin = e/np.linalg.norm(e)

        z_axis = np.add(z_axis_origin*100, c)


        # y
        cm = np.subtract(m, c)
        y_axis_origin = np.cross(z_axis_origin, cm)
        y_axis = np.add(c, y_axis_origin)
        y_axis_origin = y_axis_origin/np.linalg.norm(y_axis_origin)

        # temp axis fix
        temp = x_axis_origin
        x_axis_origin = -y_axis_origin
        y_axis_origin = -temp

        # set matrix rotation
        self.trafo_matrix[0][0] = x_axis_origin[0]
        self.trafo_matrix[1][0] = x_axis_origin[1]
        self.trafo_matrix[2][0] = x_axis_origin[2]

        self.trafo_matrix[0][1] = y_axis_origin[0]
        self.trafo_matrix[1][1] = y_axis_origin[1]
        self.trafo_matrix[2][1] = y_axis_origin[2]

        self.trafo_matrix[0][2] = z_axis_origin[0]
        self.trafo_matrix[1][2] = z_axis_origin[1]
        self.trafo_matrix[2][2] = z_axis_origin[2]
        # set matrix translation
        self.trafo_matrix[0][3] = c[0]
        self.trafo_matrix[1][3] = c[1]
        self.trafo_matrix[2][3] = c[2]

        # set inverse matrix
        self.trafo_matrix_inv = np.linalg.inv(self.trafo_matrix)

        # scale factor
        self.scale = 1 / ( (self.__dist_ab(a,b)))

        if log_matrix:
            print("trafo:")
            print(self.trafo_matrix)

            print("trafo inv:")
            print(self.trafo_matrix_inv)

            print("scale:")
            print(self.scale)

    def quaternion_to_rotation_matrix(self, Q0, Qx, Qy, Qz):
        """ quat to rotation matrix from NDI API documentation """
        # build matrix components
        m00 = (Q0 * Q0) + (Qx * Qx) - (Qy * Qy) - (Qz * Qz)
        m01 = 2.0 * ((Qx * Qy) - (Q0 * Qz))
        m02 = 2.0 * ((Qx * Qz) + (Q0 * Qy))
        m10 = 2.0 * ((Qx * Qy) + (Q0 * Qz))
        m11 = (Q0 * Q0) - (Qx * Qx) + (Qy * Qy) - (Qz * Qz)
        m12 = 2.0 * ((Qy * Qz) - (Q0 * Qx))
        m20 = 2.0 * ((Qx * Qz) - (Q0 * Qy))
        m21 = 2.0 * ((Qy * Qz) + (Q0 * Qx))
        m22 = (Q0 * Q0) - (Qx * Qx) - (Qy * Qy) + (Qz * Qz)
        # build matrix
        m = np.asarray([
            [m00, m01, m02],
            [m10, m11, m12],
            [m20, m21, m22]
        ])
        return m

    def get_transformed_rotation(self, Q0, Qx, Qy, Qz):
        """ used for model class """
        orientation_matrix = self.quaternion_to_rotation_matrix(Q0, Qx, Qy, Qz)
        transformed_matrix = self.rotate_backward(orientation_matrix)
        r,p,y = self.__rpy_from_matrix(transformed_matrix)
        return r, p, y

    def get_target_rotation_split(self, w, x, y, z):
        """ returns transformed target orientation in adjusted roll, pitch, yaw """
        assert self.target_rotation_matrix is not None
        # current orientation matrix
        orientation_matrix = self.quaternion_to_rotation_matrix(w,x,y,z)
        # backward transformed current orientation matrix
        transformed_matrix = self.rotate_backward(orientation_matrix)
        # target orientation matrix inversed
        target_inv = np.linalg.inv(self.target_rotation_matrix)
        # orientation differenc between target orientation and current orientation
        m = np.dot(target_inv, transformed_matrix)
        # calculate roll, pitch, yaw from current matrix
        r,p,y = self.__rpy_from_matrix(m)
        # TODO: the order and the sign might be missleading, make more clear what happens here
        return y, -p, r

    def __dist_ab(self, a, b):
        """ distance between point a and b """
        ab = np.subtract(b, a)
        return np.linalg.norm(ab)

    def transform_backward(self, vector, do_scale=True):
        """ transform vector using inverse matrix """
        if len(vector) == 3:
            vector.append(1.0)
        result = np.dot(self.trafo_matrix_inv, vector)
        if do_scale:
            result = np.multiply(self.scale, result)
        return [result[0], result[1], result[2]]

    def rotate_backward(self, orientation_matrix):
        """ calibrate orientation for current frame """
        # build inverse rotation matrix
        mRot = np.array([
            [self.trafo_matrix_inv[0][0], self.trafo_matrix_inv[0][1], self.trafo_matrix_inv[0][2]],
            [self.trafo_matrix_inv[1][0], self.trafo_matrix_inv[1][1], self.trafo_matrix_inv[1][2]],
            [self.trafo_matrix_inv[2][0], self.trafo_matrix_inv[2][1], self.trafo_matrix_inv[2][2]]])
        # rotate matrix
        transformed_m = np.dot(mRot, orientation_matrix)
        return transformed_m

    def __rpy_from_matrix(self, m):
        """ calculate roll pitch yaw from 3x3 rotation matrix """
        b = math.atan2(-m[2][0], np.sqrt(np.power(m[0][0],2)+np.power(m[1][0],2)))

        if b == (np.pi/2):
            a = 0.0
            c = math.atan2(m[0][1],m[1][1])
        elif b == (-np.pi/2):
            a = 0.0
            c = -math.atan2(m[0][1],m[1][1])
        else:
            a = math.atan2(m[1][0]/np.cos(b), m[0][0]/np.cos(b))
            c = math.atan2(m[2][1]/np.cos(b), m[2][2]/np.cos(b))

        return a,b,c
