import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('go2_nav_bridge')
    cloud_config = os.path.join(
        package_share, 'config', 'pointcloud_to_laserscan.yaml')

    return LaunchDescription([
        Node(
            package='go2_nav_bridge',
            executable='odom_tf_broadcaster',
            name='go2_odom_tf_broadcaster',
            output='screen',
            parameters=[{
                'odom_topic': '/utlidar/robot_odom',
                'parent_frame': 'odom',
                'child_frame': 'base_link',
                'use_message_frames': True,
            }],
        ),
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            output='screen',
            parameters=[cloud_config],
            remappings=[
                ('cloud_in', '/utlidar/cloud_deskewed'),
                ('scan', '/scan'),
            ],
        ),
        Node(
            package='go2_nav_bridge',
            executable='cmd_vel_sport_adapter',
            name='go2_cmd_vel_sport_adapter',
            output='screen',
            parameters=[{
                'cmd_vel_topic': '/cmd_vel',
                'sport_request_topic': '/api/sport/request',
                'max_vx': 0.25,
                'max_vy': 0.15,
                'max_vyaw': 0.40,
                'cmd_timeout': 0.40,
                'enable_lateral_motion': True,
            }],
        ),
    ])
