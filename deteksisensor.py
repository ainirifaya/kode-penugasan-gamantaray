import cv2
from ultralytics import YOLO

# Path menuju file best.pt hasil training kamu
model_path = 'runs/detect/train-2/weights/best.pt'
model = YOLO(model_path)

# Pengaturan filter supaya yang bukan sensor tidak ikut terdeteksi
CONF_THRESHOLD = 0.60     # confidence minimum untuk kotak ukuran normal/besar
CONF_SMALL = 0.35         # [BARU] confidence minimum khusus kotak kecil (sensor jauh, confidence-nya memang rendah)
SMALL_AREA = 0.02         # [BARU] kotak dengan luas <= 2% layar dianggap kecil/jauh
MAX_BOX_AREA = 0.15       # Kotak yang menutupi > 15% layar dianggap bukan sensor (wajah/badan)
FACE_IOU = 0.30           # [BARU] kotak yang menumpuk dengan wajah (IoU > 0.30) dibuang
MIN_FRAMES = 2            # cukup 2 frame berturut-turut baru ditampilkan
IMGSZ = 960               # ukuran inferensi lebih besar supaya sensor kecil/jauh lebih mudah terdeteksi

# [BARU] Detektor wajah bawaan OpenCV, hanya untuk membuang deteksi sensor palsu di wajah
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def iou(a, b):  # [BARU]
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0

# Buka webcam (0 untuk webcam bawaan laptop/USB)
cap = cv2.VideoCapture(0)

print("Membuka kamera... Tekan 'q' pada jendela video untuk keluar.")

frame_berturut = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Gagal mengambil frame dari kamera.")
        break

    # Mirror kamera (dibalik horizontal)
    frame = cv2.flip(frame, 1)

    # Jalankan inferensi deteksi objek
    results = model(frame, conf=CONF_SMALL, imgsz=IMGSZ)  # [DIUBAH] conf dasar dibuat rendah, disaring lagi di bawah
    r = results[0]

    # [BARU] Cari posisi wajah di frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    wajah = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
    wajah_box = [(x, y, x + w, y + h) for x, y, w, h in wajah]

    # [DIUBAH] Saring kotak: ukuran, confidence sesuai ukuran, dan bukan wajah
    keep = []
    if len(r.boxes) > 0:
        wh = (r.boxes.xywhn[:, 2] * r.boxes.xywhn[:, 3]).tolist()
        for i, area in enumerate(wh):
            conf = float(r.boxes.conf[i])
            box = r.boxes.xyxy[i].tolist()
            if area > MAX_BOX_AREA:
                continue
            if conf < (CONF_SMALL if area <= SMALL_AREA else CONF_THRESHOLD):
                continue
            if any(iou(box, w) > FACE_IOU for w in wajah_box):
                continue
            keep.append(i)

    # One at a time: hanya ambil satu sensor dengan confidence tertinggi
    if keep:
        keep = [max(keep, key=lambda i: float(r.boxes.conf[i]))]

    # Hitung berapa frame berturut-turut sensor terdeteksi
    frame_berturut = frame_berturut + 1 if keep else 0

    # Gambar kotak bounding box & label kelas hanya jika sensor benar-benar ada
    if frame_berturut >= MIN_FRAMES:
        annotated_frame = r[keep].plot()
    else:
        annotated_frame = frame

    # Tampilkan di jendela OpenCV
    cv2.imshow("Testing Live Detection - YOLOv8", annotated_frame)

    # Tekan tombol 'q' di keyboard untuk menutup
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
