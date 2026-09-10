/*
  AI-based E-Waste Smart Glove — Firmware
  ----------------------------------------
  Reads temperature & humidity from an HTU21D-F sensor, displays live
  readings on an OLED screen, triggers a buzzer on unsafe thresholds,
  and publishes sensor data to Adafruit IO over MQTT for downstream
  SHAP/LIME-based explainable AI analysis.

  Board: DFRobot Beetle ESP32-C6 Mini

  SETUP:
  1. Copy "config.example.h" to "config.h"
  2. Fill in your WiFi and Adafruit IO credentials in config.h
  3. config.h is git-ignored — your credentials will never be committed
*/

#include <Wire.h>
#include <WiFi.h>
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <Adafruit_HTU21DF.h>
#include "config.h"   // WiFi + Adafruit IO credentials (not committed to git)

// ---------------- OLED display pins (DOIT ESP32 DevKit V1) ----------------
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

#define OLED_MOSI  23   // GPIO23 (D7)
#define OLED_CLK   18   // GPIO18 (D5)
#define OLED_DC    4    // GPIO4 (D4)
#define OLED_CS    5    // GPIO5 (D1)
#define OLED_RESET 2    // GPIO2 (D2)

#define BUZZER_PIN  33  // GPIO33

// ---------------- Safety thresholds ----------------
#define TEMP_THRESHOLD_C   29.0
#define HUMIDITY_THRESHOLD 80.0

// ---------------- Instantiate display and sensor objects ----------------
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT,
  OLED_MOSI, OLED_CLK, OLED_DC, OLED_RESET, OLED_CS);

Adafruit_HTU21DF htu = Adafruit_HTU21DF();

// ---------------- WiFi and MQTT clients ----------------
WiFiClient client;
Adafruit_MQTT_Client mqtt(&client, AIO_SERVER, AIO_SERVERPORT, AIO_USERNAME, AIO_KEY);

// ---------------- MQTT feeds ----------------
Adafruit_MQTT_Publish temperatureFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/temperature");
Adafruit_MQTT_Publish humidityFeed = Adafruit_MQTT_Publish(&mqtt, AIO_USERNAME "/feeds/humidity");

// ---------------- MQTT connect function ----------------
void MQTT_connect() {
  int8_t ret;

  if (mqtt.connected()) {
    return;
  }

  Serial.print("Connecting to MQTT... ");
  while ((ret = mqtt.connect()) != 0) {
    Serial.println(mqtt.connectErrorString(ret));
    Serial.println("Retrying MQTT connection in 5 seconds...");
    mqtt.disconnect();
    delay(5000);
  }
  Serial.println("MQTT Connected!");
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting...");

  WiFi.begin(WLAN_SSID, WLAN_PASS);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi connected.");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  Wire.begin(21, 22);  // I2C pins for HTU21DF

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  if (!htu.begin()) {
    Serial.println("Couldn't find HTU21D sensor!");
    while (1);
  }

  if (!display.begin(SSD1306_SWITCHCAPVCC)) {
    Serial.println(F("SSD1306 allocation failed"));
    while (1);
  }

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("HTU21D Sensor Ready");
  display.display();
  delay(10000);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    WiFi.disconnect();
    WiFi.begin(WLAN_SSID, WLAN_PASS);
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
    }
    Serial.println("\nWiFi connected.");
  }

  MQTT_connect();

  float temp = htu.readTemperature();
  float hum = htu.readHumidity();

  Serial.print("Temperature: ");
  Serial.print(temp, 2);
  Serial.print(" C, Humidity: ");
  Serial.print(hum, 2);
  Serial.println(" %");

  if (!temperatureFeed.publish(temp)) {
    Serial.println("Failed to publish temperature");
  } else {
    Serial.println("Temperature published");
  }

  if (!humidityFeed.publish(hum)) {
    Serial.println("Failed to publish humidity");
  } else {
    Serial.println("Humidity published");
  }

  display.clearDisplay();
  display.setCursor(0, 0);

  display.print("Temp: ");
  display.print(temp, 2);
  display.println(" C");

  display.print("Humidity: ");
  display.print(hum, 2);
  display.println(" %");

  display.display();

  // Buzzer control based on safety thresholds
  if (temp > TEMP_THRESHOLD_C || hum > HUMIDITY_THRESHOLD) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }

  delay(10000);
}
