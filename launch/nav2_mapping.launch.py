import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    bridge_share = get_package_share_directory('go2_nav_bridge')
    nav2_share = get_package_share_directory('nav2_bringup')

    slam_launch = os.path.join(bridge_share, 'launch', 'slam.launch.py')
    navigation_launch = os.path.join(
        nav2_share, 'launch', 'navigation_launch.py')
    nav2_params = os.path.join(
        bridge_share, 'config', 'nav2_params.yaml')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(navigation_launch),
            launch_arguments={
                'use_sim_time': 'false',
                'autostart': 'true',
                'params_file': nav2_params,
                'use_respawn': 'false',
            }.items(),
        ),
    ])
