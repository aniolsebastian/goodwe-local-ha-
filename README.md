# GoodWe Local – Home Assistant

Lokalne (bez chmury SEMS) monitorowanie i sterowanie inwerterem GoodWe, z harmonogramem ładowania i rozładowania baterii.

## Funkcje
- Wszystkie sensory runtime inwertera (moc PV, sieć, bateria, SOC, energia)
- Tryb pracy, limit eksportu do sieci, DoD baterii
- Harmonogram: 4 przedziały czasowe (także przez północ), dla każdego akcja (ładowanie / rozładowanie / wyłączony), moc w % mocy znamionowej i docelowy SOC
- Sensor „Status harmonogramu”, ustawienia zapisywane trwale
- **Wszystkie parametry inwertera**: automatycznie wykrywane przy starcie (zależnie od modelu i firmware), widoczne jako encje „Ustawienie: …” (domyślnie wyłączone – włącz potrzebne w ustawieniach urządzenia)
- Przyciski: synchronizacja zegara inwertera, odświeżenie danych
- Usługi: `goodwe_local.read_setting`, `write_setting`, `list_settings`, `set_operation_mode`, `sync_time`

## Edycja parametrów
Domyślnie parametry są **tylko do odczytu**. Aby je edytować: Ustawienia → Urządzenia i usługi → GoodWe Local → **Konfiguruj** → zaznacz „Pozwól edytować wszystkie parametry”. Parametry liczbowe staną się edytowalne; złożone (np. grupy eco_mode, czasy) pozostają do odczytu – zapiszesz je usługą `write_setting`.

> ⚠️ Niektóre parametry dotyczą zabezpieczeń sieciowych (napięcia, częstotliwości) i baterii. Błędna wartość może wyłączyć inwerter lub naruszyć warunki przyłączenia OSD. Zmieniaj tylko to, co rozumiesz.

Przykład:
```yaml
action: goodwe_local.write_setting
data:
  setting: grid_export_limit
  value: 3000
```

## Instalacja
**HACS:** HACS → Integracje → ⋮ → Własne repozytoria → dodaj URL repozytorium (kategoria: Integration) → zainstaluj → restart HA.

**Ręcznie:** skopiuj `custom_components/goodwe_local` do `config/custom_components/` i zrestartuj HA.

Następnie: Ustawienia → Urządzenia i usługi → Dodaj integrację → **GoodWe Local**, podaj IP inwertera i port (8899 UDP lub 502 Modbus TCP).

> Usuń wbudowaną integrację GoodWe – inwerter źle obsługuje równoległe połączenia.

## Jak działa harmonogram
Co 30 s integracja sprawdza aktywny przedział i tylko przy zmianie wysyła polecenie:
- ładowanie → `ECO_CHARGE` (moc %, docelowy SOC)
- rozładowanie → `ECO_DISCHARGE` (moc %, minimalny SOC)
- poza przedziałami / po wyłączeniu harmonogramu → `GENERAL` (autokonsumpcja)

## Uwagi
- Moc jest w % mocy znamionowej; limity BMS mają pierwszeństwo.
- Nie zmieniaj trybu ręcznie / w SEMS przy aktywnym harmonogramie.
- Gdy HA nie działa, inwerter pozostaje w ostatnim trybie.
- Serie DT/SDT (bez baterii) nie obsługują harmonogramu.

Bazuje na bibliotece [goodwe](https://github.com/marcelblijleven/goodwe). Licencja MIT. Wersja 1.1.0.
