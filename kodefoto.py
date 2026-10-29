import cv2
import numpy as np

# BACA FOTO ASLI
path_foto = '/home/ainirifaya/Downloads/FOTO.jpg' # SESUAIKAN DENGAN NAMA FILE FOTO KAMU
img = cv2.imread(path_foto)

if img is None:
    print("Foto tidak ditemukan! Pastikan nama file benar.")
    exit()

# 1. Resize agar ringan
h_ori, w_ori = img.shape[:2]
target_w = 640
img = cv2.resize(img, (target_w, int(h_ori * target_w / w_ori)))
h, w = img.shape[:2]

# 2. ROI - Buang 20% bagian atas (pohon/pemandangan)
roi_y_start = int(h * 0.20)
roi = img[roi_y_start:h, 0:w]

# 3. Blur & Konversi ke HSV
blurred = cv2.GaussianBlur(roi, (5, 5), 0)
hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

# --- 4. RENTANG HSV ---
# Masker Merah
lower_red1, upper_red1 = np.array([0, 100, 80]), np.array([10, 255, 255])
lower_red2, upper_red2 = np.array([160, 100, 80]), np.array([180, 255, 255])
mask_red = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1), cv2.inRange(hsv, lower_red2, upper_red2))

# Masker Hijau
lower_green, upper_green = np.array([40, 40, 30]), np.array([90, 255, 255])
mask_green = cv2.inRange(hsv, lower_green, upper_green)

# Clean Noise
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)

# --- 5. DETEKSI BOLA & GAMBAR Bounding Box ---
def deteksi_bola(mask, warna_box, label, img_target):
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if area > 150:
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0: continue
            
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            
            if circularity > 0.35:
                x, y, bw, bh = cv2.boundingRect(cnt)
                real_y = y + roi_y_start
                
                # Gambar Kotak & Label Nama Saja
                cv2.rectangle(img_target, (x, real_y), (x + bw, real_y + bh), warna_box, 2)
                cv2.putText(img_target, label, (x, real_y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, warna_box, 2)

deteksi_bola(mask_red, (0, 0, 255), "Merah", img)
deteksi_bola(mask_green, (0, 255, 0), "Hijau", img)

# Simpan hasil foto
cv2.imwrite('hasil_foto.jpg', img)

# Tampilkan Hasil
while True:
    cv2.imshow('Hasil Deteksi Foto', img)
    key = cv2.waitKey(1) & 0xFF
    if key == 27 or cv2.getWindowProperty('Hasil Deteksi Foto', cv2.WND_PROP_VISIBLE) < 1:
        break

cv2.destroyAllWindows()
print("Hasil foto berhasil disimpan sebagai 'hasil_foto.jpg'")
