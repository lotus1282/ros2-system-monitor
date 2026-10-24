from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Start the metrics publisher and the Qt dashboard together."""
    return LaunchDescription(
        [
            Node(
                package="system_monitor_gui",
                executable="system_status_publisher",
                name="system_status_publisher",
                output="screen",
            ),
            Node(
                package="system_monitor_gui",
                executable="system_status_gui",
                name="system_status_gui",
                output="screen",
            ),
        ]
    )
