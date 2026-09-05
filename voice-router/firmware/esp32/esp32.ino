/* 语音路由的硬件端。ESP32 / Arduino 都能跑。
 *
 * 串口收一行 JSON，形如 {"intent":"light","args":{"state":"on"}}，
 * 执行完回一行 {"ok":true,"intent":"light"}。
 *
 * 依赖：ArduinoJson（库管理器里装）。
 * 灯带：把 USE_NEOPIXEL 打开，再装 Adafruit NeoPixel。
 */

#include <ArduinoJson.h>

#define LED_PIN 2          // 大多数 ESP32 开发板的板载灯
// #define USE_NEOPIXEL
#ifdef USE_NEOPIXEL
#include <Adafruit_NeoPixel.h>
#define STRIP_PIN 5
#define STRIP_LEN 30
Adafruit_NeoPixel strip(STRIP_LEN, STRIP_PIN, NEO_GRB + NEO_KHZ800);
#endif

static String line;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
#ifdef USE_NEOPIXEL
  strip.begin();
  strip.show();
#endif
  Serial.println("{\"ready\":true}");
}

uint32_t colorByName(const char* name) {
  if (!name) return 0xFFFFFF;
  String n = String(name); n.toLowerCase();
  if (n == "red")    return 0xFF0000;
  if (n == "green")  return 0x00FF00;
  if (n == "blue")   return 0x0000FF;
  if (n == "yellow") return 0xFFFF00;
  if (n == "purple") return 0x800080;
  if (n == "orange") return 0xFF8000;
  if (n == "warm")   return 0xFFB060;
  return 0xFFFFFF;
}

void handleLight(JsonObject args) {
  const char* state = args["state"] | "on";
  bool on = String(state) != "off";
  digitalWrite(LED_PIN, on ? HIGH : LOW);
#ifdef USE_NEOPIXEL
  int level = args["level"] | 100;
  uint32_t c = on ? colorByName(args["color"] | "warm") : 0;
  strip.setBrightness(map(constrain(level, 0, 100), 0, 100, 0, 255));
  for (int i = 0; i < STRIP_LEN; i++) strip.setPixelColor(i, c);
  strip.show();
#endif
}

void handleMode(JsonObject args) {
  const char* name = args["name"] | "";
  // 模式就是预设的灯光组合，按需加
  if (String(name) == "night") { digitalWrite(LED_PIN, LOW); }
  else                         { digitalWrite(LED_PIN, HIGH); }
}

void handle(const String& s) {
  StaticJsonDocument<512> doc;
  if (deserializeJson(doc, s)) {
    Serial.println("{\"ok\":false,\"error\":\"bad json\"}");
    return;
  }
  const char* intent = doc["intent"] | "";
  JsonObject args = doc["args"].as<JsonObject>();

  if      (String(intent) == "light") handleLight(args);
  else if (String(intent) == "mode")  handleMode(args);
  else {
    Serial.printf("{\"ok\":false,\"intent\":\"%s\",\"error\":\"unknown intent\"}\n", intent);
    return;
  }
  Serial.printf("{\"ok\":true,\"intent\":\"%s\"}\n", intent);
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') { line.trim(); if (line.length()) handle(line); line = ""; }
    else if (line.length() < 500) line += c;
  }
}
