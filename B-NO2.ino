#include <Adafruit_LiquidCrystal.h>

// Kontrol kecepatan motor DC: 2 push button + LCD I2C
// UP = D2, DOWN = D3 (INPUT_PULLUP), motor lewat TIP120 di D5 (PWM)

// ====== Konfigurasi ======
const int PIN_UP    = 2;
const int PIN_DOWN  = 3;
const int PIN_MOTOR = 5;      // harus pin PWM (~)

const int MAX_LEVEL = 10;                  // level 0 - 10
const unsigned long DEBOUNCE   = 50;       // ms
const unsigned long HOLD_DELAY = 400;      // ms sebelum auto-repeat
const unsigned long HOLD_RATE  = 150;      // ms antar repeat saat ditahan

// LCD I2C Tinkercad (MCP23008, alamat 0x20 -> parameter 0)
Adafruit_LiquidCrystal lcd(0);

// ====== State ======
int level = 0;

// Data tombol: indeks 0 = UP, indeks 1 = DOWN
const int btnPin[2] = {PIN_UP, PIN_DOWN};
bool lastState[2] = {HIGH, HIGH};
unsigned long lastChange[2] = {0, 0};
unsigned long lastRepeat[2] = {0, 0};
bool held[2] = {false, false};

// True saat tombol ditekan, atau saat ditahan lalu repeat
bool isTriggered(int i) {
  bool state = digitalRead(btnPin[i]);
  unsigned long now = millis();

  if (state != lastState[i] && now - lastChange[i] > DEBOUNCE) {
    lastChange[i] = now;
    lastState[i] = state;
    if (state == LOW) {
      lastRepeat[i] = now;
      held[i] = false;
      return true;
    }
  }

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
  analogWrite(PIN_MOTOR, map(level, 0, MAX_LEVEL, 0, 255));
}

void updateDisplay() {
  int pwm = map(level, 0, MAX_LEVEL, 0, 255);

  // Serial Monitor
  Serial.print("PWM: ");
  Serial.println(pwm);

  // Baris 1: nilai PWM
  char line[17];
  snprintf(line, sizeof(line), "PWM: %-3d        ", pwm);
  lcd.setCursor(0, 0);
  lcd.print(line);

  // Baris 2: Dikosongkan (menghapus bar level PPPP----)
  lcd.setCursor(0, 1);
  lcd.print("                ");
}

void setup() {
  Serial.begin(9600);

  pinMode(PIN_UP, INPUT_PULLUP);
  pinMode(PIN_DOWN, INPUT_PULLUP);
  pinMode(PIN_MOTOR, OUTPUT);

  lcd.begin(16, 2);
  lcd.setBacklight(1);

  applyMotor();
  updateDisplay();
}

void loop() {
  bool changed = false;

  if (isTriggered(0) && level < MAX_LEVEL) {
    level++;
    changed = true;
  }
  if (isTriggered(1) && level > 0) {
    level--;
    changed = true;
  }

  if (changed) {
    applyMotor();
    updateDisplay();
  }
}
