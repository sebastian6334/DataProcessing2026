import os
import time
import sqlite3
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

DANE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dane")

def p(filename):
    return os.path.join(DANE, filename)


# ── Ćwiczenie 1: Kodowanie znaków ────────────────────────────────────────────

def cwiczenie_1():
    print("\n" + "="*60)
    print("ĆWICZENIE 1: Kodowanie znaków")
    print("="*60)

    print("\n--- 1.1 Wczytanie bez encoding ---")
    try:
        df_utf8 = pd.read_csv(p("pracownicy_utf8.csv"))
        print("pracownicy_utf8.csv wczytany poprawnie (domyślne UTF-8):")
        print(df_utf8.head(3))
    except UnicodeDecodeError as e:
        print(f"pracownicy_utf8.csv → błąd: {e}")

    try:
        df_cp = pd.read_csv(p("pracownicy_cp1250.csv"))
        print("\npracownicy_cp1250.csv wczytany bez encoding:")
        print(df_cp.head(3))
    except UnicodeDecodeError as e:
        print(f"\npracownicy_cp1250.csv → UnicodeDecodeError: {e}")
        print("→ Plik CP1250 nie jest poprawnym UTF-8, więc Python wyrzuca błąd.")

    print("\n--- 1.2 Celowe pomyłki ---")
    try:
        df_cp_as_utf8 = pd.read_csv(p("pracownicy_cp1250.csv"), encoding="utf-8")
        print("CP1250 jako UTF-8 (mojibake):")
        print(df_cp_as_utf8.head(3))
    except UnicodeDecodeError as e:
        print(f"CP1250 jako UTF-8 → UnicodeDecodeError: {e}")
        print("→ Bajty CP1250 nie pasują do UTF-8.")

    try:
        df_utf8_as_cp = pd.read_csv(p("pracownicy_utf8.csv"), encoding="cp1250")
        print("\nUTF-8 jako CP1250 (mojibake — dane zepsute po cichu):")
        print(df_utf8_as_cp.head(3))
    except UnicodeDecodeError as e:
        print(f"\nUTF-8 jako CP1250 → UnicodeDecodeError: {e}")
        print("→ Plik UTF-8 zawiera bajty spoza tablicy CP1250 (np. 0x81),")
        print("  więc dostajemy błąd zamiast cichego mojibake.")

    print("\n--- 1.3 Konwersja CP1250 → UTF-8 ---")
    df_cp_prawidlowy = pd.read_csv(p("pracownicy_cp1250.csv"), encoding="cp1250")
    df_cp_prawidlowy.to_csv(p("pracownicy_utf8_skonwertowany.csv"), encoding="utf-8", index=False)
    print("Plik zapisany: pracownicy_utf8_skonwertowany.csv")
    print(pd.read_csv(p("pracownicy_utf8_skonwertowany.csv")).head(3))


# ── Ćwiczenie 2: Brudny CSV ──────────────────────────────────────────────────

def cwiczenie_2():
    print("\n" + "="*60)
    print("ĆWICZENIE 2: Brudny CSV")
    print("="*60)

    print("\n--- 2.1 Naiwne wczytanie ---")
    try:
        df_naiwny = pd.read_csv(p("klienci.csv"))
        print(df_naiwny.head(3))
    except Exception as e:
        print(f"Błąd: {e}")

    print("\n--- 2.2–2.3 Naprawa ---")
    df = pd.read_csv(
        p("klienci.csv"),
        encoding="cp1250",
        sep=";",
        decimal=",",
        dtype={"kod_pocztowy": str},
        na_values=["brak", "-", "?"],
        parse_dates=["data_rejestracji"],
        dayfirst=True,
    )
    print(df.head())
    print("\nTypy kolumn:")
    print(df.dtypes)

    print("\n--- 2.4 Klienci z Łodzi ---")
    lodz = df[df["miasto"] == "Łódź"]
    print(f"Liczba klientów z Łodzi: {len(lodz)}")
    print(f"Średni dochód (Łódź): {lodz['dochod'].mean():.2f} zł")

    print("\n--- 2.5 Porównanie rozmiarów ---")
    df.to_parquet(p("klienci_czysty.parquet"), index=False)
    rozmiar_csv     = os.path.getsize(p("klienci.csv"))
    rozmiar_parquet = os.path.getsize(p("klienci_czysty.parquet"))
    print(f"CSV:     {rozmiar_csv:>8} bajtów")
    print(f"Parquet: {rozmiar_parquet:>8} bajtów")
    if rozmiar_parquet < rozmiar_csv:
        print(f"Redukcja: {(1 - rozmiar_parquet/rozmiar_csv)*100:.1f}%")
    else:
        print("Uwaga: przy bardzo małych plikach Parquet może być większy niż CSV")
        print("(zysk pojawia się dopiero przy setkach/tysiącach wierszy)")


# ── Ćwiczenie 3: API NBP ─────────────────────────────────────────────────────

def cwiczenie_3():
    print("\n" + "="*60)
    print("ĆWICZENIE 3: Pobieranie danych z API NBP")
    print("="*60)

    BASE = "https://api.nbp.pl/api/exchangerates/rates/A"

    print("\n--- 3.1 Pobieranie EUR/30 dni ---")
    try:
        resp = requests.get(f"{BASE}/EUR/last/30/", timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Brak dostępu do API NBP ({e}).")
        print("Uruchom skrypt na komputerze z dostępem do internetu.")
        return
    data = resp.json()

    print("\n--- 3.2 Struktura odpowiedzi ---")
    print("Klucze:", list(data.keys()))
    print("Waluta:", data["currency"], "| Kod:", data["code"])
    print("Przykładowy rekord:", data["rates"][0])

    print("\n--- 3.3 Tworzenie DataFrame ---")
    df_eur = pd.DataFrame(data["rates"])
    df_eur["effectiveDate"] = pd.to_datetime(df_eur["effectiveDate"])
    df_eur = df_eur.set_index("effectiveDate").rename(columns={"mid": "EUR"})
    print(df_eur.head())

    print("\n--- 3.5 USD i GBP ---")
    waluty = {}
    for kod in ["EUR", "USD", "GBP"]:
        r = requests.get(f"{BASE}/{kod}/last/30/")
        r.raise_for_status()
        d = r.json()
        tmp = pd.DataFrame(d["rates"])
        tmp["effectiveDate"] = pd.to_datetime(tmp["effectiveDate"])
        tmp = tmp.set_index("effectiveDate").rename(columns={"mid": kod})
        waluty[kod] = tmp[kod]

    df_waluty = pd.concat(waluty, axis=1)
    print(df_waluty.tail(5))

    fig, ax = plt.subplots(figsize=(10, 5))
    df_waluty.plot(ax=ax)
    ax.set_title("Kursy EUR, USD, GBP — ostatnie 30 dni (NBP)")
    ax.set_ylabel("PLN")
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(p("kursy_walut.png"), dpi=150)
    print("Wykres zapisany: kursy_walut.png")
    plt.close()

    df_waluty.to_parquet(p("kursy_walut.parquet"))
    print("Dane zapisane: kursy_walut.parquet")

    print("\n--- 3.7 EUR najdroższy w 2024 ---")
    r2024 = requests.get(f"{BASE}/EUR/2024-01-01/2024-12-31/")
    r2024.raise_for_status()
    df_2024 = pd.DataFrame(r2024.json()["rates"])
    df_2024["effectiveDate"] = pd.to_datetime(df_2024["effectiveDate"])
    df_2024 = df_2024.set_index("effectiveDate")
    idx_max = df_2024["mid"].idxmax()
    print(f"Najdroższy EUR w 2024: {idx_max.date()}  →  {df_2024.loc[idx_max, 'mid']:.4f} PLN")


# ── Ćwiczenie 4: Benchmark formatów ──────────────────────────────────────────

def cwiczenie_4():
    print("\n" + "="*60)
    print("ĆWICZENIE 4: Benchmark formatów")
    print("="*60)

    df = pd.read_csv(p("pomiary.csv"), parse_dates=["date"])
    print(f"Wczytano pomiary.csv: {df.shape[0]} wierszy × {df.shape[1]} kolumn")

    print("\n--- 4.2 Zapis ---")
    df.to_json(p("pomiary.json"), orient="records", date_format="iso")
    df.to_parquet(p("pomiary.parquet"), index=False)
    df.to_hdf(p("pomiary.h5"), key="pomiary", mode="w")
    df.to_pickle(p("pomiary.pkl"))
    print("Zapisano: JSON, Parquet, HDF5, Pickle")

    print("\n--- 4.3 Rozmiary plików ---")
    pliki = {
        "CSV":     p("pomiary.csv"),
        "JSON":    p("pomiary.json"),
        "Parquet": p("pomiary.parquet"),
        "HDF5":    p("pomiary.h5"),
        "Pickle":  p("pomiary.pkl"),
    }
    rozmiary = {fmt: os.path.getsize(path) / 1024 / 1024 for fmt, path in pliki.items()}
    for fmt, mb in rozmiary.items():
        print(f"  {fmt:<8}: {mb:.2f} MB")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(list(rozmiary.keys()), list(rozmiary.values()),
           color=["#4c72b0", "#dd8452", "#55a868", "#c44e52", "#8172b2"])
    ax.set_ylabel("Rozmiar [MB]")
    ax.set_title("Porównanie rozmiarów plików")
    plt.tight_layout()
    plt.savefig(p("benchmark_rozmiary.png"), dpi=150)
    print("Wykres zapisany: benchmark_rozmiary.png")
    plt.close()

    print("\n--- 4.4 Czasy wczytywania ---")
    def zmierz(fn, n=3):
        return min([(t0 := time.perf_counter(), fn(), time.perf_counter() - t0)[2] for _ in range(n)])

    czasy = {
        "CSV":     zmierz(lambda: pd.read_csv(p("pomiary.csv"))),
        "JSON":    zmierz(lambda: pd.read_json(p("pomiary.json"))),
        "Parquet": zmierz(lambda: pd.read_parquet(p("pomiary.parquet"))),
        "HDF5":    zmierz(lambda: pd.read_hdf(p("pomiary.h5"))),
        "Pickle":  zmierz(lambda: pd.read_pickle(p("pomiary.pkl"))),
    }
    for fmt, sec in czasy.items():
        print(f"  {fmt:<8}: {sec*1000:.1f} ms")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(list(czasy.keys()), [v*1000 for v in czasy.values()],
           color=["#4c72b0", "#dd8452", "#55a868", "#c44e52", "#8172b2"])
    ax.set_ylabel("Czas [ms]")
    ax.set_title("Porównanie czasu wczytywania")
    plt.tight_layout()
    plt.savefig(p("benchmark_czas.png"), dpi=150)
    print("Wykres zapisany: benchmark_czas.png")
    plt.close()

    print("\n--- 4.5 Parquet: wszystkie vs 2 kolumny ---")
    t_all = zmierz(lambda: pd.read_parquet(p("pomiary.parquet")))
    t_2   = zmierz(lambda: pd.read_parquet(p("pomiary.parquet"), columns=["date", "pm25"]))
    print(f"  Wszystkie kolumny: {t_all*1000:.1f} ms")
    print(f"  Tylko date+pm25:   {t_2*1000:.1f} ms")
    print(f"  Przyspieszenie: {t_all/t_2:.1f}×")

    print("\n--- 4.6 Wnioski ---")
    print("CSV     — duży rozmiar, wolne wczytywanie; dobry do wymiany z ludźmi/Excel.")
    print("JSON    — największy rozmiar; unikaj dla danych tabelarycznych.")
    print("Parquet — mały rozmiar, bardzo szybkie wczytywanie; ideał do analiz.")
    print("HDF5    — dobry dla dużych danych naukowych i częściowego wczytywania.")
    print("Pickle  — szybki, ale nieprzenośny; tylko do tymczasowego cache.")


# ── Ćwiczenie 5: SQLite i pandas ─────────────────────────────────────────────

def cwiczenie_5():
    print("\n" + "="*60)
    print("ĆWICZENIE 5: SQLite i pandas")
    print("="*60)

    conn = sqlite3.connect(p("sklep.db"))

    print("\n--- 5.1 Dostępne tabele ---")
    tabele = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn)
    print(tabele.to_string(index=False))

    print("\n--- 5.2 Wczytanie tabel ---")
    klienci    = pd.read_sql("SELECT * FROM klienci",    conn)
    produkty   = pd.read_sql("SELECT * FROM produkty",   conn)
    zamowienia = pd.read_sql("SELECT * FROM zamowienia", conn)

    for nazwa, df in [("klienci", klienci), ("produkty", produkty), ("zamowienia", zamowienia)]:
        print(f"\n{nazwa}: {df.shape[0]} wierszy × {df.shape[1]} kolumn")
        print(df.dtypes.to_string())
        print(df.head(2))

    print("\n--- 5.3 Top 10 klientów wg liczby zamówień (SQL) ---")
    top10_sql = pd.read_sql("""
        SELECT k.imie, k.nazwisko, k.miasto,
               COUNT(z.id) AS liczba_zamowien
        FROM klienci k
        JOIN zamowienia z ON z.klient_id = k.id
        GROUP BY k.id
        ORDER BY liczba_zamowien DESC
        LIMIT 10
    """, conn)
    print(top10_sql.to_string(index=False))

    print("\n--- Dod. 1 Wczytywanie porcjami (chunksize=100) ---")
    suma_wartosci = 0.0
    n_porcji = 0
    for chunk in pd.read_sql("SELECT * FROM zamowienia", conn, chunksize=100):
        if "wartosc" in chunk.columns:
            suma_wartosci += chunk["wartosc"].sum()
        n_porcji += 1
    print(f"Wczytano {n_porcji} porcji po max 100 rekordów")
    print(f"Łączna wartość zamówień: {suma_wartosci:.2f}")

    print("\n--- Dod. 2 Wartość per kategoria — SQL ---")
    kategorie_sql = pd.read_sql("""
        SELECT p.kategoria,
               SUM(z.ilosc * p.cena) AS wartosc_sprzedazy,
               COUNT(*) AS liczba_pozycji
        FROM zamowienia z
        JOIN produkty p ON p.id = z.produkt_id
        GROUP BY p.kategoria
        ORDER BY wartosc_sprzedazy DESC
    """, conn)
    print(kategorie_sql.to_string(index=False))

    print("\n--- Dod. 3 Wartość per kategoria — pandas ---")
    merged = zamowienia.merge(produkty, left_on="produkt_id", right_on="id", suffixes=("_zam", "_prod"))
    merged["wartosc"] = merged["ilosc"] * merged["cena"]
    kategorie_pd = (merged.groupby("kategoria")["wartosc"]
                          .agg(wartosc_sprzedazy="sum", liczba_pozycji="count")
                          .sort_values("wartosc_sprzedazy", ascending=False)
                          .reset_index())
    print(kategorie_pd.to_string(index=False))

    conn.close()
    print("\nPołączenie z bazą zamknięte.")


# ── Punkt wejścia ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cwiczenie_1()
    cwiczenie_2()
    cwiczenie_3()
    cwiczenie_4()
    cwiczenie_5()
    print("\n✓ Wszystkie ćwiczenia zakończone.")