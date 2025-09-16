import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime
import warnings

# Unterdrückt RuntimeWarnings und FutureWarnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


def load_and_analyze_data(csv_file, date_column, price_column, inflation_rate):
    """
    Lädt historische Daten, berechnet monatliche Renditen und liefert deren Statistik.
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Die Datei '{csv_file}' wurde nicht gefunden.")

    df = pd.read_csv(csv_file, sep=';', decimal=',', parse_dates=[date_column], date_format="%m/%d/%Y")

    # Die 'price' Spalte enthält bereits die monatlichen Renditen
    df['monthly_return'] = pd.to_numeric(df[price_column], errors='coerce')
    df.dropna(inplace=True)
    df.set_index(date_column, inplace=True)

    monthly_returns = df['monthly_return'].resample('ME').mean()

    # Korrektur um inflationsbereinigte Rendite
    monthly_inflation = (1 + inflation_rate) ** (1 / 12) - 1
    monthly_returns_adj = (monthly_returns - monthly_inflation) / (1 + monthly_inflation)

    mean_monthly_return = monthly_returns_adj.mean()
    std_dev_monthly_return = monthly_returns_adj.std()

    print(f"Historische Analyse:")
    print(f"  Durchschnittliche monatliche Rendite (inflationsbereinigt): {mean_monthly_return:.4f}")
    print(f"  Monatliche Volatilität (Standardabweichung): {std_dev_monthly_return:.4f}")
    print("-" * 50)

    return monthly_returns_adj, mean_monthly_return, std_dev_monthly_return


def get_worst_3_years_from_simulations(results, years):
    """
    Findet innerhalb der Monte-Carlo-Ergebnisse den Simulationspfad mit
    den schlechtesten aufeinanderfolgenden 3 Jahren.
    """
    annual_returns = np.zeros((results.shape[0], years))
    for i in range(results.shape[0]):
        for y in range(years):
            start_value = results[i, y * 12]
            end_value = results[i, (y + 1) * 12]
            if start_value > 0:
                annual_returns[i, y] = (end_value / start_value) - 1

    rolling_returns = np.zeros((results.shape[0], years - 2))
    for i in range(results.shape[0]):
        for y in range(years - 2):
            rolling_returns[i, y] = (1 + annual_returns[i, y]) * (1 + annual_returns[i, y + 1]) * (
                    1 + annual_returns[i, y + 2]) - 1

    worst_path_index = np.argmin(np.min(rolling_returns, axis=1))
    worst_period_start_year = np.argmin(rolling_returns[worst_path_index, :])

    # Neue Berechnung der kumulierten Rendite
    worst_period_return = np.min(rolling_returns)

    # Monatliche Renditen des schlechtesten Pfads extrahieren
    worst_period_start_month = worst_period_start_year * 12
    worst_period_end_month = worst_period_start_month + 3 * 12

    path_values = results[worst_path_index, worst_period_start_month:worst_period_end_month + 1]

    worst_monthly_returns = np.zeros(36)
    for i in range(36):
        worst_monthly_returns[i] = (path_values[i + 1] / path_values[i]) - 1

    return worst_monthly_returns, worst_period_return

def get_worst_3_years(monthly_returns):
    """
    Findet die 3 aufeinanderfolgenden Jahre mit der schlechtesten Rendite
    und gibt die monatlichen Renditen dieser Periode sowie deren kumulierte Rendite zurück.
    """
    returns_by_year = monthly_returns.groupby(monthly_returns.index.year).apply(lambda x: (1 + x).prod() - 1)
    rolling_returns = returns_by_year.rolling(window=3).apply(lambda x: (1 + x).prod() - 1, raw=True)

    worst_period_start_year = rolling_returns.idxmin() - 2
    worst_period_return = rolling_returns.min()

    worst_period_returns = monthly_returns[(monthly_returns.index.year >= worst_period_start_year) &
                                           (monthly_returns.index.year < worst_period_start_year + 3)]

    return worst_period_returns.values, worst_period_start_year, worst_period_return

def run_monte_carlo_simulation(mean_return, std_dev, initial_investment, years, num_simulations, scenario='normal',
                               worst_returns=None, monthly_investment=0, monthly_dynamik_rate=0,
                               dynamik_turnus_monate=12, beitragszahldauer_monate=0, entnahme_plan=None,
                               death_year=None, ruecknahmeabschlag=0.0):
    """
    Führt die Monte-Carlo-Simulation für einen Sparplan durch, wahlweise mit 'Worst-Case'-Szenarien.
    """
    num_months = years * 12

    simulation_results = np.zeros((num_simulations, num_months + 1))
    year_intervals = [1, 2, 5, 10, 15, 20, 25]
    if years not in year_intervals:
        year_intervals.append(years)
    year_intervals.sort()

    final_values_at_years = {y: np.zeros(num_simulations) for y in year_intervals}
    annual_returns_all_sims = np.zeros((num_simulations, years))
    max_drawdowns = np.zeros(num_simulations)

    entnahme_plan = entnahme_plan if entnahme_plan is not None else {}

    for i in range(num_simulations):
        path = np.zeros(num_months + 1)
        path[0] = initial_investment
        current_monthly_investment = monthly_investment

        death_triggered_in_sim = False

        for month in range(num_months):
            current_year_for_death = (month + 1) // 12

            # NEUE LOGIK FÜR DEN TODESFALL
            if death_year and current_year_for_death == death_year and not death_triggered_in_sim:
                # Simuliere steuerfreien Reset im Todesfall
                depotwert_brutto = path[month]
                depotwert_nach_abschlag = depotwert_brutto * (1 - ruecknahmeabschlag)
                path[month + 1] = depotwert_nach_abschlag
                death_triggered_in_sim = True
                monthly_return_simulated = 0.0
            else:
                # Dynamische Anpassung der Einzahlung
                if monthly_dynamik_rate > 0 and (month > 0) and (month % dynamik_turnus_monate == 0):
                    current_monthly_investment *= (1 + monthly_dynamik_rate)

                # Monatliche Einzahlung hinzufügen
                if month < beitragszahldauer_monate:
                    path[month + 1] = path[month] + current_monthly_investment
                else:
                    path[month + 1] = path[month]

                # Simulation der Rendite
                # NEUE Logik für das Szenario 'worst_simulated'
                if scenario == 'start' and worst_returns is not None and month < len(worst_returns):
                    monthly_return_simulated = worst_returns[month]
                elif scenario == 'withdrawal' and worst_returns is not None and 19 * 12 <= month < 19 * 12 + len(worst_returns):
                    monthly_return_simulated = worst_returns[month - 19 * 12]
                elif scenario == 'worst_simulated' and worst_returns is not None:
                    # Der Index 'month' wird verwendet, da 'worst_returns' die gesamte Pfadreihe ist
                    monthly_return_simulated = worst_returns[month]
                else:
                    monthly_return_simulated = np.random.normal(mean_return, std_dev)

                path[month + 1] *= (1 + monthly_return_simulated)

            # Korrektur: Jährliche Entnahme abziehen
            current_year_index = (month + 1) // 12
            if (month + 1) % 12 == 0 and current_year_index in entnahme_plan:
                path[month + 1] -= entnahme_plan[current_year_index]

            if (month + 1) % 12 == 0:
                year_index = (month + 1) // 12 - 1
                start_of_year_value = path[max(0, (month + 1 - 12))]
                end_of_year_value = path[month + 1]
                if start_of_year_value != 0:
                    annual_return = (end_of_year_value / start_of_year_value) - 1
                    annual_returns_all_sims[i, year_index] = annual_return

            if (month + 1) in [y * 12 for y in year_intervals]:
                year = (month + 1) // 12
                final_values_at_years[year][i] = path[month + 1]

        cumulative_max = np.maximum.accumulate(path)
        drawdown = (path - cumulative_max) / cumulative_max
        max_drawdowns[i] = np.min(drawdown)

        simulation_results[i, :] = path

    return simulation_results, final_values_at_years, annual_returns_all_sims, max_drawdowns

def analyze_and_plot_results(results, final_values_at_years, annual_returns_all_sims, max_drawdowns, scenario_name,
                             years, start_value, num_simulations):
    # --------------------------------------
    # TABELLE 1: Erwartete annualisierte Renditen über die Zeit
    # --------------------------------------
    percentiles = [10, 25, 50, 75, 90]
    annualized_returns_data = {}

    for year, values in final_values_at_years.items():
        if year > 0 and start_value > 0:
            annualized_returns = (values / start_value) ** (1 / year) - 1
            percentile_values = np.percentile(annualized_returns, percentiles)
            annualized_returns_data[year] = percentile_values

    df_returns_over_time = pd.DataFrame(annualized_returns_data, index=[f'{p}. Perzentil' for p in percentiles])
    df_returns_over_time_formatted = df_returns_over_time.applymap(lambda x: f'{x:,.2%}')

    print(f"--- 1. Erwartete annualisierte Renditen über die Zeit ({scenario_name}) ---")
    print(df_returns_over_time_formatted)
    df_returns_over_time.to_csv(f'erwartete_renditen_{scenario_name}.csv', sep=';')
    print("\n")

    # --------------------------------------
    # TABELLE 2: Jährliche Rendite-Wahrscheinlichkeiten
    # --------------------------------------
    annual_returns_percs = {}
    return_ranges = [
        '<= 0%', '>0% bis 2,5%', '>2,5% bis 5%', '>5% bis 7,5%', '>7,5% bis 10%', '>10% bis 12,5%', '>12,5%'
    ]

    for year_idx, year in enumerate(range(1, years + 1)):
        year_returns = annual_returns_all_sims[:, year_idx]
        counts = {
            '<= 0%': np.sum(year_returns <= 0),
            '>0% bis 2,5%': np.sum((year_returns > 0) & (year_returns <= 0.025)),
            '>2,5% bis 5%': np.sum((year_returns > 0.025) & (year_returns <= 0.05)),
            '>5% bis 7,5%': np.sum((year_returns > 0.05) & (year_returns <= 0.075)),
            '>7,5% bis 10%': np.sum((year_returns > 0.075) & (year_returns <= 0.10)),
            '>10% bis 12,5%': np.sum((year_returns > 0.10) & (year_returns <= 0.125)),
            '>12,5%': np.sum(year_returns > 0.125)
        }
        probabilities = {k: v / num_simulations for k, v in counts.items()}
        annual_returns_percs[year] = list(probabilities.values())

    df_probabilities = pd.DataFrame(annual_returns_percs, index=return_ranges)
    df_probabilities_formatted = df_probabilities.applymap(lambda x: f'{x * 100:,.2f}%')

    print(f"--- 2. Jährliche Rendite-Wahrscheinlichkeiten ({scenario_name}) ---")
    print(df_probabilities_formatted.to_string())
    df_probabilities.to_csv(f'rendite_wahrscheinlichkeiten_{scenario_name}.csv', sep=';')
    print("\n")

    # --------------------------------------
    # TABELLE 3: Verlustwahrscheinlichkeiten
    # --------------------------------------
    print(f"--- 3. Verlustwahrscheinlichkeiten innerhalb der Gesamtperiode ({scenario_name}) ---")
    print("Die Tabelle zeigt die Wahrscheinlichkeit, dass das Portfolio zu irgendeinem Zeitpunkt")
    print("einen maximalen Wertverlust (Drawdown) von der angegebenen Höhe erlebt.")
    print("-" * 50)

    loss_thresholds = np.arange(-0.025, -0.325, -0.025)
    loss_probabilities = []

    for threshold in loss_thresholds:
        prob_of_loss = np.sum(max_drawdowns <= threshold) / num_simulations
        loss_probabilities.append(prob_of_loss)

    data_loss = {
        'Verlust-Schwelle': [f'<= {abs(t):.1%}' for t in loss_thresholds],
        'Wahrscheinlichkeit innerhalb der Periode': loss_probabilities
    }

    df_loss = pd.DataFrame(data_loss)
    df_loss_formatted = df_loss.copy()
    df_loss_formatted['Wahrscheinlichkeit innerhalb der Periode'] = df_loss_formatted[
        'Wahrscheinlichkeit innerhalb der Periode'].map(lambda x: f'{x * 100:,.2f}%')

    print(df_loss_formatted.to_string(index=False))
    df_loss.to_csv(f'verlust_wahrscheinlichkeiten_{scenario_name}.csv', sep=';', index=False)
    print("\n")

    print("-" * 50)
    print(f"Alle 3 Tabellen für das Szenario '{scenario_name}' wurden als CSV-Dateien exportiert.")
    print("-" * 50)

    # Plot der Simulationspfade
    plt.figure(figsize=(12, 8))
    p10 = np.percentile(results, 10, axis=0)
    p90 = np.percentile(results, 90, axis=0)
    plt.fill_between(range(len(p10)), p10, p90, color='lightblue', alpha=0.3, label='10.-90. Perzentilbereich')
    p25 = np.percentile(results, 25, axis=0)
    p75 = np.percentile(results, 75, axis=0)
    plt.fill_between(range(len(p25)), p25, p75, color='royalblue', alpha=0.5, label='25.-75. Perzentilbereich')
    median_line = np.percentile(results, 50, axis=0)
    plt.plot(median_line, label='Median', color='blue', linewidth=2)
    plt.title(f'Monte-Carlo-Simulation der Portfolioentwicklung ({scenario_name})')
    plt.xlabel('Monate')
    plt.ylabel('Depotwert (€)')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'monte_carlo_pfade_{scenario_name}.png')
    plt.close()