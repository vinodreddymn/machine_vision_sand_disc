import cv2
import numpy as np
import random
import math
# =========================================================
# VIDEO CONFIGURATION
# =========================================================

WIDTH = 1280
HEIGHT = 720
FPS = 30
TOTAL_FRAMES = 1500

BELT_SPEED = 5

OUTPUT_VIDEO = "industrial_disk_inspection.mp4"

video = cv2.VideoWriter(
    OUTPUT_VIDEO,
    cv2.VideoWriter_fourcc(*'mp4v'),
    FPS,
    (WIDTH, HEIGHT)
)

# =========================================================
# DISC STORAGE
# =========================================================

discs = []

# =========================================================
# CAMERA EFFECTS
# =========================================================

def add_camera_noise(frame):

    # Very low industrial CMOS noise

    noise = np.random.normal(
        0,
        0.35,
        frame.shape
    ).astype(np.int16)

    noisy = frame.astype(np.int16) + noise

    noisy = np.clip(noisy, 0, 255)

    return noisy.astype(np.uint8)


def add_motion_blur(frame):

    kernel_size = 3

    kernel = np.zeros((kernel_size, kernel_size))

    kernel[int((kernel_size - 1) / 2), :] = np.ones(kernel_size)

    kernel = kernel / kernel_size

    return cv2.filter2D(frame, -1, kernel)

# =========================================================
# DRAW SANDING DISC
# =========================================================

def draw_disc(frame, x, y, radius, defective=False):

    height, width = frame.shape[:2]

    # -------------------------------------------------
    # REALISTIC SHADOW
    # -------------------------------------------------

    shadow = np.zeros_like(frame)

    cv2.circle(
        shadow,
        (x + 8, y + 8),
        radius,
        (0, 0, 0),
        -1
    )

    shadow = cv2.GaussianBlur(shadow, (31, 31), 15)

    frame[:] = cv2.addWeighted(
        frame,
        1.0,
        shadow,
        0.22,
        0
    )

    # -------------------------------------------------
    # DISC BASE COLOR
    # -------------------------------------------------

    base_color = np.array([55, 65, 105], dtype=np.uint8)

    cv2.circle(
        frame,
        (x, y),
        radius,
        base_color.tolist(),
        -1
    )

    # -------------------------------------------------
    # ABRASIVE TEXTURE
    # -------------------------------------------------

    for _ in range(radius * 70):

        angle = random.uniform(0, 2 * math.pi)

        r = random.uniform(0, radius)

        tx = int(x + r * math.cos(angle))
        ty = int(y + r * math.sin(angle))

        if (
            0 <= tx < width and
            0 <= ty < height
        ):

            variation = random.randint(-18, 18)

            color = (
                int(np.clip(55 + variation, 0, 255)),
                int(np.clip(65 + variation, 0, 255)),
                int(np.clip(105 + variation, 0, 255))
            )

            frame[ty, tx] = color

    # -------------------------------------------------
    # FIBER GRAIN EFFECT
    # -------------------------------------------------

    for _ in range(radius * 10):

        angle = random.uniform(0, 180)

        length = random.randint(4, 10)

        sx = random.randint(x - radius, x + radius)
        sy = random.randint(y - radius, y + radius)

        ex = int(sx + length * math.cos(math.radians(angle)))
        ey = int(sy + length * math.sin(math.radians(angle)))

        if (
            (sx - x) ** 2 + (sy - y) ** 2
        ) <= radius ** 2:

            cv2.line(
                frame,
                (sx, sy),
                (ex, ey),
                (45, 55, 90),
                1
            )

    # -------------------------------------------------
    # SOFT EDGE
    # -------------------------------------------------

    cv2.circle(
        frame,
        (x, y),
        radius,
        (40, 45, 70),
        2
    )

    # -------------------------------------------------
    # 8 HOLE PATTERN
    # -------------------------------------------------

    hole_radius = radius // 10

    hole_distance = int(radius * 0.48)

    holes = []

    for i in range(8):

        theta = math.radians(i * 45 - 90)

        hx = int(x + hole_distance * math.cos(theta))
        hy = int(y + hole_distance * math.sin(theta))

        holes.append((hx, hy))

    for hx, hy in holes:

        if defective and random.random() < 0.15:

            # imperfect hole

            axes = (
                hole_radius + random.randint(-2, 5),
                hole_radius + random.randint(-2, 5)
            )

            cv2.ellipse(
                frame,
                (hx, hy),
                axes,
                random.randint(0, 180),
                0,
                360,
                (12, 12, 12),
                -1
            )

        else:

            cv2.circle(
                frame,
                (hx, hy),
                hole_radius,
                (10, 10, 10),
                -1
            )

        # subtle inner highlight

        cv2.circle(
            frame,
            (hx - 1, hy - 1),
            hole_radius - 2,
            (22, 22, 22),
            1
        )

    # -------------------------------------------------
    # DEFECTS
    # -------------------------------------------------

    if defective:

        # edge tear

        cv2.ellipse(
            frame,
            (x + radius - 12, y),
            (14, 8),
            random.randint(0, 180),
            0,
            360,
            (20, 20, 20),
            -1
        )

        # scratch

        cv2.line(
            frame,
            (x - radius // 3, y - 12),
            (x + radius // 3, y + 8),
            (30, 30, 30),
            2
        )

        # discoloration

        overlay = frame.copy()

        cv2.circle(
            overlay,
            (x + 15, y + 10),
            18,
            (40, 50, 70),
            -1
        )

        frame[:] = cv2.addWeighted(
            overlay,
            0.25,
            frame,
            0.75,
            0
        )


# =========================================================
# MAIN LOOP
# =========================================================

belt_animation = 0

for frame_no in range(TOTAL_FRAMES):

    # -----------------------------------------------------
    # CONVEYOR BACKGROUND
    # -----------------------------------------------------

    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    frame[:] = (18, 18, 18)
    for yline in range(0, HEIGHT, 6):

        intensity = random.randint(16, 24)

        cv2.line(
            frame,
            (0, yline),
            (WIDTH, yline),
            (intensity, intensity, intensity),
            1
        )

    # -----------------------------------------------------
    # MOVING BELT TEXTURE
    # -----------------------------------------------------

    belt_animation += BELT_SPEED

    for y in range(0, HEIGHT, 24):

        shift = belt_animation % 50

        cv2.line(
            frame,
            (-shift, y),
            (WIDTH, y),
            (36, 36, 36),
            1
        )




    # -----------------------------------------------------
    # DRAW DISCS
    # -----------------------------------------------------

    updated_discs = []

    for disc in discs:

        x, y, radius, defective = disc

        vibration = random.randint(-2, 2)

        draw_disc(
            frame,
            x,
            y + vibration,
            radius,
            defective
        )

        x += BELT_SPEED

        if x < WIDTH + radius:

            updated_discs.append(
                (
                    x,
                    y,
                    radius,
                    defective
                )
            )

    discs = updated_discs

    # -----------------------------------------------------
    # ADD NEW DISCS
    # -----------------------------------------------------

    if frame_no % 70 == 0:

        y = 360 + random.randint(-5, 5)

        radius = random.randint(90, 110)

        defective = random.random() < 0.08

        allow_new = True

        if len(discs) > 0:

            last_disc = discs[-1]

            if last_disc[0] < 300:

                allow_new = False

        if allow_new:

            discs.append(
                (
                    -radius - 20,
                    y,
                    radius,
                    defective
                )
            )

    # -----------------------------------------------------
    # CAMERA EFFECTS
    # -----------------------------------------------------

    frame = add_camera_noise(frame)

    frame = add_motion_blur(frame)

    # -----------------------------------------------------
    # INDUSTRIAL LIGHTING
    # -----------------------------------------------------
    # INDUSTRIAL LIGHTING
    # -----------------------------------------------------

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (0, 0),
        (WIDTH, HEIGHT),
        (8, 8, 8),
        -1
    )

    frame = cv2.addWeighted(
        overlay,
        0.18,
        frame,
        0.82,
        0
    )

    # top inspection light

    light = np.zeros_like(frame)

    cv2.ellipse(
        light,
        (WIDTH // 2, HEIGHT // 3),
        (500, 180),
        0,
        0,
        360,
        (30, 30, 30),
        -1
    )

    light = cv2.GaussianBlur(light, (151, 151), 80)

    frame = cv2.addWeighted(
        frame,
        1.0,
        light,
        0.28,
        0
    )

    # -----------------------------------------------------
    # WRITE FRAME
    # -----------------------------------------------------

    video.write(frame)

# =========================================================
# RELEASE VIDEO
# =========================================================

video.release()

print()
print("VIDEO GENERATED SUCCESSFULLY")
print(f"OUTPUT FILE : {OUTPUT_VIDEO}")
print()