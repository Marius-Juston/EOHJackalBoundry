#! /usr/bin/env python
# coding=utf-8

import numpy as np

import rospy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Joy
from tf.transformations import euler_from_quaternion


class Boundry:
    def __init__(self):
        self.sub = rospy.Subscriber("/odometry/filtered", Odometry, self.callback)
        self.pub = rospy.Publisher("/cmd_vel", Twist, queue_size=10)
        self.joy_sub = rospy.Subscriber("/bluetooth_teleop/joy", Joy, self.joy_callback)

        self.reset_button_idx = [4, 5, 9, 10]

        self.pose_transform = None
        self.stop = False

    def joy_callback(self, msg):
        pressed = []

        for i in self.reset_button_idx:
            pressed.append(msg.buttons[i])

        # print pressed

        if np.all(pressed):
            self.pose_transform = None

    def callback(self, msg):
        pose = msg.pose.pose

        x = pose.position.x
        y = pose.position.y

        orientation_q = pose.orientation
        orientation_list = [orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w]
        (_, _, theta) = euler_from_quaternion(orientation_list)

        if self.pose_transform is None:
            T = np.array([
                [1, 0, -x],
                [0, 1, -y],
                [0, 0, 1],
            ])

            R = np.array([
                [np.cos(-theta), -np.sin(-theta), 0],
                [np.sin(-theta), np.cos(-theta), 0],
                [0, 0, 1],
            ])

            self.pose_transform = np.matmul(R, T)

        pose = np.asarray([x, y, 1])
        pose = np.matmul(pose, self.pose_transform)
        x, y = pose[0], pose[1]

        print x, y, theta

        width = rospy.get_param("width", 10)
        height = rospy.get_param("height", 10)

        if x < -width / 2 or x > width / 2 or y < -.1 or y > height:
            self.stop = True
        else:
            self.stop = False

    def step(self):
        twist = Twist()
        twist.linear.x = 0
        twist.angular.z = 0

        self.pub.publish(twist)


if __name__ == '__main__':
    rospy.init_node("boundary")

    b = Boundry()

    rate = rospy.Rate(120)

    while not rospy.is_shutdown():
        b.step()

        rate.sleep()
