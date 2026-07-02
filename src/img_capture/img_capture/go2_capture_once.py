#!/usr/bin/env python3

import argparse
import os
import sys
import time


def parse_args():
    parser = argparse.ArgumentParser(description='Capture one image from Go2 front camera.')
    parser.add_argument('--network-interface', default='enp86s0')
    parser.add_argument('--save-dir', default='/home/baram/mission_ws/go2_images')
    parser.add_argument('--domain-id', type=int, default=0)
    parser.add_argument('--timeout-sec', type=float, default=2.0)
    return parser.parse_args()


def make_image_path(save_dir):
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    return os.path.join(save_dir, f'go2_{timestamp}.jpg')


def main():
    args = parse_args()

    try:
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize
        from unitree_sdk2py.go2.video.video_client import VideoClient
    except Exception as e:
        print(f'failed to import unitree_sdk2py: {e}', file=sys.stderr)
        print('hint: check whether unitree_sdk2_python is installed.', file=sys.stderr)
        return 1

    os.makedirs(args.save_dir, exist_ok=True)

    try:
        ChannelFactoryInitialize(args.domain_id, args.network_interface)

        client = VideoClient()
        client.SetTimeout(args.timeout_sec)
        client.Init()

        ret = client.GetImageSample()

        if isinstance(ret, tuple):
            code = ret[0]
            image_data = ret[1]
        else:
            code = 0
            image_data = ret

        if code != 0:
            print(f'GetImageSample failed. code={code}', file=sys.stderr)
            return 1

        if image_data is None or len(image_data) == 0:
            print('GetImageSample returned empty image data.', file=sys.stderr)
            return 1

        image_path = make_image_path(args.save_dir)

        with open(image_path, 'wb') as f:
            f.write(bytes(image_data))

        print(f'IMG_PATH={image_path}')
        return 0

    except Exception as e:
        print(f'capture exception: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
