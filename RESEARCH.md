# Home Assistant IP Camera Integration Research

Copyright (c) 2026, Silas Mariusz Grzybacz

## 1. Architektura Integracji (Platforma)
Zgodnie z dokumentacją `creating_platform_index`, integracja powinna komunikować się z urządzeniem poprzez zewnętrzną bibliotekę Python lub dedykowany moduł API. W Home Assistant tworzymy platformę `camera` (plik `camera.py`), która dziedziczy po `homeassistant.components.camera.Camera`.

## 2. Encja Kamery (`camera.py`)
Klasa kamery musi implementować:
- **Właściwości:** `brand`, `model`, `is_on`, `is_recording`, `is_streaming`, `motion_detection_enabled`.
- **Funkcje (Supported Features):** `CameraEntityFeature.ON_OFF`, `CameraEntityFeature.STREAM`.
- **Metody:**
  - `async_camera_image()`: Zwraca klatkę obrazu (snapshot) w postaci bajtów. Zazwyczaj pobierana przez HTTP API kamery.
  - `stream_source()`: Zwraca adres URL strumienia (np. RTSP), który jest używany przez komponent `stream` i `ffmpeg` w HA.
  - `async_turn_on()`, `async_turn_off()`: Włączanie/wyłączanie kamery.
  - `async_enable_motion_detection()`, `async_disable_motion_detection()`: Sterowanie detekcją ruchu.

## 3. Konfiguracja (Config Entries)
Zgodnie z `config_entries_index`, integracja musi wspierać konfigurację przez UI (Config Flow).
- Plik `config_flow.py` definiuje kroki konfiguracji (podanie IP, portu, loginu, hasła).
- W `__init__.py` implementujemy `async_setup_entry` i `async_unload_entry`, by zarządzać cyklem życia integracji.

## 4. Zdarzenia i Automatyzacje (`device_automation_trigger`)
Dla zdarzeń takich jak "Motion detection", "Human detection", "LPR" (rozpoznawanie tablic), używamy `device_trigger.py`.
- Definiujemy `TRIGGER_SCHEMA` dla różnych typów zdarzeń.
- Kiedy kamera zgłosi zdarzenie (np. przez Webhook lub polling API), integracja emituje zdarzenie na szynę (Event Bus), co wyzwala automatyzacje.

## 5. Media i Nagrania (Research)
Referencyjne integracje (np. Reolink, ONVIF, Synology):
- **Zdarzenia (Camera Events):** Często oparte na subskrypcji zdarzeń (np. ONVIF PullPoint) lub Webhookach konfigurowanych w kamerze.
- **Przeglądanie nagrań:** Realizowane poprzez integrację z komponentem `media_source`. Integracja rejestruje się jako źródło mediów i pozwala na przeglądanie plików wideo zapisanych na karcie SD kamery poprzez wywołania API.
- **Wiele strumieni:** Kamery często oferują strumień główny (wysoka jakość) i pomocniczy (niższa jakość). Integracja może tworzyć osobną encję kamery dla każdego strumienia lub pozwalać na wybór w opcjach integracji.

## Podsumowanie Planu dla MERX Horizon:
1. **API Client:** Klasa do komunikacji z API MERX (logowanie, pobieranie snapshotów, pobieranie URL RTSP, nasłuchiwanie zdarzeń).
2. **Config Flow:** Formularz do wpisania IP, portu (HTTP/RTSP), loginu i hasła.
3. **Camera Platform:** Encja kamery serwująca snapshoty i strumień RTSP.
4. **Binary Sensors:** Encje dla detekcji ruchu (odświeżane na podstawie zdarzeń z kamery).
5. **Device Triggers:** Wyzwalacze dla zaawansowanych zdarzeń (LPR, detekcja twarzy).
