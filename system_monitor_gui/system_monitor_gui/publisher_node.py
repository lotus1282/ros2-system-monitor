"""Publish a 1 Hz snapshot of host CPU, memory and network counters."""

from __future__ import annotations

import socket
import time

import psutil
import rclpy
from rclpy.node import Node

from system_monitor_interfaces.msg import SystemStatus


class SystemStatusPublisher(Node):
    """Collect local system metrics and publish them on ``system_status``."""

    def __init__(self) -> None:
        super().__init__("system_status_publisher")

        self.declare_parameter("publish_rate_hz", 1.0)
        rate_hz = float(self.get_parameter("publish_rate_hz").value)
        if rate_hz <= 0.0:
            self.get_logger().warning(
                f"publish_rate_hz={rate_hz} is invalid; falling back to 1.0 Hz"
            )
            rate_hz = 1.0

        self._hostname = socket.gethostname()
        self._publisher = self.create_publisher(SystemStatus, "system_status", 10)
        self._last_net = None
        self._last_sample_time = None

        # Prime psutil's CPU counter so the first published sample is meaningful.
        psutil.cpu_percent(interval=None)
        time.sleep(0.1)

        self._timer = self.create_timer(1.0 / rate_hz, self._publish_sample)
        self.get_logger().info(
            f"Publishing system status at {rate_hz:.2f} Hz on /system_status"
        )

    def _publish_sample(self) -> None:
        now = time.monotonic()
        memory = psutil.virtual_memory()
        net = psutil.net_io_counters()

        bytes_recv = int(getattr(net, "bytes_recv", 0) or 0)
        bytes_sent = int(getattr(net, "bytes_sent", 0) or 0)

        recv_rate = 0.0
        send_rate = 0.0
        if self._last_net is not None and self._last_sample_time is not None:
            elapsed = max(now - self._last_sample_time, 1e-6)
            recv_rate = max(0.0, (bytes_recv - self._last_net[0]) / elapsed)
            send_rate = max(0.0, (bytes_sent - self._last_net[1]) / elapsed)

        self._last_net = (bytes_recv, bytes_sent)
        self._last_sample_time = now

        message = SystemStatus()
        message.stamp = self.get_clock().now().to_msg()
        message.hostname = self._hostname
        message.cpu_percent = float(psutil.cpu_percent(interval=None))
        message.memory_percent = float(memory.percent)
        message.memory_total = int(memory.total)
        message.memory_used = int(memory.used)
        message.memory_available = int(memory.available)
        message.net_bytes_recv = bytes_recv
        message.net_bytes_sent = bytes_sent
        message.net_recv_rate = float(recv_rate)
        message.net_send_rate = float(send_rate)

        self._publisher.publish(message)
        self.get_logger().debug(
            f"cpu={message.cpu_percent:.1f}% "
            f"mem={message.memory_percent:.1f}% "
            f"rx={recv_rate:.0f}B/s tx={send_rate:.0f}B/s"
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = SystemStatusPublisher()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
