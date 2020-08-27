import logging

import numpy as np
from pyquaternion import Quaternion
import logging
import math

class Calibrator:
    """ builds transformation matrices """

    def __init__(self):
        self.trafo_matrix = np.asarray([ \
            [1.0, 0.0, 0.0, 0.0], \
            [0.0, 1.0, 0.0, 0.0], \
            [0.0, 0.0, 1.0, 0.0], \
            [0.0, 0.0, 0.0, 1.0]])

        self.trafo_matrix_inv = np.linalg.inv(self.trafo_matrix)

        self.scale = 1.0

    def set_trafo_matrix(self, a, b, c, log_matrix=False):
        """ set transformation matrix and inverse transformation matrix from calibration sensors
            a: Becken rechts (pelvis, right)
            b: Becken links (pelvis, left)
            c: Brustbein (sternum, caudal)
        """
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

    def quaternion_to_rpy(self, qw, qx, qy, qz):
        vx, vy, vz = self.__quaternion_to_unit_vectors(qw, qx, qy, qz)

        print(vx)


        #temp_z = [vz[0], vz[1], vz[2]]
        #vz = [vx[0], vx[1], vx[2]]
        #vx = [-temp_z[0], -temp_z[1], -temp_z[2]]

        #vx = self.rotate_backward(vx) # kopf 0, -1, 0 / links 1, 0, 0 / oben 0, 0, 1
        #vy = self.rotate_backward(vy)
        #vz = self.rotate_backward(vz)

        m = self.__vectors_to_matrix(vz, -1*vy, vx)
        #print(m)
        #transformed = self.rotate_backward(m)
        #print(transformed)
        a,b,c = self.__rpy_from_matrix(m)
        #print("r: " + str(a) + ", p: " + str(b) + ", y: " + str(c))

        #b = vx[2]
        #print("---")
        #print(str(a) + ", " + str(b) + ", " + str(c))

        return c,b,a

    def __rpy_from_matrix(self, m):
        #yaw = math.atan2(m[1][0], m[0][0])
        #pitch = math.atan2(-m[2][0], np.sqrt(np.power(m[2][1], 2) + np.power(m[2][2], 2)))
        #roll = math.atan2(m[2][1], m[2][2])
        #return roll, pitch, yaw

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




    def __quaternion_to_unit_vectors(self, qw, qx, qy, qz):
        """ rotates unit vectors with input quaternion """
        # unit vectors
        vx = [1,0,0]
        vy = [0,1,0]
        vz = [0,0,1]
        # build quaternion from parameters
        q = Quaternion(qw, qx, qy, qz)
        # rotate unit vectors
        vx = q.rotate(vx)
        vy = q.rotate(vy)
        vz = q.rotate(vz)
        return np.asarray(vx), np.asarray(vy), np.asarray(vz)

    def __vectors_to_matrix(self, vx, vy, vz):
        """ builds rotation matrix from quaternion """
        # build matrix
        m = [ \
            [vx[0], vy[0], vz[0], 0.0], \
            [vx[1], vy[1], vz[1], 0.0], \
            [vx[2], vy[2], vz[2], 0.0], \
            [0.0, 0.0, 0.0, 1.0]]
        return m

    def rotations_from_vectors(self, vx, vy, vz):
        """ TODO """
        # unit vectors of the coordinate system
        ux = [1,0,0]
        uy = [0,1,0]
        uz = [0,0,1]

        # 2d projections of input vectors
        z_on_xz = [vz[0], vz[2]]
        z_on_yz = [vz[1], vz[2]]
        #x_on_xy = [vx[0], vx[1]]

        pitch = self.__angle_between(z_on_xz, [0.0, 1.0])
        yaw = self.__angle_between(z_on_yz, [0.0, 1.0])

        rotated_x = [[vx[0], vx[1], vx[2]]]


        #roll = self.__angle_between(x_on_xy, )



    def quaternion_to_rotations(self, w, x, y, z):
        """
        Source:
        https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#Quaternion_to_Euler_Angles_Conversion
        """

        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        pitch = 0
        if (abs(sinp) >= 1):
            pitch = math.copysign(math.pi / 2, sinp) # use 90 degrees if out of range
        else:
            pitch = math.asin(sinp)

        # yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        #print("r: " + str(-yaw) + ", p: " + str(pitch) + ", y: " + str(-roll))

        #return -roll, pitch, -yaw
        return -yaw, pitch, -roll

    """
    def quaternion_to_rotations(self, qw, qx, qy, qz):
        # builds rotation matrix from quaternion
        if (qw is None)or(qx is None)or(qy is None)or(qz is None):
            return 0.0, 0.0, 0.0
        # unit vectors
        vx_u = [1,0,0]
        vy_u = [0,1,0]
        vz_u = [0,0,1]

        # build quaternion from parameters
        q = Quaternion(qw, qx, qy, qz)

        #vx = q.rotate(vx_u)
        #vy = q.rotate(vy_u)
        #vz = q.rotate(vz_u)

        # rotations as 3 unit vectors
        vz = self.__inverse_vec(q.rotate(vx_u))
        vy = q.rotate(vy_u)
        vx = self.__inverse_vec(q.rotate(vz_u))

        #print("---")
        #print(vx)
        #print(vy)
        #print(vz)

        # vector on the x/z plane
        v_xz = self.__unit_vector([vz[0], 0.0, vz[2]])
        a_xz = self.__angle_between(vz, v_xz)*-np.sign(vz[1])


        # vector on the y/z plane
        v_yz = self.__unit_vector([0.0, vz[1], vz[2]])
        a_yz = self.__angle_between(vz, v_yz)*np.sign(vz[0])

        #print(self.__angle_between(vz, v_yz))

        # TODO this does not realy work
        rot_v = self.__unit_vector([vx[0], vx[1], 0.0])
        rot_angle = self.__angle_between([1.0,0.0,0.0], rot_v)#*np.sign(vx[1])
        #print(rot_v)
        #print(rot_angle)
        #v_xy = self.__unit_vector([vx[0], vx[1], 0.0])
        #a_xy = self.__angle_between(vx, v_xy)*np.sign(vx[1])*np.pi

        #print("Orientations: " + str([a_yz, a_xz, 0.0]))
        return a_yz, a_xz, rot_angle
    """


    def transform_forward(self, vector):
        """ transform vector using forward matrix """
        if len(vector) == 3:
            vector.append(1.0)
        result = np.dot(self.trafo_matrix, vector)
        result = np.multiply(1/self.scale, result)
        return [result[0], result[1], result[2]]

    def transform_backward(self, vector, do_scale=True):
        """ transform vector using inverse matrix """
        if len(vector) == 3:
            vector.append(1.0)
        result = np.dot(self.trafo_matrix_inv, vector)
        if do_scale:
            result = np.multiply(self.scale, result)
        return [result[0], result[1], result[2]]

    def rotate_backward(self, m):
        rot_m = [ \
            [self.trafo_matrix_inv[0][0], self.trafo_matrix_inv[0][1], self.trafo_matrix_inv[0][2], 0.0],
            [self.trafo_matrix_inv[1][0], self.trafo_matrix_inv[1][1], self.trafo_matrix_inv[1][2], 0.0],
            [self.trafo_matrix_inv[2][0], self.trafo_matrix_inv[2][1], self.trafo_matrix_inv[2][2], 0.0],
            [0.0, 0.0, 0.0, 1.0]]

        result = np.dot(rot_m, m)
        return [result[0], result[1], result[2]]

    def __dist_ab(self, a, b):
        """ distance between point a and b """
        ab = np.subtract(b, a)
        return np.linalg.norm(ab)

    def __angle_between(self, v1, v2):
        """ Returns the angle in radians between vectors 'v1' and 'v2'::

                >>> angle_between((1, 0, 0), (0, 1, 0))
                1.5707963267948966
                >>> angle_between((1, 0, 0), (1, 0, 0))
                0.0
                >>> angle_between((1, 0, 0), (-1, 0, 0))
                3.141592653589793
        """
        v1_u = self.__unit_vector(v1)
        v2_u = self.__unit_vector(v2)
        return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

    def __unit_vector(self, vector):
        """ Returns the unit vector of the vector.  """
        return vector / np.linalg.norm(vector)

    def __inverse_vec(self, vector):
        return [-vector[0],-vector[1],-vector[2]]
