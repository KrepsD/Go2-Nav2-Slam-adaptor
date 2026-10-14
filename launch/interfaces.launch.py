import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import TimerAction, ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():

    package_share = get_package_share_directory('go2_nav_bridge')

    cloud_config = os.path.join(
        package_share,
        'config',
        'pointcloud_to_laserscan.yaml'
    )

    return LaunchDescription([

        # ============================================================
        # Hesai LiDAR
        #
        # Equivalent command:
        # ros2 launch hesai_ros_driver start.py
        # ============================================================
        ExecuteProcess(
            cmd=[
                'ros2', 'launch',
                'hesai_ros_driver',
                'start.py',
            ],
            output='screen',
        ),

        # ============================================================
        # GO2 Odometry
        #
        # Equivalent command:
        # ros2 launch go2_odometry go2_odometry_switch.launch.py \
        #     odom_type:=use_full_odom
        # ============================================================
        ExecuteProcess(
            cmd=[
                'ros2', 'launch',
                'go2_odometry',
                'go2_odometry_switch.launch.py',
                'odom_type:=use_full_odom',
            ],
            output='screen',
        ),

        # ============================================================
        # Static TF: base -> hesai_lidar
        #
        # LiDAR yaw offset: +90 degrees
        # ============================================================
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_hesai_lidar',
            output='screen',
            arguments=[
                '0', '0', '0',
                '1.570796', '0', '0',
                'base',
                'hesai_lidar',
            ],
        ),

        # ============================================================
        # GO2 cmd_vel -> SportMode adapter
        # ============================================================
        Node(
            package='go2_nav_bridge',
            executable='cmd_vel_sport_adapter',
            name='go2_cmd_vel_sport_adapter',
            output='screen',
            parameters=[{
                'cmd_vel_topic': '/cmd_vel',
                'sport_request_topic': '/api/sport/request',

                'max_vx': 0.80,
                'max_vy': 0.15,
                'max_vyaw': 1.0,

                'cmd_timeout': 0.40,
                'enable_lateral_motion': True,
            }],
        ),

        # ============================================================
        # SLAM Toolbox
        #
        # Start delay: 2 seconds
        #
        # Equivalent command:
        #
        # ros2 run slam_toolbox async_slam_toolbox_node --ros-args \
        #   -p base_frame:=base \
        #   -p odom_frame:=odom \
        #   -p map_frame:=map \
        #   -p scan_topic:=/scan \
        #   -p max_laser_range:=25.0 \
        #   -p map_update_interval:=0.5 \
        #   -p minimum_travel_distance:=0.05 \
        #   -p minimum_travel_heading:=0.05
        # ============================================================
        TimerAction(
            period=2.0,
            actions=[
                Node(
                    package='slam_toolbox',
                    executable='async_slam_toolbox_node',
                    name='slam_toolbox',
                    output='screen',
                    parameters=[{
                        'base_frame': 'base',
                        'odom_frame': 'odom',
                        'map_frame': 'map',
                        'scan_topic': '/scan',

                        'max_laser_range': 25.0,

                        'map_update_interval': 0.5,
                        'minimum_travel_distance': 0.05,
                        'minimum_travel_heading': 0.05,
                    }],
                ),
            ],
        ),

        # ============================================================
        # PointCloud -> LaserScan
        #
        # Start delay: 5 seconds
        # ============================================================
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='pointcloud_to_laserscan',
                    executable='pointcloud_to_laserscan_node',
                    name='pointcloud_to_laserscan',
                    output='screen',
                    parameters=[cloud_config],
                    remappings=[
                        ('cloud_in', '/lidar_points'),
                        ('scan', '/scan'),
                    ],
                ),
            ],
        ),

        # ============================================================
        # Nav2
        #
        # Start delay: 7 seconds
        #
        # Equivalent command:
        # ros2 launch go2_nav_bridge nav2_mapping.launch.py
        # ============================================================
        TimerAction(
            period=7.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'launch',
                        'go2_nav_bridge',
                        'nav2_mapping.launch.py',
                    ],
                    output='screen',
                ),
            ],
        ),

    ])
