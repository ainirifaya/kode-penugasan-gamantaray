#include <Servo.h>

// Servo yang sudut putarnya mengikuti jarak dari sensor ultrasonik HC-SR04
// Makin jauh objek, makin besar sudut servo (2 cm = 0 derajat, 200 cm = 180 derajat)

// ====== Pin sesuai rangkaian ======
const int pinTrig  = 2;   // TRIG (kabel kuning)
const int pinEcho  = 3;   // ECHO (kabel biru)
const int pinServo = 9;   // Sinyal servo (kabel oranye)

// ====== Konfigurasi ======
const int JARAK_MIN = 2;      // cm
const int JARAK_MAX = 200;    // cm
const int JUMLAH_SAMPEL = 5;  // rata-rata beberapa pembacaan agar stabil

Servo myServo;
int sudutTerakhir = 0;

// Baca jarak sekali dalam cm, return -1 kalau tidak ada pantulan
long bacaJarak() {
  digitalWrite(pinTrig, LOW);
  delayMicroseconds(2);
  digitalWrite(pinTrig, HIGH);
  delayMicroseconds(10);
  digitalWrite(pinTrig, LOW);

  long durasi = pulseIn(pinEcho, HIGH, 30000);  // timeout 30 ms
  if (durasi == 0) return -1;

  return durasi * 0.034 / 2;
}

void setup() {
  Serial.begin(9600);

  pinMode(pinTrig, OUTPUT);
  pinMode(pinEcho, INPUT);

  myServo.attach(pinServo);
  myServo.write(0);
}

void loop() {
  // Rata-rata beberapa pembacaan
  long total = 0;
  int valid = 0;
  for (int i = 0; i < JUMLAH_SAMPEL; i++) {
    long d = bacaJarak();
    if (d > 0) {
      total += d;
      valid++;
    }
    delay(10);
  }

  if (valid > 0) {
    int jarak = total / valid;
    jarak = constrain(jarak, JARAK_MIN, JARAK_MAX);

    // Ubah jarak (2-200 cm) menjadi sudut servo (0-180 derajat)
    sudutTerakhir = map(jarak, JARAK_MIN, JARAK_MAX, 0, 180);
    myServo.write(sudutTerakhir);

    Serial.print("Jarak: ");
    Serial.print(jarak);
    Serial.print(" cm | Sudut Servo: ");
    Serial.print(sudutTerakhir);
    Serial.println(" derajat");
  } else {
    Serial.println("Tidak ada objek terdeteksi");
  }

  delay(50);
}
