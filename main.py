import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

def load_data(path):
    data = []
    with open(path) as file:
        data = [int(line.strip()) for line in file]
    return data

def convert_to_h_m_s(starting_time, data):
    time_data = []
    current_time = datetime.strptime(starting_time, "%H:%M:%S")
    for t in data:
        current_time += timedelta(milliseconds=t)
        # Formatujemy czas z dwucyfrową precyzją mikrosekund
        formatted_time = f"{current_time.strftime('%H:%M:%S')}.{current_time.microsecond // 10000:02}"
        time_data.append(formatted_time)
    return time_data

def plot_data(data, x, starting_time):
    y = []
    current_time = datetime.strptime(starting_time, "%H:%M:%S")

    # Przeliczamy punkty osi X do formatu czasowego z milisekundami
    x_time_data = []
    for t in x:
        time_point = current_time + timedelta(milliseconds=t)
        formatted_time = f"{time_point.strftime('%H:%M:%S')}.{time_point.microsecond // 10000:02}"
        x_time_data.append(formatted_time)

    # Tworzymy wartości dla osi Y w zależności od obecności czasu w `data`
    for time_point in x_time_data:
        if time_point in data:
            y.append(1)
        else:
            y.append(0)

    # Rysujemy wykres
    plt.figure(figsize=(12, 6))
    plt.plot(x_time_data, y, label="Dane czasowe", marker='o')
    plt.xlabel("Czas (HH:MM:SS)")
    plt.ylabel("Dane (1 = obecny, 0 = brak)")
    plt.title("Wykres danych czasowych")

    # Obracamy etykiety na osi X dla lepszej czytelności
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()
    plt.show()

# Przykładowe dane
starting_time = "16:53:21"
p1_data = load_data("dane1.txt")
d = convert_to_h_m_s(starting_time, p1_data)

# Tworzymy argumenty x z odpowiednią precyzją
x = np.linspace(0, max(p1_data), len(p1_data))
plot_data(d, x, starting_time)
