"""Qt dashboard that subscribes to ``/system_status`` and renders live metrics."""

from __future__ import annotations

import os
import sys
import time

import rclpy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)
from rclpy.node import Node

from system_monitor_interfaces.msg import SystemStatus

from .formatting import format_stamp, human_bytes, human_rate


class MonitorWindow(QMainWindow):
    """Single-window dashboard with CPU, memory and network cards."""

    def __init__(self, node: Node) -> None:
        super().__init__()
        self.node = node
        self._subscription = node.create_subscription(
            SystemStatus, "system_status", self._on_status, 10
        )
        self._latest: SystemStatus | None = None
        self._last_received: float | None = None

        self.setWindowTitle("System Monitor · ROS 2")
        self.resize(700, 560)
        self.setMinimumSize(620, 500)
        self._build_ui()
        self._apply_style()
        self._set_status("WAITING", "#f4a261")

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(100)

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 22)
        root.setSpacing(16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("SYSTEM MONITOR")
        title.setObjectName("title")
        self.hostname_label = QLabel("waiting for first sample…")
        self.hostname_label.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(self.hostname_label)
        header.addLayout(title_box)
        header.addStretch(1)

        self.status_label = QLabel("WAITING")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.status_label, 0, Qt.AlignTop)
        root.addLayout(header)

        cpu_card, cpu_layout = self._card("CPU")
        cpu_row = QHBoxLayout()
        self.cpu_value = QLabel("--.-%")
        self.cpu_value.setObjectName("metric")
        self.cpu_hint = QLabel("system-wide utilization")
        self.cpu_hint.setObjectName("hint")
        cpu_row.addWidget(self.cpu_value)
        cpu_row.addSpacing(12)
        cpu_row.addWidget(self.cpu_hint, 0, Qt.AlignBottom)
        cpu_row.addStretch(1)
        cpu_layout.addLayout(cpu_row)

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setFixedHeight(9)
        cpu_layout.addWidget(self.cpu_bar)
        root.addWidget(cpu_card)

        memory_card, memory_layout = self._card("MEMORY")
        mem_row = QHBoxLayout()
        self.memory_value = QLabel("--.-%")
        self.memory_value.setObjectName("metric")
        self.memory_detail = QLabel("used -- / total --")
        self.memory_detail.setObjectName("hint")
        mem_row.addWidget(self.memory_value)
        mem_row.addSpacing(12)
        mem_row.addWidget(self.memory_detail, 0, Qt.AlignBottom)
        mem_row.addStretch(1)
        memory_layout.addLayout(mem_row)

        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        self.memory_bar.setTextVisible(False)
        self.memory_bar.setFixedHeight(9)
        memory_layout.addWidget(self.memory_bar)

        self.memory_available = QLabel("available --")
        self.memory_available.setObjectName("hint")
        memory_layout.addWidget(self.memory_available)
        root.addWidget(memory_card)

        network_card, network_layout = self._card("NETWORK")
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(6)
        grid.addWidget(self._caption("DOWNLOAD"), 0, 0)
        grid.addWidget(self._caption("UPLOAD"), 0, 1)
        self.net_recv_total = QLabel("--")
        self.net_recv_total.setObjectName("networkValue")
        self.net_sent_total = QLabel("--")
        self.net_sent_total.setObjectName("networkValue")
        grid.addWidget(self.net_recv_total, 1, 0)
        grid.addWidget(self.net_sent_total, 1, 1)
        self.net_recv_rate = QLabel("--")
        self.net_recv_rate.setObjectName("hint")
        self.net_sent_rate = QLabel("--")
        self.net_sent_rate.setObjectName("hint")
        grid.addWidget(self.net_recv_rate, 2, 0)
        grid.addWidget(self.net_sent_rate, 2, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        network_layout.addLayout(grid)
        root.addWidget(network_card)

        root.addStretch(1)
        footer = QHBoxLayout()
        self.last_sample = QLabel("last sample: --")
        self.last_sample.setObjectName("footer")
        topic = QLabel("topic: /system_status")
        topic.setObjectName("footer")
        footer.addWidget(self.last_sample)
        footer.addStretch(1)
        footer.addWidget(topic)
        root.addLayout(footer)

    def _card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 18)
        layout.setSpacing(10)
        caption = self._caption(title)
        layout.addWidget(caption)
        return frame, layout

    @staticmethod
    def _caption(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("caption")
        return label

    # --------------------------------------------------------------- data
    def _on_status(self, message: SystemStatus) -> None:
        self._latest = message
        self._last_received = time.monotonic()

    def _tick(self) -> None:
        try:
            rclpy.spin_once(self.node, timeout_sec=0.01)
        except Exception:
            pass

        if self._latest is not None:
            message = self._latest
            self._latest = None
            self._render(message)

        if self._last_received is not None:
            age = time.monotonic() - self._last_received
            if age > 5.0:
                self._set_status("STALE", "#e76f51")
            else:
                self._set_status("LIVE", "#2a9d8f")

    def _render(self, message: SystemStatus) -> None:
        hostname = (message.hostname or "unknown").strip()
        self.hostname_label.setText(f"{hostname}  ·  {format_stamp(message.stamp.sec, message.stamp.nanosec)}")

        cpu = max(0.0, min(100.0, float(message.cpu_percent)))
        memory = max(0.0, min(100.0, float(message.memory_percent)))
        self.cpu_value.setText(f"{cpu:.1f}%")
        self.cpu_bar.setValue(int(round(cpu)))
        self.memory_value.setText(f"{memory:.1f}%")
        self.memory_bar.setValue(int(round(memory)))
        self.memory_detail.setText(
            f"used {human_bytes(message.memory_used)} / total {human_bytes(message.memory_total)}"
        )
        self.memory_available.setText(
            f"available {human_bytes(message.memory_available)}"
        )

        self.net_recv_total.setText(human_bytes(message.net_bytes_recv))
        self.net_sent_total.setText(human_bytes(message.net_bytes_sent))
        self.net_recv_rate.setText(human_rate(message.net_recv_rate))
        self.net_sent_rate.setText(human_rate(message.net_send_rate))
        self.last_sample.setText(
            f"last sample: {format_stamp(message.stamp.sec, message.stamp.nanosec)}"
        )

    def _set_status(self, text: str, color: str) -> None:
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"color: {color}; border: 1px solid {color}; "
            "border-radius: 11px; padding: 4px 12px; font-weight: 600;"
        )

    # -------------------------------------------------------------- style
    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #0b1220;
                color: #e6edf7;
            }
            QLabel#title {
                font-size: 22px;
                font-weight: 700;
                letter-spacing: 2px;
                color: #f8fbff;
            }
            QLabel#subtitle, QLabel#hint, QLabel#footer {
                color: #8194b2;
                font-size: 12px;
            }
            QLabel#caption {
                color: #6f86a6;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1.5px;
            }
            QFrame#card {
                background: #121c2e;
                border: 1px solid #1e2d47;
                border-radius: 14px;
            }
            QLabel#metric {
                font-size: 34px;
                font-weight: 700;
                color: #4cc9f0;
            }
            QLabel#networkValue {
                font-size: 20px;
                font-weight: 600;
                color: #c9d7ea;
            }
            QProgressBar {
                background: #1b2940;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: #4cc9f0;
                border-radius: 4px;
            }
            """
        )

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API name)
        self._timer.stop()
        try:
            self.node.destroy_subscription(self._subscription)
        except Exception:
            pass
        super().closeEvent(event)


def main(args=None) -> int:
    if not any(
        os.environ.get(name)
        for name in ("DISPLAY", "WAYLAND_DISPLAY", "QT_QPA_PLATFORM")
    ):
        print(
            "No DISPLAY/WAYLAND_DISPLAY detected. "
            "Run the publisher headless and inspect /system_status with "
            "`ros2 topic echo`, or start this GUI from a desktop session.",
            file=sys.stderr,
        )
        return 1

    rclpy.init(args=args)
    node = rclpy.create_node("system_status_gui")

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName("System Monitor")
    app.setFont(QFont("DejaVu Sans", 10))

    window = MonitorWindow(node)
    window.show()
    try:
        return app.exec_()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())
