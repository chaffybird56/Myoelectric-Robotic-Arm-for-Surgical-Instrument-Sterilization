#By: Ahmed(Ibrahim) Sahi and Ahmad Choudhry. We worked on the program in collaboration.

# random container is spawned
import time
import sys
import random

sys.path.append('../')

from Common_Libraries.p2_lib import *
import os
from Common_Libraries.repeating_timer_lib import repeating_timer


def update_sim():
    try:
        arm.ping()
    except Exception as error_update_sim:
        print(error_update_sim)


arm = qarm()

update_thread = repeating_timer(2, update_sim)

# Defining a list to track the containers that have been spawned
global spawned
spawned = []


# A function used to spawn a container that has not already been used
def spawn():
    while True:
        new_id = random.randint(1, 6)
        if new_id not in spawned:
            global ID
            ID = new_id
            break
    arm.spawn_cage(ID)
    print(ID)
    spawned.append(ID)


# The threshold for myoelectric interface
thresh = 0.5


# Function used to open drawers based on container ID
def open_drawer(cont_id):
    if cont_id == 4:
        arm.open_red_autoclave(True)
    elif cont_id == 5:
        arm.open_green_autoclave(True)
    elif cont_id == 6:
        arm.open_blue_autoclave(True)


# Function used to close drawers based on container ID
def close_drawer(cont_id):
    if cont_id == 4:
        arm.open_red_autoclave(False)
    elif cont_id == 5:
        arm.open_green_autoclave(False)
    elif cont_id == 6:
        arm.open_blue_autoclave(False)


# Pickup Location for all containers
pick_up = [0.5055, 0.0, 0.0227]


# Function that returns dropoff location based on container ID
def get_drop_off(cont_id):
    if cont_id == 1:  # red top (r1)
        drop_off = [-0.6078, 0.2517, 0.37]
    elif cont_id == 3:  # blue top (b1)
        drop_off = [0.0, 0.6334, 0.37]
    elif cont_id == 2:  # green top (g1)
        drop_off = [0.0, -0.6334, 0.37]
    elif cont_id == 4:  # red bottom (r2)
        drop_off = [-0.3622, 0.15, 0.31]
    elif cont_id == 6:  # blue bottom (b2)
        drop_off = [0.0, 0.395, 0.31]
    elif cont_id == 5:  # green bottom (g2)
        drop_off = [0.0, -0.395, 0.31]
    return drop_off


# Uses open_drawer() or close_drawer() function based on position of arm
def drawer():
    if arm.effector_position() == (pick_up[0], pick_up[1], pick_up[2]):
        open_drawer(ID)
    elif arm.effector_position() == (get_drop_off(ID)[0], get_drop_off(ID)[1], get_drop_off(ID)[2]):
        close_drawer(ID)


global grip_amount
grip_amount = []


# Opens or closes gripper based on position of arm
def gripper():
    if arm.effector_position() == (pick_up[0], pick_up[1], pick_up[2]) and len(
            grip_amount) == 0:  # Closing the gripper (at pickup)
        arm.control_gripper(30)
        grip_amount.append("1")
    elif arm.effector_position() == (get_drop_off(ID)[0], get_drop_off(ID)[1], get_drop_off(ID)[2]) and len(
            grip_amount) == 1:
        arm.control_gripper(-30)
        grip_amount.remove("1")


# Defines a list that gets appended once all containers are dropped off, breaking the while loop
end = []


# Moves arm to pickup, dropoff or home based on starting position
def move_arm():
    if arm.effector_position() == (0.4064, 0.0, 0.4826):
        arm.move_arm(pick_up[0], pick_up[1], pick_up[2])
        time.sleep(1)
    elif arm.effector_position() == (pick_up[0], pick_up[1], pick_up[2]):
        arm.move_arm(0.4064, 0.0, 0.4826)
        time.sleep(1)
        arm.move_arm(get_drop_off(ID)[0], get_drop_off(ID)[1], get_drop_off(ID)[2])
        time.sleep(1)
    # Resets arm and spawns new; terminates program if all items have been dropped off
    else:
        arm.home()
        if len(spawned) == 6:
            print("Congratulations!")
            end.append(1)
        else:
            spawn()


spawn()

while True:
    right = arm.emg_right()
    left = arm.emg_left()
    time.sleep(1.5)

    # Breaks loop when 6 containers have been dropped off
    if len(end) == 1:
        break

    # Right arm used to control drawers
    elif right > thresh and left < thresh:
        drawer()
        time.sleep(2)

    # Left arm used to control gripper
    elif left > thresh and right < thresh:
        gripper()
        time.sleep(2)

    # Both arms used to control qarm
    elif right > thresh and left > thresh:
        move_arm()
        time.sleep(2)
