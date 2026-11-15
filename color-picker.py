"""Camera color detector + mouse Color Picker.

Run: python main.py
Mouse left click: pick a pixel color; C: clear; S: screenshot; Q: quit.
"""

from collections import Counter
from datetime import datetime

import cv2


# cv2 uses BGR: (blue, green, red), not RGB.
COLOR_BGR = {
    "RED": (0, 0, 255),
    "ORANGE": (0, 165, 255),
    "YELLOW": (0, 255, 255),
    "GREEN": (0, 200, 0),
    "CYAN": (255, 255, 0),
    "BLUE": (255, 0, 0),
    "PURPLE": (160, 50, 160),
    "PINK": (180, 105, 255),
    "BROWN": (42, 42, 165),
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "GRAY": (128, 128, 128),
}


def detect_color(h, s, v):
    """Guess a basic color name from OpenCV HSV values."""
    if v < 50:
        return "BLACK"
    if s < 45:
        return "WHITE" if v >= 200 else "GRAY"
    if 8 <= h < 26 and s >= 65 and 50 <= v < 160:
        return "BROWN"
    if h < 9 or h >= 170:
        return "RED"
    if h < 21:
        return "ORANGE"
    if h < 36:
        return "YELLOW"
    if h < 85:
        return "GREEN"
    if h < 100:
        return "CYAN"
    if h < 131:
        return "BLUE"
    if h < 150:
        return "PURPLE"
    return "PINK"


def analyze_region(region):
    """Find the most common color name in the central square."""
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    names = []
    for row in hsv[::6, ::6]:
        for h, s, v in row:
            names.append(detect_color(int(h), int(s), int(v)))

    color, count = Counter(names).most_common(1)[0]
    percent = count / len(names) * 100
    center_hsv = tuple(int(x) for x in hsv[hsv.shape[0] // 2, hsv.shape[1] // 2])
    return color, percent, center_hsv


def pick_color(event, x, y, flags, state):
    """Read the clicked pixel from the ORIGINAL camera frame."""
    if event != cv2.EVENT_LBUTTONDOWN:
        return

    frame = state["frame"]
    if frame is None:
        return

    height, width = frame.shape[:2]
    if not (0 <= x < width and 0 <= y < height):
        return

    # Frame uses BGR. UI and HEX use RGB.
    b, g, r = (int(channel) for channel in frame[y, x])
    hsv_pixel = cv2.cvtColor(frame[y:y+1, x:x+1], cv2.COLOR_BGR2HSV)[0, 0]
    h, s, v = (int(channel) for channel in hsv_pixel)

    state["picked"] = {
        "x": x,
        "y": y,
        "name": detect_color(h, s, v),
        "rgb": (r, g, b),
        "hex": f"#{r:02X}{g:02X}{b:02X}",
        "hsv": (h, s, v),
        "bgr": (b, g, r),
    }
    print("Picked:", state["picked"]["name"], state["picked"]["hex"])


def draw_text(frame, text, xy, scale=0.55):
    cv2.putText(frame, text, xy, cv2.FONT_HERSHEY_SIMPLEX, scale,
                (255, 255, 255), 2, cv2.LINE_AA)


def main():
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Camera neegdsen gui. Windows Camera privacy settings-aa shalga.")
        return

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # The mouse callback and video loop share this dictionary.
    state = {"frame": None, "picked": None}
    window_name = "Color Detector + Color Picker"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(window_name, pick_color, state)

    print("CLICK = color pick | C = clear | S = save | Q = quit")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("Camera-aas zurag unshij chadsangui.")
                break

            frame = cv2.flip(frame, 1)
            state["frame"] = frame.copy()  # raw image, WITHOUT text or boxes
            display = frame.copy()          # draw only on this image
            height, width = frame.shape[:2]

            # Existing feature: recognize the dominant central color.
            side = max(1, min(height, width) // 4)
            x1, y1 = (width - side) // 2, (height - side) // 2
            x2, y2 = x1 + side, y1 + side
            color, percent, (h, s, v) = analyze_region(frame[y1:y2, x1:x2])

            cv2.rectangle(display, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.rectangle(display, (0, 0), (width, 110), (35, 35, 35), -1)
            draw_text(display, "COLOR DETECTOR + PICKER", (12, 28), 0.65)
            draw_text(display, f"CENTER: {color} ({percent:.0f}% area)", (12, 60))
            draw_text(display, f"CENTER HSV: H={h} S={s} V={v}", (12, 89), 0.48)
            cv2.rectangle(display, (width - 65, 45), (width - 15, 95),
                          COLOR_BGR[color], -1)

            # New feature: show the selected pixel color at the bottom.
            panel_top = max(110, height - 130)
            cv2.rectangle(display, (0, panel_top), (width, height), (35, 35, 35), -1)
            picked = state["picked"]
            if picked is None:
                draw_text(display, "CLICK ANY PIXEL TO PICK A COLOR", (12, panel_top + 30))
                draw_text(display, "S: save   C: clear   Q: quit", (12, height - 14), 0.46)
            else:
                draw_text(display, f"PICKED: {picked['name']}", (12, panel_top + 28), 0.65)
                r, g, b = picked["rgb"]
                draw_text(display, f"RGB: ({r}, {g}, {b})", (12, panel_top + 57))
                draw_text(display, f"HEX: {picked['hex']}", (12, panel_top + 83))
                draw_text(display, "S: save   C: clear   Q: quit", (12, height - 12), 0.44)
                cv2.rectangle(display, (width - 90, panel_top + 16),
                              (width - 15, panel_top + 91), picked["bgr"], -1)
                cv2.circle(display, (picked["x"], picked["y"]), 7,
                           (255, 255, 255), 2)

            cv2.imshow(window_name, display)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("c"):
                state["picked"] = None
            if key == ord("s"):
                filename = datetime.now().strftime("color_%Y%m%d_%H%M%S_%f.png")
                cv2.imwrite(filename, display)
                print("Zurag hadgallaa:", filename)
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
