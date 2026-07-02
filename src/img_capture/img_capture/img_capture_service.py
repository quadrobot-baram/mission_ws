#!/usr/bin/env python3

import os
import re
import subprocess
import sys

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class ImgCaptureService(Node):
    def __init__(self):
        super().__init__('img_capture_service')

        self.declare_parameter('network_interface', 'enp86s0')
        self.declare_parameter('save_dir', '/home/baram/mission_ws/go2_images')
        self.declare_parameter('domain_id', 0)
        self.declare_parameter('timeout_sec', 2.0)
        self.declare_parameter('process_timeout_sec', 8.0)

        self.network_interface = self.get_parameter('network_interface').value
        self.save_dir = self.get_parameter('save_dir').value
        self.domain_id = int(self.get_parameter('domain_id').value)
        self.timeout_sec = float(self.get_parameter('timeout_sec').value)
        self.process_timeout_sec = float(self.get_parameter('process_timeout_sec').value)

        os.makedirs(self.save_dir, exist_ok=True)

        self.service = self.create_service(
            Trigger,
            'img_capture',
            self.capture_callback
        )

        self.get_logger().info('Service ready: /img_capture')
        self.get_logger().info(f'network_interface: {self.network_interface}')
        self.get_logger().info(f'save_dir: {self.save_dir}')

    def capture_callback(self, request, response):
        del request

        cmd = [
            sys.executable,
            '-m',
            'img_capture.go2_capture_once',
            '--network-interface',
            self.network_interface,
            '--save-dir',
            self.save_dir,
            '--domain-id',
            str(self.domain_id),
            '--timeout-sec',
            str(self.timeout_sec),
        ]

        self.get_logger().info('Capture request received.')
        self.get_logger().info('Running Unitree capture subprocess...')

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.process_timeout_sec,
                check=False
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if result.returncode != 0:
                response.success = False
                response.message = (
                    f'capture subprocess failed. '
                    f'returncode={result.returncode}, '
                    f'stdout={stdout}, stderr={stderr}'
                )
                self.get_logger().error(response.message)
                return response

            match = re.search(r'IMG_PATH=(.+)', stdout)
            if not match:
                response.success = False
                response.message = (
                    f'capture succeeded but image path was not found. '
                    f'stdout={stdout}, stderr={stderr}'
                )
                self.get_logger().error(response.message)
                return response

            image_path = match.group(1).strip()

            if not os.path.exists(image_path):
                response.success = False
                response.message = f'image path does not exist: {image_path}'
                self.get_logger().error(response.message)
                return response

            response.success = True
            response.message = image_path

            self.get_logger().info(f'Image captured: {image_path}')
            return response

        except subprocess.TimeoutExpired:
            response.success = False
            response.message = 'capture subprocess timeout'
            self.get_logger().error(response.message)
            return response

        except Exception as e:
            response.success = False
            response.message = f'capture service exception: {e}'
            self.get_logger().error(response.message)
            return response


def main(args=None):
    rclpy.init(args=args)
    node = ImgCaptureService()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
