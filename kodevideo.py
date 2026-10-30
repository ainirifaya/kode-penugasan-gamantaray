import cv2
import numpy as np

# ===================== PATH FILE =====================
INPUT_VIDEO = "/home/ainirifaya/Downloads/VIDEO.mp4"
OUTPUT_VIDEO = "hasil_video.mp4"

# ===================== KONFIGURASI =====================
TARGET_W = 640            # Lebar proses agar ringan
ROI_TOP = 0.18            # Buang 18% bagian atas (langit/pohon)
MIN_AREA = 80             # Luas minimum blob
MIN_CIRCULARITY = 0.50    # Filter kebulatan
ASPECT_RANGE = (0.6, 2.0) # Aspect ratio bounding box
WATER_MIN = 0.50          # Min. proporsi air (biru) di sekitar blob hijau
MAX_SLOPE = 0.30          # Maks. kemiringan garis merah-hijau (dy/dx), lebih dari ini = vertikal = background

# Nilai HSV (sampling merah & hijau)
HSV = {
    "R1_Hlo": 0,   "R1_Hhi": 10,
    "R2_Hlo": 160, "R2_Hhi": 180,
    "R_Smin": 100, "R_Vmin": 60,
    "G_Hlo": 35,   "G_Hhi": 95,   # [DIUBAH] sebelumnya 90, supaya bola hijau tosca gelap ikut tertangkap
    "G_Smin": 40,  "G_Vmin": 30,
    "B_Hlo": 85,   "B_Hhi": 130,  # rentang warna air kolam
    "B_Smin": 40,  "B_Vmin": 40,
}

KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

def buat_mask(hsv):
    p = HSV
    merah = cv2.bitwise_or(
        cv2.inRange(hsv, (p["R1_Hlo"], p["R_Smin"], p["R_Vmin"]), (p["R1_Hhi"], 255, 255)),
        cv2.inRange(hsv, (p["R2_Hlo"], p["R_Smin"], p["R_Vmin"]), (p["R2_Hhi"], 255, 255))
    )
    hijau = cv2.inRange(hsv, (p["G_Hlo"], p["G_Smin"], p["G_Vmin"]), (p["G_Hhi"], 255, 255))
    air = cv2.inRange(hsv, (p["B_Hlo"], p["B_Smin"], p["B_Vmin"]), (p["B_Hhi"], 255, 255))
    return merah, hijau, air

def bersihkan(mask, roi_y):
    mask[:roi_y, :] = 0
    mask = cv2.medianBlur(mask, 5)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, KERNEL, iterations=2)
    return mask

def deteksi_bola(mask, air=None):  # air hanya dipakai untuk bola hijau
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hasil = []
    for cnt in cnts:
        area = cv2.contourArea(cnt)
        if area < MIN_AREA:
            continue
        per = cv2.arcLength(cnt, True)
        if per == 0:
            continue
        circ = 4 * np.pi * area / (per * per)
        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = bw / float(bh)
        if circ < MIN_CIRCULARITY or not (ASPECT_RANGE[0] < aspect < ASPECT_RANGE[1]):
            continue

        # [DIUBAH] Bola hijau lolos jika air ada di kiri-kanan ATAU di bawahnya (bola di tepi kolam
        # kiri-kanannya tembok/keramik, tapi bawahnya tetap air). Tembok/pohon tidak punya air di keduanya.
        if air is not None:
            H, W = air.shape
            pad = max(8, max(bw, bh))
            kiri = air[y:y + bh, max(x - pad, 0):x]
            kanan = air[y:y + bh, x + bw:min(x + bw + pad, W)]
            bawah = air[min(y + bh, H):min(y + bh + pad, H), max(x - bw, 0):min(x + 2 * bw, W)]
            total = kiri.size + kanan.size
            sisi_ok = total > 0 and (cv2.countNonZero(kiri) + cv2.countNonZero(kanan)) / float(total) >= WATER_MIN
            bawah_ok = bawah.size > 0 and cv2.countNonZero(bawah) / float(bawah.size) >= WATER_MIN
            if not (sisi_ok or bawah_ok):
                continue

        hasil.append((x, y, bw, bh, x + bw // 2, y + bh // 2))
    return hasil

def main():
    cap = cv2.VideoCapture(INPUT_VIDEO)
    if not cap.isOpened():
        print(f"Gagal membuka video dari path: {INPUT_VIDEO}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    target_h = int(height * TARGET_W / width)
    roi_y = int(target_h * ROI_TOP)

    # Video Writer untuk menyimpan hasil
    out = cv2.VideoWriter(OUTPUT_VIDEO, cv2.VideoWriter_fourcc(*"mp4v"), fps, (TARGET_W, target_h))

    print("Memproses video... Tekan 'q' pada jendela preview untuk berhenti.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (TARGET_W, target_h), interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (5, 5), 0), cv2.COLOR_BGR2HSV)
        
        m_merah, m_hijau, m_air = buat_mask(hsv)
        m_merah = bersihkan(m_merah, roi_y)
        m_hijau = bersihkan(m_hijau, roi_y)
        m_air = cv2.medianBlur(m_air, 5)  # rapikan mask air

        merah = deteksi_bola(m_merah)
        hijau = deteksi_bola(m_hijau, m_air)

        # 1. Gambar Bounding Box Merah & Hijau
        for lst, warna, label in ((merah, (0, 0, 255), "Merah"), (hijau, (0, 255, 0), "Hijau")):
            for x, y, bw, bh, cx, cy in lst:
                cv2.rectangle(frame, (x, y), (x + bw, y + bh), warna, 2)
                cv2.putText(frame, label, (x, max(y - 5, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, warna, 1)

        # 2. Cari bola terdekat (posisi Y paling bawah)
        near_m = max(merah, key=lambda b: b[5]) if merah else None
        # Hanya bola hijau yang garisnya ke bola merah horizontal (bukan vertikal/background)
        hijau_sejajar = [b for b in hijau
                         if near_m and abs(b[5] - near_m[5]) <= abs(b[4] - near_m[4]) * MAX_SLOPE]
        near_h = max(hijau_sejajar, key=lambda b: b[5]) if hijau_sejajar else None

        # 3. Gambar garis antara bola kanan & kiri serta titik tengahnya
        if near_m and near_h:
            # Garis penghubung
            cv2.line(frame, (near_m[4], near_m[5]), (near_h[4], near_h[5]), (255, 255, 0), 2)
            
            # Titik tengah target
            target_x = (near_m[4] + near_h[4]) // 2
            target_y = (near_m[5] + near_h[5]) // 2
            cv2.circle(frame, (target_x, target_y), 6, (0, 255, 255), -1)

        # Simpan ke file output video
        out.write(frame)

        # Preview tampilan
        cv2.imshow("Hasil Deteksi Video", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Selesai! Hasil video berhasil disimpan di {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
