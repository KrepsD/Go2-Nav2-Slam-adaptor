# GO2 Nav Bridge — ROS 2 Foxy

ROS 2 Foxy integration for autonomous navigation and SLAM on the Unitree GO2 EDU using a Hesai LiDAR, `slam_toolbox`, Nav2, and the GO2 Sport API.

This repository contains the interfaces and configuration used to integrate:

- Hesai LiDAR data with ROS 2;
- GO2 odometry;
- PointCloud-to-LaserScan conversion;
- SLAM Toolbox;
- Nav2;
- ROS 2 `/cmd_vel` commands with the Unitree Sport API.

The current implementation was developed and tested directly on a physical Unitree GO2 EDU.

> **GO2 environment backup**
>
> A download link containing files from the configured GO2 environment will be made available soon:
>
> **<>**
>
> This backup is intended mainly as a reference for users who want to inspect the workspaces, dependencies, configuration files, and general setup used on the robot.

---

## Dependencies

This project was developed using **ROS 2 Foxy**.

### Hesai LiDAR ROS 2 Driver

The Hesai LiDAR driver used in this project is based on the official Hesai ROS 2 repository:

https://github.com/HesaiTechnology/HesaiLidar_ROS_2.0

The driver provides the point cloud used by the navigation stack.

The current setup expects the package:

```text
hesai_ros_driver
```

and launches it using:

```bash
ros2 launch hesai_ros_driver start.py
```

### GO2 Odometry

The odometry implementation used in this project is provided by the INRIA Paris Robotics Lab:

https://github.com/inria-paris-robotics-lab/go2_odometry

The current setup uses:

```bash
ros2 launch go2_odometry go2_odometry_switch.launch.py odom_type:=use_full_odom
```

The odometry node provides the robot pose estimation used by SLAM Toolbox and Nav2, including the:

```text
odom -> base
```

transform.

The `unitree_description` package required by the odometry stack is also provided as part of the INRIA GO2 setup.

The Unitree ROS 2 interfaces must also already be available and sourced so that the GO2 Sport API topics and messages can be accessed.

---

## LiDAR Reference Frame

An important detail of this setup is that the physical reference frame of the Hesai LiDAR is not aligned with the GO2 body reference frame.

During testing, an obstacle physically located in front of the robot appeared approximately 90 degrees away in the generated LaserScan.

A static transform is therefore applied between:

```text
base -> hesai_lidar
```

with a yaw correction of:

```text
+90 degrees
```

or:

```text
+1.570796 rad
```

The transform used in the current setup is:

```python
arguments=[
    '0', '0', '0',
    '1.570796', '0', '0',
    'base',
    'hesai_lidar',
]
```

This correction was experimentally verified using LaserScan measurements around the physical robot.

If the LiDAR mounting position or orientation is different, this transform must be measured and adjusted accordingly.

---

## Nav2 Configuration

The parameters available in:

```text
config/nav2_params.yaml
```

were tuned experimentally on the physical GO2.

They should therefore be considered a tested starting configuration rather than universal values for every GO2.

Several parameters were selected through direct experiments with the robot, including:

- minimum translational velocity;
- maximum translational velocity;
- minimum rotational velocity;
- maximum rotational velocity;
- acceleration and deceleration limits;
- DWB controller configuration;
- goal position and orientation tolerances;
- progress checker parameters;
- recovery behavior velocities;
- robot footprint;
- local costmap configuration;
- global costmap configuration;
- obstacle marking and clearing distances;
- inflation radius;
- inflation cost scaling;
- costmap update and publishing frequencies.

A physical velocity dead zone was observed on the GO2. Commands below a certain magnitude were not sufficient to reliably move the robot.

For this reason, the DWB controller was configured so that Nav2 avoids generating very small translational and rotational commands.

The current controller configuration uses approximately:

```text
Linear velocity:
-0.80 m/s to -0.20 m/s
+0.20 m/s to +0.80 m/s

Angular velocity:
minimum magnitude: 0.50 rad/s
maximum magnitude: 1.00 rad/s
```

The local and global costmaps also use different inflation parameters.

The global costmap is configured more conservatively so that the global planner prefers paths farther away from obstacles, while the local costmap allows more flexibility during local maneuvers.

Other parameters, such as obstacle ranges, costmap update rates, goal tolerances, controller sampling, and recovery behavior, were also adjusted based on tests performed with the physical robot.

These values may require additional tuning depending on:

- floor friction;
- GO2 firmware;
- robot gait;
- LiDAR mounting;
- environment geometry;
- available navigation space.

---

# Installation

## 1. Create a ROS 2 workspace

```bash
mkdir -p ~/go2_nav_ws/src
cd ~/go2_nav_ws/src
```

## 2. Clone this repository

Clone the `Hesai_Lidar` branch:

```bash
git clone -b Hesai_Lidar https://github.com/KrepsD/Go2-Nav2-Slam-adaptor.git
```

The workspace should then contain:

```text
~/go2_nav_ws/
└── src/
    └── Go2-Nav2-Slam-adaptor/
```

## 3. Make sure the external dependencies are available

Before building this package, the following dependencies should already be installed or built:

- ROS 2 Foxy;
- Unitree ROS 2 interfaces;
- Hesai ROS 2 driver:
  https://github.com/HesaiTechnology/HesaiLidar_ROS_2.0
- GO2 odometry:
  https://github.com/inria-paris-robotics-lab/go2_odometry
- `slam_toolbox`;
- Nav2;
- `pointcloud_to_laserscan`.

For the standard ROS 2 packages:

```bash
sudo apt update

sudo apt install \
  ros-foxy-navigation2 \
  ros-foxy-nav2-bringup \
  ros-foxy-slam-toolbox \
  ros-foxy-pointcloud-to-laserscan
```

## 4. Source the required workspaces

The exact paths depend on your installation.

For example:

```bash
source /opt/ros/foxy/setup.bash
source ~/unitree_ros2/install/setup.bash
source ~/go2_odom_fix/install/setup.bash
```

If the Hesai driver is installed in another workspace, source it as well.

For example:

```bash
source ~/hesai_ws/install/setup.bash
```

## 5. Build the navigation workspace

Go to the workspace:

```bash
cd ~/go2_nav_ws
```

Install available ROS dependencies:

```bash
rosdep install --from-paths src --ignore-src -r -y
```

Build the workspace:

```bash
colcon build --symlink-install
```

Source it:

```bash
source install/setup.bash
```

---

# Running the Complete Stack

Once all dependencies are installed, built, and sourced, the complete navigation and SLAM stack can be started using:

```bash
ros2 launch go2_nav_bridge interfaces.launch.py
```

The launch file starts the main components required by the system, including:

```text
Hesai LiDAR driver
        |
        v
/lidar_points
        |
        v
PointCloud -> LaserScan
        |
        v
/scan
        |
        +----------------------+
        |                      |
        v                      v
 SLAM Toolbox             Nav2 costmaps
        |                      |
        v                      v
    map -> odom          obstacle handling


GO2 odometry
        |
        v
    odom -> base


Nav2
        |
        v
     /cmd_vel
        |
        v
cmd_vel_sport_adapter
        |
        v
/api/sport/request
        |
        v
      GO2
```

The launch file also applies the required:

```text
base -> hesai_lidar
```

rotation and starts the different components with startup delays where required.

The current startup sequence includes the Hesai LiDAR driver, GO2 odometry, SLAM Toolbox, PointCloud-to-LaserScan conversion, and Nav2.

---

## Main Configuration Files

The most relevant files are:

```text
launch/interfaces.launch.py
launch/nav2_mapping.launch.py

config/nav2_params.yaml
config/pointcloud_to_laserscan.yaml
```

`interfaces.launch.py` is intended to be the main entry point for the complete system.

---

## Notes

The configuration in this repository corresponds to the specific GO2 EDU and Hesai LiDAR setup used during development.

Before autonomous navigation on another robot, verify:

- LiDAR orientation;
- `base -> hesai_lidar` transform;
- `odom -> base` transform;
- LaserScan orientation;
- robot footprint;
- minimum usable velocity;
- maximum safe velocity;
- angular velocity limits;
- local costmap;
- global costmap;
- inflation radius;
- obstacle detection ranges.

The parameters provided here were obtained through experiments on the physical robot and may not be optimal for every GO2 or environment.

Always perform the first autonomous navigation tests in a large open area and keep the GO2 remote control or emergency stop available.
