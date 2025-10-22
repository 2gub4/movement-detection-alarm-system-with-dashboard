# alarm-system-with-pin-disarming-and-dashboard

## Opis projektu
Projekt realizuje działanie systemu alarmowego z detekcją ruchu. Zdudowany jest na platformie Raspberry Pi 4b+ w języku Python z serwerem Flask. 
Serwer służy do komunikacji z dashboardem będącym aplikacją web'ową stworzoną w HTML, JavaScript i CSS przy pomocy narzędzia Bootsrap.
Sterowanie odbywa się poprzez ręczne ustawianie, uzbrajanie i rozbrajanie kodem PIN, a szczegółowe informacje dostępne są przez wspomniany dashboard po połączeniu z serwerem. Korzysta z programowania asynchronicznego.

Realizowany na potrzeby projektu studenckiego - 2 rok - Informatyka Stosowana
---

## Technologie
- Biblioteki:
  - RPi.GPIO - obsługa Pinów, sterowanie komponentami
  - threading - asynchroniczne działanie i komunikacja kluczowych funkcji
  - Flask - serwer obsługujący dashboard
  - tm1637 - sterowanie komponentem o tożsamej nazwie - wyświetlanie aktualnej konfiguracji pinu
  - mailer - wysyłanie monitu o potencjalnym włamaniu na maila
- Bootstap 5 - frontend dashboard'u

---

## Funkcjonalności
- **RCWL-0516** - mikrofalowy czujnik Dopplera, odpowiedzialny za detekcję ruchu
- **HCSR-04** - regulacja zasięgu czujnika Dopplera, mierzenie odległości do ruchomego obiektu
- klawiatura membranowa 4x3:
   - ustawianie pinu
   - uzbrajanie i rozbrajanie detektora
   - przerywanie alarmu i odliczania
- **TM1637** + diody LED:
   - wyświetlanie zmian przy PINie na panelu
   - proste animacje sygnalizujące zdarzenia
- Flask:
   - obsługa dashboardu
   - tworzenie logów o próbach wprowadznia PINu
   - pobieranie pliku log.txt
   - status systemu
- Bootstrap:
   - wizualny aspekt aplikacji webowej   
   - obsługa ciemnego i jansnego motywu
   - wyświetlanie ilości odwiedzeń
   - różnokolorowe podświetlenie przycisków
- alarm w przypadku 3-krotnego wprowadzenia błędnego PINu lub upływu czasu
- sygnalizacja dźwiękowa

---

## Aspekty programowania asynchronicznego
Z biblioteki zaimportowano obiekty Thread, Event i Lock, by usprawnić równoległe funkcjonowanie kluczowych funkcji oraz zapewnić komunikację i dostęp do komponentów.
- Thread - tworzenie wątków czerpiących z funkcji by umożliwić np. jednoczesne odliczanie do alarmu i walidację PINu, mającą na celu jego przerwanie
-  Event - tworzenie dwustanowych flag służących do komunikacji i sterowania wątkami
-  Lock - zarządanie dostępem do ekranu tm1632, tak by wyświetlane z różnych funkcji informacje nie nachodziły na siebie

---

## Sprzęt
- Raspberry Pi 4b+
- TM1632
- diody LED 2x
- klawiatura membranowa 4x3
- RCWL-0516
- HC-SR04
- buzzer pasywny KY-006

---

## Schemat struktury plików
<img width="499" height="472" alt="schemat" src="https://github.com/user-attachments/assets/390527c1-da0d-4bed-a294-3b7e889a981a" />

## Schemat połączeń

![e0dd9675-cee9-4b02-9b4f-687b96b7323b](https://github.com/user-attachments/assets/5d30b374-6c1a-40c8-960a-a7334515ed83)

---

## Autorzy:
- Jakub Sosna (2gub4) - kod Python, hardware
- Kamil Skorupski ([K3mYk](https://github.com/K3mYk)) - serwer Flask, dashboard, hardware

  
