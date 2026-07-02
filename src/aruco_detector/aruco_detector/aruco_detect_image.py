#!/usr/bin/env python3

import argparse
import glob
import json
import os
import sys
import time

import cv2
import numpy as np


# =============================
# Default settings
# =============================
DEFAULT_IMAGE_DIR = "/home/baram/mission_ws/go2_images"
DEFAULT_OUTPUT_DIR = "/home/baram/mission_ws/aruco_results"
DEFAULT_DICTIONARY = "DICT_4X4_250"


def get_aruco_dict_map():
    return {
        "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
        "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
        "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
        "DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,

        "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
        "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
        "DICT_5X5_250": cv2.aruco.DICT_5X5_250,
        "DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,

        "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
        "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
        "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
        "DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,

        "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
        "DICT_7X7_100": cv2.aruco.DICT_7X7_100,
        "DICT_7X7_250": cv2.aruco.DICT_7X7_250,
        "DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,

        "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
    }


def parse_args():
    aruco_dict_map = get_aruco_dict_map()

    parser = argparse.ArgumentParser(
        description="Detect ArUco markers from a saved image."
    )

    # 이제 --image는 필수가 아님.
    # 입력하지 않으면 DEFAULT_IMAGE_DIR에서 가장 최근 jpg를 자동 선택.
    parser.add_argument(
        "--image",
        default=None,
        help="Input image path. If omitted, latest jpg in DEFAULT_IMAGE_DIR is used."
    )

    parser.add_argument(
        "--image-dir",
        default=DEFAULT_IMAGE_DIR,
        help="Directory to search latest image when --image is omitted."
    )

    parser.add_argument(
        "--dictionary",
        default=DEFAULT_DICTIONARY,
        choices=list(aruco_dict_map.keys()),
        help="ArUco dictionary type"
    )

    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save annotated result image"
    )

    parser.add_argument(
        "--show",
        action="store_true",
        help="Show result image window"
    )

    return parser.parse_args()


def find_latest_image(image_dir):
    patterns = [
        os.path.join(image_dir, "*.jpg"),
        os.path.join(image_dir, "*.jpeg"),
        os.path.join(image_dir, "*.png"),
    ]

    image_files = []
    for pattern in patterns:
        image_files.extend(glob.glob(pattern))

    if not image_files:
        return None

    image_files.sort(key=os.path.getmtime, reverse=True)
    return image_files[0]


def create_aruco_detector(dictionary_name):
    aruco_dict_map = get_aruco_dict_map()

    dictionary = cv2.aruco.getPredefinedDictionary(
        aruco_dict_map[dictionary_name]
    )

    parameters = cv2.aruco.DetectorParameters()

    # =============================
    # ArUco detector tuning
    # Marker size: 8 cm x 8 cm
    # Camera distance: about 50 cm
    # =============================

    # 조명 변화 대응
    parameters.adaptiveThreshWinSizeMin = 3
    parameters.adaptiveThreshWinSizeMax = 45
    parameters.adaptiveThreshWinSizeStep = 4

    # 이미지가 너무 밝은 편이면 10~12 추천
    # 일반 환경이면 7도 가능
    parameters.adaptiveThreshConstant = 10

    # 8 cm 마커를 50 cm 거리에서 보는 경우,
    # 마커가 너무 작지 않기 때문에 min을 과하게 낮추지 않는 게 좋음
    parameters.minMarkerPerimeterRate = 0.03
    parameters.maxMarkerPerimeterRate = 2.0

    # 사각형 후보 판단
    # 비스듬한 각도나 약간의 왜곡을 허용
    parameters.polygonalApproxAccuracyRate = 0.04

    # 마커 후보끼리 너무 가까운 경우 제거 기준
    parameters.minCornerDistanceRate = 0.03
    parameters.minMarkerDistanceRate = 0.05

    # 마커가 화면 가장자리 근처에 있어도 검출 허용
    parameters.minDistanceToBorder = 2

    # 내부 비트 판독 안정화
    parameters.markerBorderBits = 1
    parameters.perspectiveRemovePixelPerCell = 8
    parameters.perspectiveRemoveIgnoredMarginPerCell = 0.13

    # 코너 보정
    parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    parameters.cornerRefinementWinSize = 5
    parameters.cornerRefinementMaxIterations = 30
    parameters.cornerRefinementMinAccuracy = 0.1

    # ID 오인식 방지
    # 인식이 너무 안 되면 0.7까지 올릴 수 있음
    # 잘못된 ID가 나오면 0.4~0.5로 낮추기
    parameters.errorCorrectionRate = 0.6

    # 일반 흑백 ArUco 마커라면 False 유지
    parameters.detectInvertedMarker = False

    if hasattr(cv2.aruco, "ArucoDetector"):
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)

        def detect(gray_image):
            corners, ids, rejected = detector.detectMarkers(gray_image)
            return corners, ids, rejected

        return detect

    def detect(gray_image):
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray_image,
            dictionary,
            parameters=parameters
        )
        return corners, ids, rejected

    return detect


def build_marker_result(marker_id, marker_corners):
    pts = marker_corners.reshape((4, 2)).astype(float)

    top_left = pts[0]
    top_right = pts[1]
    bottom_right = pts[2]
    bottom_left = pts[3]

    center = np.mean(pts, axis=0)

    return {
        "id": int(marker_id),
        "center": {
            "x": float(center[0]),
            "y": float(center[1]),
        },
        "corners": {
            "top_left": {
                "x": float(top_left[0]),
                "y": float(top_left[1]),
            },
            "top_right": {
                "x": float(top_right[0]),
                "y": float(top_right[1]),
            },
            "bottom_right": {
                "x": float(bottom_right[0]),
                "y": float(bottom_right[1]),
            },
            "bottom_left": {
                "x": float(bottom_left[0]),
                "y": float(bottom_left[1]),
            },
        },
    }


def draw_marker_centers(image, markers):
    for marker in markers:
        cx = int(marker["center"]["x"])
        cy = int(marker["center"]["y"])
        marker_id = marker["id"]

        cv2.circle(image, (cx, cy), 5, (0, 0, 255), -1)

        cv2.putText(
            image,
            f"ID:{marker_id}",
            (cx + 8, cy - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )


def make_output_path(output_dir):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(output_dir, f"aruco_result_{timestamp}.jpg")


def main():
    if not hasattr(cv2, "aruco"):
        print("ERROR: cv2.aruco module not found.", file=sys.stderr)
        print("Install opencv-contrib-python or python3-opencv.", file=sys.stderr)
        return 1

    args = parse_args()

    if args.image is None:
        image_path = find_latest_image(args.image_dir)

        if image_path is None:
            print(f"ERROR: no image found in {args.image_dir}", file=sys.stderr)
            return 1

        print(f"[aruco_detector] No image path given.")
        print(f"[aruco_detector] Latest image selected: {image_path}")
    else:
        image_path = args.image

    if not os.path.exists(image_path):
        print(f"ERROR: image not found: {image_path}", file=sys.stderr)
        return 1

    os.makedirs(args.output_dir, exist_ok=True)

    image = cv2.imread(image_path)
    if image is None:
        print(f"ERROR: failed to read image: {image_path}", file=sys.stderr)
        return 1

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    detect = create_aruco_detector(args.dictionary)
    corners, ids, rejected = detect(gray)

    result_image = image.copy()
    markers = []

    if ids is not None and len(ids) > 0:
        cv2.aruco.drawDetectedMarkers(result_image, corners, ids)

        for marker_id, marker_corners in zip(ids.flatten(), corners):
            marker = build_marker_result(marker_id, marker_corners)
            markers.append(marker)

        draw_marker_centers(result_image, markers)

    output_image_path = make_output_path(args.output_dir)
    cv2.imwrite(output_image_path, result_image)

    result = {
        "success": True,
        "input_image": image_path,
        "output_image": output_image_path,
        "dictionary": args.dictionary,
        "marker_count": len(markers),
        "markers": markers,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.show:
        cv2.imshow("aruco_result", result_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
