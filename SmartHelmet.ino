#include <Adafruit_NeoPixel.h>
#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <WebSocketsClient.h>
#include <Hash.h>
#include <Scheduler.h>

#define LED 16
#define DELAY 300
#define NUMPIXELS 9
#define BUZZER 2


Adafruit_NeoPixel pixels(NUMPIXELS, LED, NEO_GRB + NEO_KHZ800);
ESP8266WiFiMulti WiFiMulti;
WebSocketsClient webSocket;

enum Notices {SAFE, WARN, DANGER, INIT};

enum Notices notice;

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {

  switch (type) {
    case WStype_DISCONNECTED:
      Serial.println("Disconnected from notice server");
      notice = INIT;
      break;
    case WStype_CONNECTED: {
        Serial.println("Connected to notice server");
        notice = SAFE;
      }
      break;
    case WStype_TEXT: {
        const size_t capacity = JSON_OBJECT_SIZE(2) + length;
        DynamicJsonDocument doc(capacity);
        DeserializationError error = deserializeJson(doc, payload);
        if (error) {
          Serial.print(F("Received unfamiliar payload\t"));
          Serial.print("Error Code: ");
          Serial.println(error.c_str());
          return;
        }
        int range = doc["range"].as<int>();
        float distance = doc["distance"].as<float>();
        Serial.printf("Range: %d\tDistance: %f\n", range, distance);
        if (range == 1) {
          notice = WARN;
          Serial.println("Mode set to WARN");
        } else if (range == 2) {
          notice = DANGER;
          Serial.println("Mode set to DANGER");

        } else if (range == 0) {
          notice = SAFE;
          Serial.println("Mode set to SAFE");

        }

      }

      break;
    case WStype_BIN:
      Serial.printf("Received binary payload of length %u\n", length);
      hexdump(payload, length);

      break;
  }

}

class WebSocketTask : public Task {
  protected:


    void setup() {

      webSocket.begin(WiFi.gatewayIP().toString(), 9001);

      webSocket.onEvent(webSocketEvent);


      webSocket.setReconnectInterval(2000);
    }
    void loop()  {
      webSocket.loop();
    }
} websocket_task;

class NotifyTask : public Task {
  protected:
    void setup() {
      notice = INIT;
    }

    void loop() {
      switch (notice) {
        case SAFE: {
            pixels.clear();
            digitalWrite(BUZZER, 0);
            break;
          }
        case WARN: {
            bool state = !digitalRead(BUZZER);
            if (state) {
              pixels.fill(pixels.Color(255, 255, 0));
            }
            else {
              pixels.clear();
            }
            digitalWrite(BUZZER, state);
            delay(DELAY);
            break;
          }
        case DANGER: {
            bool state = !digitalRead(BUZZER);
            if (state) {
              pixels.fill(pixels.Color(255, 0, 0));
            }
            else {
              pixels.clear();
            }
            digitalWrite(BUZZER, state);
            delay(DELAY / 4);
            break;
          }
        default: {
            pixels.fill(pixels.Color(0, 0, 255));
            digitalWrite(BUZZER, 0);
            break;
          }

      }
    }


} notify_task;

class MemTask : public Task {
  public:
    void loop() {
      Serial.print("Free Memory: ");
      Serial.print(ESP.getFreeHeap());
      Serial.println(" bytes");

      delay(30000);
    }
} mem_task;



void setup() {
  Serial.begin(115200);

  Serial.setDebugOutput(true);

  Serial.println();
  Serial.println();
  Serial.println();

  for (uint8_t t = 4; t > 0; t--) {
    Serial.printf("[SETUP] BOOT WAIT %d...\n", t);
    Serial.flush();
    delay(1000);
  }
  pixels.begin();
  pinMode(BUZZER, OUTPUT);
  pinMode(LED, OUTPUT);
  WiFiMulti.addAP("MainFrame", "PEgO3Sa6");
  while (WiFiMulti.run() != WL_CONNECTED) {
    delay(100);
  }
  Scheduler.start(&notify_task);

  Scheduler.start(&mem_task);
  Scheduler.start(&websocket_task);

  Scheduler.begin();

}

void loop() {
}
