import logging

import numpy as np
from pyquaternion import Quaternion


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

    def set_trafo_matrix(self, a, b, c):
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

        print("trafo:")
        print(self.trafo_matrix)

        print("trafo inv:")
        print(self.trafo_matrix_inv)

        print("scale:")
        print(self.scale)

        """
        print(self.scale)
        print("TEST")
        test_a = self.transform_backward(a)
        print(test_a)
        test_a = np.multiply(self.scale, test_a)
        print(test_a)

        v_test = [0.0,0.0,0.0,1.0]
        test = np.dot(self.trafo_matrix, v_test)
        print("test")
        print(test)

        test = np.dot(self.trafo_matrix_inv, test)
        print("test")
        print(test)

        print("Trafo Matix:")
        print(self.trafo_matrix)

        print("z_axis: " + str(z_axis))
        print("y_axis: " + str(y_axis))
        print("x_axis: " + str(x_axis))

        print("z_axis_origin: " + str(z_axis_origin))
        print("y_axis_origin: " + str(y_axis_origin))
        print("x_axis_origin: " + str(x_axis_origin))

        # check. all should be 90deg
        print("angle xy: " + str(np.degrees(self.__angle_between(x_axis_origin, y_axis_origin))))
        print("angle xz: " + str(np.degrees(self.__angle_between(x_axis_origin, z_axis_origin))))
        print("angle yz: " + str(np.degrees(self.__angle_between(y_axis_origin, z_axis_origin))))
        """

    def quaternion_to_rotation_matrix(self, qw, qx, qy, qz):
        """ builds rotation matrix from quaternion """
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
        # build matrix
        m = [ \
            [vx[0], vy[0], vz[0], 0.0], \
            [vx[1], vy[1], vz[1], 0.0], \
            [vx[2], vy[2], vz[2], 0.0], \
            [0.0, 0.0, 0.0, 1.0]]
        return m

    def quaternion_to_rotations(self, qw, qx, qy, qz):
        """ builds rotation matrix from quaternion """
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



    def transform_forward(self, vector):
        """ transform vector using forward matrix """
        if len(vector) == 3:
            vector.append(1.0)
        result = np.dot(self.trafo_matrix, vector)
        result = np.multiply(1/self.scale, result)
        return [result[0], result[1], result[2]]

    def transform_backward(self, vector):
        """ transform vector using inverse matrix """
        if len(vector) == 3:
            vector.append(1.0)
        result = np.dot(self.trafo_matrix_inv, vector)
        result = np.multiply(self.scale, result)
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
