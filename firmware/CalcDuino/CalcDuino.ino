#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

const int BUZZER_PIN = 8;
const int LED_PIN    = 9;
enum BlinkState { BLINK_IDLE, BLINK_ON, BLINK_OFF };

BlinkState blinkState   = BLINK_IDLE;
int blinkRemain  = 0;      
unsigned long blinkTime = 0;       
const unsigned long BLINK_ON_MS  = 150;
const unsigned long BLINK_OFF_MS = 150;

String inputLine = "";

String truncate(String s, int maxLen) {
  if ((int)s.length() > maxLen) {
    return s.substring(0, maxLen - 1) + "~"; 
  }
  return s;
}

void processLine(String line) {

  if (line.startsWith("B:")) {
    int count = line.substring(2).toInt();
    if (count <= 0) return;          
    if (count > 20) count = 20;      

    tone(BUZZER_PIN, 1000, 100);

    blinkRemain = count;
    blinkState  = BLINK_ON;
    blinkTime   = millis();
    digitalWrite(LED_PIN, HIGH);

    return;
  }

  if (line.startsWith("D:")) {
    String data = line.substring(2);
    lcd.clear();

    int eqIdx = data.lastIndexOf('=');
    if (eqIdx != -1) {
      String expr   = truncate(data.substring(0, eqIdx), 16);
      String result = truncate(data.substring(eqIdx + 1), 16);
      lcd.setCursor(0, 0);
      lcd.print(expr);
      lcd.setCursor(0, 1);
      lcd.print(result);
    } else {
      lcd.setCursor(0, 0);
      lcd.print(truncate(data, 16));
    }
    Serial.println("DONE");
    return;
  }
  Serial.println("DONE");
}

void setup() {
  Serial.begin(9600);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  lcd.begin(16, 2);
  lcd.print("Ready...");

  Serial.println("DONE");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      inputLine.trim();
      if (inputLine.length() > 0) {
        processLine(inputLine);
      }
      inputLine = "";
    } else if (c != '\r') {
      inputLine += c;
    }
  }

  unsigned long now = millis();

  if (blinkState == BLINK_ON && (now - blinkTime >= BLINK_ON_MS)) {
    digitalWrite(LED_PIN, LOW);
    blinkTime  = now;
    blinkState = BLINK_OFF;
  }
  else if (blinkState == BLINK_OFF && (now - blinkTime >= BLINK_OFF_MS)) {
    blinkRemain--;
    if (blinkRemain <= 0) {
      blinkState = BLINK_IDLE;
      Serial.println("DONE");    
    } else {
      digitalWrite(LED_PIN, HIGH);
      blinkTime  = now;
      blinkState = BLINK_ON;
    }
  }
}
