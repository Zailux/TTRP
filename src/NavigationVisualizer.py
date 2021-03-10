import logging
import tkinter as tk

import matplotlib
matplotlib.use('Tkagg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D


class NavigationVisualizer:

    def __init__(self, Frame):
        self.Frame = Frame

        # input data
        self.pos_x = 0
        self.pos_y = 0
        self.pos_z = 0
        self.ori_x = 0
        self.ori_y = 0
        self.ori_z = 0

        self.target_pos_x = 0
        self.target_pos_y = 0
        self.target_pos_z = 0
        self.target_ori_x = 0
        self.target_ori_y = 0
        self.target_ori_z = 0

        self.fig = plt.Figure()
        self.fig.set_dpi(100)
        self.fig.set_size_inches(7, 5.5)
        self.ax = self.fig.add_subplot(xlim=(-1, 1.2), ylim=(-1, 1))
        #self.ax.set_axis_off()
        self.ax.axes.get_xaxis().set_visible(False)
        self.ax.axes.get_yaxis().set_visible(False)
        self.ax.margins(0,0)
        self.ax.set_facecolor("black")
        

        self.circle_count = 8 # >= 2
        self.target_tollerance = 0.025

        help_line_color = (0.5, 0.5, 0.5)
        # help lines
        self.ax.plot((-1,1), (0,0), color = help_line_color)
        self.ax.plot((0,0), (-1,1), color = help_line_color)
        self.ax.plot((1.0,1.2), (0,0), color = (0.1, 0.1, 0.1))
        target_circle = plt.Circle((0, 0), 1/self.circle_count, fc='y', fill=False, color=help_line_color)
        self.ax.add_artist(target_circle)

        # target cross
        self.line1, = self.ax.plot((1,1), (0.9,1.1), color = "r")
        self.line2, = self.ax.plot((0.9,1.1), (1,1), color = "r")
        # height line
        self.line3, = self.ax.plot((1.0,1.2), (0,0), color = "r")

        # target circles
        self.circles = []
        for i in range(self.circle_count):
            self.circles.append(plt.Circle((0, 0), (i+1)*(1/self.circle_count), fc='y', fill=False))

        self.canvas = FigureCanvasTkAgg(self.fig, Frame)

        self.__initAll()
        self.__animateAll(5)

    def update_All(self):
        self.__animateAll(0)
        self.canvas.draw()

    def set_pos(self, x, y, z):
        self.pos_x = x #max(min(x, 1), -1)
        self.pos_y = y #max(min(y, 1), -1)
        self.pos_z = z
        
    def set_ori(self, roll, pitch, yaw):
        self.ori_x = yaw
        self.ori_y = pitch
        self.ori_z = roll

    def set_target_pos(self, x, y, z):
        self.target_pos_x = x
        self.target_pos_y = y
        self.target_pos_z = z

    def set_target_ori(self, x, y, z):
        #return
        self.target_ori_x = x
        self.target_ori_y = y
        self.target_ori_z = z

    def __initAll(self):
        """
        initialize all animations
        """
        logging.info("Init All Animations")
        for patch in self.circles:
            self.ax.add_patch(patch)
        return self.circles+[self.line1,self.line2,self.line3]

    def is_orientation_in_tolerance():
        correction_ori_x = self.ori_x - self.target_ori_x
        correction_ori_y = self.ori_y - self.target_ori_y
        correction_ori_z = self.ori_z - self.target_ori_z

        if ((abs(correction_ori_x)<self.target_tollerance)and(abs(correction_ori_y)<self.target_tollerance)and(abs(correction_ori_z)<self.target_tollerance)):
            return True
        else:
            return False

    def is_position_in_tolerance():
        correction_x = self.pos_x - self.target_pos_x
        correction_y = self.pos_y - self.target_pos_y

        if ((abs(correction_x)<self.target_tollerance)and(abs(correction_y)<self.target_tollerance)):
            return True
        else:
            return False

    def __animateCircles(self):
        """
        target circle animation
        """
        # target correction for orientation is currently managed by the calibrator
        correction_ori_x = self.ori_x# - self.target_ori_x
        correction_ori_y = self.ori_y# - self.target_ori_y

        # color circles to indicate if target has been reached
        color = "red"
        if ((abs(correction_ori_x)<self.target_tollerance)and(abs(correction_ori_y)<self.target_tollerance)):
            color = "green"

        circle_count = len(self.circles)
        for p in range(circle_count):
            self.circles[p].center = (((circle_count-1-p)/(circle_count-1))*correction_ori_x, ((circle_count-1-p)/(circle_count-1))*correction_ori_y)
            self.circles[p].set_color(color)

        return self.circles

    def __rotate(self, point, angle, center):
        p = Point(point.x-center.x, point.y-center.y)


        point.x = p.x * np.cos(angle) - p.y * np.sin(angle)
        point.y = p.x * np.sin(angle) + p.y * np.cos(angle)

        point.x += center.x
        point.y += center.y

        return point

    def __animateLines(self):
        """
        target cros animation
        """

        # current position/ target position difference
        # TODO: why is x negative?
        correction_x = -(self.pos_x - self.target_pos_x)
        correction_y = self.pos_y - self.target_pos_y
        correction_z = self.pos_z - self.target_pos_z

        # build a cross at the correct x/y coordinates
        p11 = Point(correction_x,correction_y-0.1)
        p12 = Point(correction_x,correction_y+0.2)
        p21 = Point(correction_x-0.2,correction_y)
        p22 = Point(correction_x+0.2,correction_y)

        # TODO: is this necessary? orintation targeting might be handled by the calibrator class 
        correction_ori_z = self.ori_z - self.target_ori_z
        # rotate the cross according to the roll langle
        p11 = self.__rotate(p11, correction_ori_z, Point(correction_x, correction_y))
        p12 = self.__rotate(p12, correction_ori_z, Point(correction_x, correction_y))
        p21 = self.__rotate(p21, correction_ori_z, Point(correction_x, correction_y))
        p22 = self.__rotate(p22, correction_ori_z, Point(correction_x, correction_y))

        # target cross x/y color
        color = "red"
        if ((abs(correction_x)<self.target_tollerance)and(abs(correction_y)<self.target_tollerance)):
            self.line2.set_color("green")
        else:
            self.line2.set_color("red")

        # roll color            
        if (abs(correction_ori_z) < self.target_tollerance):
            self.line1.set_color("green")
        else:
            self.line1.set_color("red")
        
        # heigth color
        if (abs(correction_z) < self.target_tollerance):
            self.line3.set_color("green")
        else:
            self.line3.set_color("red")

        self.line1.set_data((p11.x,p12.x), (p11.y,p12.y))
        self.line2.set_data((p21.x,p22.x), (p21.y,p22.y))
        self.line3.set_data((1.0, 1.2), (correction_z, correction_z))
        return [self.line1,self.line2, self.line3]

    def __animateAll(self, i):
        """
        handles all animations
        calls animation function and returns list with every animated object

        """
        circles = self.__animateCircles()
        lines = self.__animateLines()
        return circles+lines

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
