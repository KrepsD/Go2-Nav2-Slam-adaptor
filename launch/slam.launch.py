import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    bridge_share = get_package_share_directory('go2_nav_bridge')
    slam_share = get_package_share_directory('slam_toolbox')

    interfaces_launch = os.path.join(
        bridge_share, 'launch', 'interfaces.launch.py')
    slam_launch = os.path.join(
        slam_share, 'launch', 'online_async_launch.py')
    slam_params = os.path.join(
        bridge_share, 'config', 'slam_toolbox.yaml')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(interfaces_launch),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch),
            launch_arguments={
                'slam_params_file': slam_params,
                'use_sim_time': 'false',
                'autostart': 'true',
                'use_lifecycle_manager': 'false',
            }.items(),
        ),
    ])
