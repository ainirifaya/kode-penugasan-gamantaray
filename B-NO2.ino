#include <Adafruit_LiquidCrystal.h> // library lcd

// pin
const int PIN_UP    = 2;
const int PIN_DOWN  = 3;
const int PIN_MOTOR = 5;      // pin PWM (~)
// PWM = Pulse Width Modulatiom

const int MAX_LEVEL = 10;                  // level 0 - 10
const unsigned long DEBOUNCE   = 50;       // ms
const unsigned long HOLD_DELAY = 400;      // ms sebelum diulang lagi
const unsigned long HOLD_RATE  = 150;      // ms antar repeat saat ditahan

Adafruit_LiquidCrystal lcd(0);

int level = 0;

// Data tombol: indeks 0 = UP, indeks 1 = DOWN
const int btnPin[2] = {PIN_UP, PIN_DOWN};
bool lastState[2] = {HIGH, HIGH};
unsigned long lastChange[2] = {0, 0};
unsigned long lastRepeat[2] = {0, 0};
bool held[2] = {false, false};

bool isTriggered(int i) {
  bool state = digitalRead(btnPin[i]); // tombol ditekan/ditahan atau tidak
  unsigned long now = millis(); // mencatat waktu sejak arduino dinyalakan (milidetik)

  // mengecek debounce dari button
  // jika status tombol berubah dan jeda waktunya lebih lama dari 50ms, maka perubahannya akan disimpan
  if (state != lastState[i] && now - lastChange[i] > DEBOUNCE) {
    lastChange[i] = now;
    lastState[i] = state;
    if (state == LOW) {
      lastRepeat[i] = now;
      held[i] = false;
      return true;
    }
  }

  // jika tombolnya ditekan lama, kecepatan motornya akan meningkat. 400ms pertama kali di tahan. 150ms untuk selanjutnya.
  if (lastState[i] == LOW) {
    unsigned long wait = held[i] ? HOLD_RATE : HOLD_DELAY;
    if (now - lastRepeat[i] >= wait) {
      lastRepeat[i] = now;
      held[i] = true;
      return true;
    }
  }
  return false;
}

void applyMotor() {
  analogWrite(PIN_MOTOR, map(level, 0, MAX_LEVEL, 0, 255)); // mengubah level 0-10 ke 0-255
}

void updateDisplay() {
  int pwm = map(level, 0, MAX_LEVEL, 0, 255); 

  // Serial Monitor
  Serial.print("PWM: ");
  Serial.println(pwm);

  // Baris 1: nilai PWM
  char line[17]; 
  snprintf(line, sizeof(line), "PWM: %-3d        ", pwm); // %-3d diratakan ke kiri sebanyak 3 digit
  lcd.setCursor(0, 0); // kolom pertama, baris pertama
  lcd.print(line);

  lcd.setCursor(0, 1); // baris kedua
  lcd.print("                "); // dikosongkan
}

void setup() {
  Serial.begin(9600);

  pinMode(PIN_UP, INPUT_PULLUP);
  pinMode(PIN_DOWN, INPUT_PULLUP);
  pinMode(PIN_MOTOR, OUTPUT);

  lcd.begin(16, 2); // lcd 16 kolom & 2 baris
  lcd.setBacklight(1);

  applyMotor();
  updateDisplay();
}

void loop() {
  bool changed = false;

  // untuk mengecek apakah tombol up ditekan dan kecepatan motornya masih di bawah maksimal
  if (isTriggered(0) && level < MAX_LEVEL) { 
    level++;
    changed = true;
  }
  // untuk mengecek apakah tombol down ditekan dan kecepatan motornya masih di atas 0
  if (isTriggered(1) && level > 0) {
    level--;
    changed = true;
  }

  if (changed) { // jika ada perubahan
    applyMotor();
    updateDisplay();
  }
}
