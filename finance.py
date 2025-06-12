import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Liste des actifs
tickers = ['^FCHI', 'BTC-USD', '^GSPC', '^IXIC', '^DJI']
names = {
    '^FCHI': 'CAC 40',
    'BTC-USD': 'Bitcoin',
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ',
    '^DJI': 'Dow Jones'
}

# Récupération des données de 2011 (arrivée de Bitcoin) à aujourd'hui
data = yf.download(tickers, start='2011-01-01', end='2025-06-01')['Adj Close']

# Base 100 pour toutes les séries
perf_indexed = data / data.iloc[0] * 100

# Tracer le graphique
plt.figure(figsize=(14, 7))
for ticker in tickers:
    plt.plot(perf_indexed[ticker], label=f"{names[ticker]}")

plt.title("Performance cumulée des actifs financiers (base 100)")
plt.xlabel("Date")
plt.ylabel("Performance (base 100)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("performance_cumulee.png", dpi=300)  # Enregistrement en image
plt.show()
