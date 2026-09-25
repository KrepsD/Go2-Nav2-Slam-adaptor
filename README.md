# GO2 Nav Bridge — ROS 2 Foxy

Interfaces required to use the Unitree GO2 EDU topics with `slam_toolbox` and
Nav2:

- `/utlidar/robot_odom` (`nav_msgs/Odometry`) -> TF `odom -> base_link`;
- `/utlidar/cloud_deskewed` (`sensor_msgs/PointCloud2`) -> `/scan`;
- `/cmd_vel` (`geometry_msgs/Twist`) -> `/api/sport/request`;
- SLAM Toolbox publishes `map -> odom`.

## 1. Place the package in the workspace

```bash
mkdir -p ~/go2_nav_ws/src
cp -r go2_nav_bridge ~/go2_nav_ws/src/
```

The `unitree_api` package must already be built and sourced. On the GO2 this is
normally in the Unitree CycloneDDS workspace.

## 2. Install runtime dependencies

```bash
sudo apt update
sudo apt install ros-foxy-pointcloud-to-laserscan ros-foxy-slam-toolbox
```

Nav2 can be installed after the interfaces and SLAM tests pass:

```bash
sudo apt install ros-foxy-navigation2 ros-foxy-nav2-bringup
```

## 3. Build

Use the same shell setup that already exposes the GO2 topics and
`unitree_api/msg/Request`.

```bash
source /opt/ros/foxy/setup.bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
cd ~/go2_nav_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select go2_nav_bridge
source install/setup.bash
```

If the Unitree workspace has another location, replace the second `source`.

## 4. Test odometry TF first

Terminal 1:

```bash
ros2 run go2_nav_bridge odom_tf_broadcaster
```

Terminal 2:

```bash
ros2 run tf2_ros tf2_echo odom base_link
```

The transformation must update continuously. Stop this test before launching
the combined launch file, otherwise two nodes will publish the same TF.

## 5. Test the PointCloud2 conversion

```bash
ros2 launch go2_nav_bridge interfaces.launch.py
```

`pointcloud_to_laserscan` subscribes lazily, so start a `/scan` subscriber:

```bash
ros2 topic hz /scan
ros2 topic echo /scan --once
```

In RViz, set `Fixed Frame` to `odom` and add `/scan` and
`/utlidar/cloud_deskewed`. Tune `min_height` and `max_height` in
`config/pointcloud_to_laserscan.yaml` until the scan contains obstacles but not
the floor or the robot's legs.

## 6. Test the velocity adapter safely

Use a clear, level test area with nobody within the robot's reach. Start with
the GO2 standing in Sport mode, keep the remote/emergency stop available, and
be ready to stop the robot immediately. Do not improvise a support stand.

```bash
ros2 launch go2_nav_bridge interfaces.launch.py
```

Send a small forward command for a short period:

```bash
timeout 1 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.10, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

After the publisher stops, the 0.4 s watchdog sends the Sport `StopMove`
request. Test yaw only after forward motion works.

## 7. Start mapping

Do not run Unitree uSLAM or another process that also publishes `map -> odom`.

```bash
ros2 launch go2_nav_bridge slam.launch.py
```

Check:

```bash
ros2 topic hz /scan
ros2 topic echo /map --once
ros2 run tf2_ros tf2_echo map base_link
```

Use RViz with `Fixed Frame = map`. Drive slowly using teleoperation before
starting Nav2 autonomous control.

## 8. Nav2 integration

Configure all Nav2 `robot_base_frame`/`base_frame_id` values as `base_link`, and
all global frames as `map`. Configure local costmap `global_frame` as `odom`.
Where Nav2 expects `/odom`, remap it to `/utlidar/robot_odom` or set its
`odom_topic` parameter accordingly.

The GO2 supports lateral velocity, so a holonomic controller may use
`linear.y`. For the first autonomous tests, disabling lateral motion in
`interfaces.launch.py` is safer:

```python
'enable_lateral_motion': False,
```

The Nav2 footprint and controller limits must be measured/tuned on the physical
robot before autonomous movement.

After the separate TF, scan, command and SLAM tests pass, start the complete
mapping/navigation stack:

```bash
ros2 launch go2_nav_bridge nav2_mapping.launch.py
```

The supplied `config/nav2_params.yaml` starts conservatively as a
non-holonomic controller (`max_vel_y: 0.0`). It is an initial bring-up file,
not final physical-robot tuning. Keep the GO2 in an open test area with the
remote/emergency stop ready, then send the first goals at short distances.

## Safety and implementation notes

- Sport API `Move` uses API ID `1008` with JSON keys `x`, `y`, `z` for
  `vx`, `vy`, `vyaw`.
- Sport API `StopMove` uses API ID `1003`.
- The adapter clamps all commands and stops after a command timeout.
- Do not connect Nav2 to `/lowcmd`; that is the joint-level interface.
- Do not run more than one `odom -> base_link` broadcaster.
- If the point cloud is dropped because of TF extrapolation, compare the
  timestamps of `/utlidar/robot_odom` and `/utlidar/cloud_deskewed`.
