import cv2 # untuk memproses video
import numpy as np # untuk operasi matematika/array

# video
INPUT_VIDEO = "/home/ainirifaya/penugasan gamantaray/VIDEO.mp4"
OUTPUT_VIDEO = "hasil_video.mp4"

TARGET_W = 640            # lebar proses agar ringan
ROI_TOP = 0.18            # hapus 18% bagian atas (langit/pohon)
MIN_AREA = 80             # luas minimum blob
MIN_CIRCULARITY = 0.50    # filter kebulatan
ASPECT_RANGE = (0.6, 2.0) # aspect ratio bounding box
WATER_MIN = 0.50          # min. proporsi air (biru) di sekitar blob hijau
MAX_SLOPE = 0.30          # maks. kemiringan garis merah-hijau (dy/dx), lebih dari ini dianggap vertikal/background

# nilai HSV awal (sampling merah & hijau), dipakai sebagai posisi awal slider trackbar
HSV = {
    "R1_Hlo": 0,   "R1_Hhi": 10,
    "R2_Hlo": 160, "R2_Hhi": 179,  # maksimal H di OpenCV 179 (180 sama saja hasilnya)
    "R_Smin": 100, "R_Vmin": 60,
    "G_Hlo": 35,   "G_Hhi": 95,   # 95 supaya bola hijau tosca gelap ikut tertangkap
    "G_Smin": 40,  "G_Vmin": 30,
    "B_Hlo": 85,   "B_Hhi": 130,  # rentang warna air kolam
    "B_Smin": 40,  "B_Vmin": 40,
}

# buat elips 5x5, nantinya untuk membersihkan noise
KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)) 

# nama window yang berisi slider trackbar
JENDELA = "Trackbar HSV"

# membuat window baru berisi slider untuk tiap nilai HSV
def buat_trackbar():
    cv2.namedWindow(JENDELA, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(JENDELA, 420, 500)
    for nama, nilai in HSV.items():
        maks = 179 if "_H" in nama else 255  # H: 0-179, S dan V: 0-255
        cv2.createTrackbar(nama, JENDELA, min(nilai, maks), maks, lambda v: None)

# membaca posisi slider saat ini (dipanggil tiap frame)
def baca_trackbar():
    return {nama: cv2.getTrackbarPos(nama, JENDELA) for nama in HSV}

# masking untuk menyaring piksel berdasarkan rentang warna HSV dari trackbar
def buat_mask(hsv):
    p = baca_trackbar()
    merah = cv2.bitwise_or(
        cv2.inRange(hsv, (p["R1_Hlo"], p["R_Smin"], p["R_Vmin"]), (p["R1_Hhi"], 255, 255)),
        cv2.inRange(hsv, (p["R2_Hlo"], p["R_Smin"], p["R_Vmin"]), (p["R2_Hhi"], 255, 255))
    )
    hijau = cv2.inRange(hsv, (p["G_Hlo"], p["G_Smin"], p["G_Vmin"]), (p["G_Hhi"], 255, 255))
    air = cv2.inRange(hsv, (p["B_Hlo"], p["B_Smin"], p["B_Vmin"]), (p["B_Hhi"], 255, 255))
    return merah, hijau, air

# menghilangkan area langit/pohon
# membersihkan titik-titik noise
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

        # khusus untuk bola hijau, program memeriksa area di sekitar objek (sisi kiri, kanan, dan bawahnya)
        # Jika di sekitarnya terdapat air (warna biru), maka objek tersebut valid berada di area kolam
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

    # buka window trackbar
    buat_trackbar()

    print("Memproses video... Tekan 'q' pada jendela preview untuk berhenti.")

    # membaca video frame demi frame, mengubah ukuran, memberikan efek blur,
    # mengonversinya ke ruang warna HSV, membuat masker warna, dan membersihkannya
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

        # gambar bounding box merah & hijau
        for lst, warna, label in ((merah, (0, 0, 255), "Merah"), (hijau, (0, 255, 0), "Hijau")):
            for x, y, bw, bh, cx, cy in lst:
                cv2.rectangle(frame, (x, y), (x + bw, y + bh), warna, 2)
                cv2.putText(frame, label, (x, max(y - 5, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, warna, 1)

        # cari bola terdekat 
        near_m = max(merah, key=lambda b: b[5]) if merah else None
        # hanya bola hijau yang garisnya ke bola merah horizontal (bukan vertikal/background)
        hijau_sejajar = [b for b in hijau
                         if near_m and abs(b[5] - near_m[5]) <= abs(b[4] - near_m[4]) * MAX_SLOPE]
        near_h = max(hijau_sejajar, key=lambda b: b[5]) if hijau_sejajar else None

        # gambar garis antara bola kanan & kiri serta titik tengahnya
        if near_m and near_h:
            # garis penghubung
            cv2.line(frame, (near_m[4], near_m[5]), (near_h[4], near_h[5]), (255, 255, 0), 2)
            
            # titik tengah target
            target_x = (near_m[4] + near_h[4]) // 2
            target_y = (near_m[5] + near_h[5]) // 2
            cv2.circle(frame, (target_x, target_y), 6, (0, 255, 255), -1)

        # simpan ke file output video
        out.write(frame)

        # preview tampilan
        cv2.imshow("Hasil Deteksi Video", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Selesai! Hasil video berhasil disimpan di {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
