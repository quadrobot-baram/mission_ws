from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'network_interface',
            default_value='enp86s0',
            description='Network interface connected to Go2'
        ),

        DeclareLaunchArgument(
            'save_dir',
            default_value='/home/baram/mission_ws/go2_images',
            description='Directory to save captured images'
        ),

        DeclareLaunchArgument(
            'domain_id',
            default_value='0',
            description='Unitree DDS domain id'
        ),

        DeclareLaunchArgument(
            'timeout_sec',
            default_value='2.0',
            description='Unitree VideoClient timeout seconds'
        ),

        DeclareLaunchArgument(
            'process_timeout_sec',
            default_value='8.0',
            description='Subprocess timeout seconds'
        ),

        Node(
            package='img_capture',
            executable='img_capture_service',
            name='img_capture_service',
            output='screen',
            parameters=[
                {
                    'network_interface': LaunchConfiguration('network_interface'),
                    'save_dir': LaunchConfiguration('save_dir'),
                    'domain_id': LaunchConfiguration('domain_id'),
                    'timeout_sec': LaunchConfiguration('timeout_sec'),
                    'process_timeout_sec': LaunchConfiguration('process_timeout_sec'),
                }
            ]
        )
    ])
