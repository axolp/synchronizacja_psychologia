
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
from bisect import bisect_left
from scipy.signal import correlate
from scipy.stats import pearsonr  # Korelacja Pearsona


def read_file(path):
    ticks= []
    with open(path) as file:
        ticks= [int(line.strip("\n")) for line in file]
    #print(ticks)
    return ticks

def convert_ms_to_hmsms(milliseconds):
    # Obliczenie godzin, minut, sekund i milisekund
    hours = milliseconds // (3600 * 1000)
    minutes = (milliseconds % (3600 * 1000)) // (60 * 1000)
    seconds = (milliseconds % (60 * 1000)) // 1000
    ms = milliseconds % 1000
    
    # Formatowanie jako string w formacie "HH:MM:SS.mmm"
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}.{ms:03}"
    return formatted_time

def convert_hmsms_to_ms(hmsms):
    # Podzielenie czasu na części: godziny, minuty, oraz sekundy.milisekundy
    hours, minutes, seconds_ms = hmsms.split(":")
    
    # Rozdzielenie sekundy i milisekundy
    seconds, ms = map(int, seconds_ms.split("."))
    hours = int(hours)
    minutes = int(minutes)
    
    # Obliczenie całkowitego czasu w milisekundach
    milliseconds = (hours * 3600 * 1000) + (minutes * 60 * 1000) + (seconds * 1000) + ms
    return milliseconds


class measure_device:

    def make_ticks(self, path):
        return read_file(path)
    
    def make_ticks_ms_and_ticks_hmsms(self, ticks, starting_time):

        ticks_ms= []
        ticks_hmsms= []

        s= convert_hmsms_to_ms(starting_time)
        for t in ticks:
            s+= t 
            s= round(s/100)*100
            ticks_ms.append(s)
            ticks_hmsms.append(convert_ms_to_hmsms(s))
        return ticks_ms, ticks_hmsms
    
    def __init__(self, owner, starting_time, file_path):
        self.owner= owner
        self.ticks= self.make_ticks(file_path)
        self.ticks_ms, self.ticks_hmsms = self.make_ticks_ms_and_ticks_hmsms(self.ticks , starting_time)
        
def is_tick_present(tick_list, value):
        # Wyszukiwanie binarne sprawdzające obecność `value` w posortowanej liście `tick_list`
        idx = bisect_left(tick_list, value)
        return idx < len(tick_list) and tick_list[idx] == value

def plot_measurements(device1, device2):
    # Wyznaczenie wspólnego zakresu czasu
    start_time = max(device1.ticks_ms[0], device2.ticks_ms[0])
    end_time = min(device1.ticks_ms[-1], device2.ticks_ms[-1])
    
    # Generowanie równomiernych wartości czasu od start_time do end_time
    arguments = np.arange(start_time, start_time + (1000*60*0.5), 100)
    
    # Listy domen (1 gdy urządzenie miało tick w danym czasie, 0 w przeciwnym wypadku)
    device1_domain = []
    device2_domain = []
    
    # Wypełnienie list domen z użyciem wyszukiwania binarnego
    for t in arguments:
        device1_domain.append(1 if is_tick_present(device1.ticks_ms, t) else 0)
        device2_domain.append(1 if is_tick_present(device2.ticks_ms, t) else 0)
    
    # Rysowanie wykresu
    plt.figure(figsize=(12, 6))
    
    # Wykres dla urządzenia 1
    plt.plot(arguments, device1_domain, label=f"{device1.owner}", marker='o', linestyle='-')
    
    # Wykres dla urządzenia 2
    plt.plot(arguments, device2_domain, label=f"{device2.owner}", marker='x', linestyle='-')

    # Konwersja etykiet osi X na format HH:MM:SS.mmm
    tick_labels = [convert_ms_to_hmsms(int(t)) for t in plt.gca().get_xticks()]
    plt.gca().set_xticklabels(tick_labels, rotation=45, ha="right")

    # Ustawienia osi, tytułu i legendy
    plt.xlabel("Time (HH:MM:SS.mmm)")
    plt.ylabel("Tick Presence (1=Tick, 0=No Tick)")
    plt.title("Comparison of Tick Measurements Over Time for Two Devices")
    plt.legend()
    plt.grid(True)
    
    # Wyświetlenie wykresu
    plt.show()

def plot_rolling_correlation(device1, device2, window_ms=60000, step_ms=100):
    """
    Funkcja oblicza korelację między tickami dwóch urządzeń dla kolejnych okien 15-sekundowych
    i rysuje wykres korelacji oraz ticków dla obu pacjentów w funkcji czasu.
    
    Parametry:
    - device1, device2: obiekty klasy measure_device
    - window_ms: długość okna w ms (domyślnie 15 sekund = 15000 ms)
    - step_ms: krok przesunięcia okna w ms (domyślnie 100 ms)
    """
    # Początek i koniec wspólnego zakresu czasu
    start_time = max(device1.ticks_ms[0], device2.ticks_ms[0])
    end_time = min(device1.ticks_ms[-1], device2.ticks_ms[-1])

    # Zakres czasu dla analizy korelacji
    times = np.arange(start_time + window_ms, start_time+(1000*60*15), step_ms)
    correlations = []
    device1_presence = []
    device2_presence = []

    i= 0
    for current_time in times:
        if i % 200 == 0: print(len(times), i)
        # Wybieramy ticki z ostatnich 15 sekund dla obu urządzeń
        window_start = current_time - window_ms
        device1_window = [t for t in device1.ticks_ms if window_start <= t < current_time]
        device2_window = [t for t in device2.ticks_ms if window_start <= t < current_time]

        # Konwertujemy ticki na domeny (0 i 1) w zakresie okna
        common_time = np.arange(window_start, current_time, step_ms)
        device1_domain = np.array([1 if t in device1_window else 0 for t in common_time])
        device2_domain = np.array([1 if t in device2_window else 0 for t in common_time])

        # Obliczamy korelację Pearsona tylko dla bieżącego okna
        if len(device1_domain) > 1 and len(device2_domain) > 1:
            corr, _ = pearsonr(device1_domain, device2_domain)
        else:
            corr = 0  # Jeśli brak wystarczających danych, korelacja wynosi 0

        correlations.append(corr)

        # Dodajemy obecność ticków w czasie jako średnią w oknie, aby uwzględnić ich zagęszczenie
        device1_presence.append(np.mean(device1_domain))
        device2_presence.append(np.mean(device2_domain))
        i+= 1

    # Rysowanie wykresu korelacji w funkcji czasu
    plt.figure(figsize=(12, 8))

    # Wykres korelacji
    plt.plot(times, correlations, label="Correlation (15-second windows)", color='purple', marker='o', linestyle='-')
    
    # Wykresy ticków dla obu urządzeń
    plt.plot(times, device1_presence, label=f"{device1.owner} Tick Presence", color='blue', linestyle='--')
    plt.plot(times, device2_presence, label=f"{device2.owner} Tick Presence", color='red', linestyle='--')
    
    # Konwersja etykiet osi X na format HH:MM:SS.mmm
    tick_labels = [convert_ms_to_hmsms(int(t)) for t in plt.gca().get_xticks()]
    plt.gca().set_xticklabels(tick_labels, rotation=45, ha="right")
    
    # Ustawienia osi, tytułu i legendy
    plt.xlabel("Time (HH:MM:SS.mmm)")
    plt.ylabel("Correlation / Tick Presence")
    plt.title("Correlation and Tick Presence over time (15-second windows)")
    plt.legend()
    plt.grid(True)
    
    # Wyświetlenie wykresu
    plt.show()

def plot_cross_correlation(device1, device2, window_ms=15000, step_ms=100):
    """
    Funkcja oblicza kroskorelację między tickami dwóch urządzeń dla kolejnych okien 15-sekundowych
    i rysuje wykres kroskorelacji w funkcji czasu.
    
    Parametry:
    - device1, device2: obiekty klasy measure_device
    - window_ms: długość okna w ms (domyślnie 15 sekund = 15000 ms)
    - step_ms: krok przesunięcia okna w ms (domyślnie 100 ms)
    """
    # Początek i koniec wspólnego zakresu czasu
    start_time = max(device1.ticks_ms[0], device2.ticks_ms[0])
    end_time = min(device1.ticks_ms[-1], device2.ticks_ms[-1])

    # Zakres czasu dla analizy kroskorelacji
    times = np.arange(start_time + window_ms, start_time + (1000*60*3), step_ms)
    cross_correlations = []

    for current_time in times:
        # Wybieramy ticki z ostatnich 15 sekund dla obu urządzeń
        window_start = current_time - window_ms
        device1_window = [t for t in device1.ticks_ms if window_start <= t < current_time]
        device2_window = [t for t in device2.ticks_ms if window_start <= t < current_time]

        # Konwertujemy ticki na domeny (0 i 1) w zakresie okna
        common_time = np.arange(window_start, current_time, step_ms)
        device1_domain = [1 if t in device1_window else 0 for t in common_time]
        device2_domain = [1 if t in device2_window else 0 for t in common_time]

        # Obliczamy kroskorelację dla bieżącego okna
        if len(device1_domain) > 1 and len(device2_domain) > 1:
            correlation = correlate(device1_domain, device2_domain, mode='valid')
            max_corr = max(correlation)
        else:
            max_corr = 0  # Jeśli nie mamy danych w oknie, ustawiamy korelację na 0

        cross_correlations.append(max_corr)

    # Rysowanie wykresu kroskorelacji w funkcji czasu
    plt.figure(figsize=(12, 6))
    plt.plot(times, cross_correlations, label="Cross-correlation", marker='o', linestyle='-')
    
    # Konwersja etykiet osi X na format HH:MM:SS.mmm
    tick_labels = [convert_ms_to_hmsms(int(t)) for t in plt.gca().get_xticks()]
    plt.gca().set_xticklabels(tick_labels, rotation=45, ha="right")
    
    # Ustawienia osi, tytułu i legendy
    plt.xlabel("Time (HH:MM:SS.mmm)")
    plt.ylabel("Cross-correlation")
    plt.title("Cross-correlation over time (15-second windows)")
    plt.legend()
    plt.grid(True)
    
    # Wyświetlenie wykresu
    plt.show()

def cross_correlation(device1_ticks, device2_ticks):
    """
    Oblicza kroskorelację między dwoma listami ticks_ms i zwraca przesunięcie (lag) oraz wartość korelacji.
    """
    # Ustal wspólny czas od najwcześniejszego do najpóźniejszego ticku
    start_time = max(device1_ticks[0], device2_ticks[0])
    end_time = min(device1_ticks[-1], device2_ticks[-1])

    # Tworzymy wspólną siatkę czasową z dokładnością do 1 ms
    common_time = np.arange(start_time, start_time+(1000*60*1), 100)
    device1_domain = []
    device2_domain = []
    
    # Wypełniamy domeny (1 dla ticku, 0 dla jego braku)
    for t in common_time:
        device1_domain.append(1 if is_tick_present(device1_ticks, t) else 0)
        device2_domain.append(1 if is_tick_present(device2_ticks, t) else 0)

    # Obliczamy kroskorelację między dwoma listami domen
    correlation = correlate(device1_domain, device2_domain, mode="full")
    lag = np.argmax(correlation) - (len(device1_domain) - 1)
    print(lag)
    return lag, correlation

psycholog= measure_device("psycholog", "15:56:42.000", "dane1.txt")
pacjent= measure_device("pacjent", "15:53:57.000", "dane2.txt")

plot_rolling_correlation(psycholog, pacjent)

#print(pacjent.ticks_hmsms)
#plot_measurements(psycholog, pacjent)


# lag, correlation = cross_correlation(psycholog.ticks_ms, pacjent.ticks_ms)

# ##Wynik korelacji i przesunięcia
# print("Przesunięcie (lag):", lag, "ms")
# print("Wartość korelacji:", max(correlation))

# ## Wykres korelacji
# plt.figure(figsize=(10, 5))
# lags = np.arange(-len(psycholog.ticks_ms) + 1, len(pacjent.ticks_ms))
# plt.plot(lags, correlation)
# plt.xlabel("Lag (ms)")
# plt.ylabel("Cross-correlation")
# plt.title("Cross-correlation between Psychologist and Patient Heartbeats")
# plt.grid(True)
# plt.show()















