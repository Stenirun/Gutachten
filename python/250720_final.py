# === IMPORTS ===
from collections import deque
import datetime
import matplotlib.pyplot as plt
import pandas as pd

# === PARAMETER ===
initial_investment = 10_000
monthly_investment = 400
monthly_dynamik_rate = 0
freistellungsauftrag_jahr = 0
sonderzahlung_jahr = 0
sonderzahlung_betrag = 0
dynamik_turnus_monate = 12
monthly_return = (1 + 0.06) ** (1 / 12) - 1
simulation_years = 30
entnahme_jahre = 0
total_months = simulation_years * 12
rebalancing_rate = 0.20
basiszins = 0.0255
teilfreistellung = 0.7
full_tax_rate = 0.25 * (1 + 0.055 + 0.09)
ausgabeaufschlag = 0.002
ruecknahmeabschlag = 0.002
ter = 0.0045
verwalter_gebuehr = 0.0119
stueckkosten = 45
annual_withdrawal = 20000

# === INITIALISIERUNG ===
start_date = datetime.date(2025, 1, 1)
portfolio = deque()
log = []
total_tax_paid = 0
total_costs_paid = 0
jahreswerte = []
freistellungs_topf = freistellungsauftrag_jahr

# Einmalanlage mit Ausgabeaufschlag
aufschlag = initial_investment * ausgabeaufschlag
nettobetrag = initial_investment - aufschlag
portfolio.append({
    "date": start_date,
    "amount_invested": nettobetrag,
    "units": nettobetrag,
    "value": nettobetrag,
    "start_of_prev_year_value": nettobetrag,
    "vorabpauschalen_bereits_versteuert": 0.0
})

# === SIMULATION ===
for month in range(total_months + entnahme_jahre * 12):
    current_date = start_date + datetime.timedelta(days=30 * month)
    year = current_date.year
    is_january = current_date.month == 1

    # Dynamik des Sparbetrags
    if month > 0 and month % dynamik_turnus_monate == 0:
        monthly_investment *= (1 + monthly_dynamik_rate)

    # Sonderzahlung
    if month == sonderzahlung_jahr * 12:
        aufschlag = sonderzahlung_betrag * ausgabeaufschlag
        netto = sonderzahlung_betrag - aufschlag
        portfolio.append({
            "date": current_date,
            "amount_invested": netto,
            "units": netto,
            "value": netto,
            "start_of_prev_year_value": netto,
            "vorabpauschalen_bereits_versteuert": 0.0
        })

    # Monatliche Einzahlung
    if month < total_months:
        aufschlag = monthly_investment * ausgabeaufschlag
        netto = monthly_investment - aufschlag
        portfolio.append({
            "date": current_date,
            "amount_invested": netto,
            "units": netto,
            "value": netto,
            "start_of_prev_year_value": netto,
            "vorabpauschalen_bereits_versteuert": 0.0
        })

    # Vorabpauschale im Januar
    if is_january:
        freistellungs_topf = freistellungsauftrag_jahr
        for entry in portfolio:
            start_value = entry["start_of_prev_year_value"]
            fiktiver_ertrag = start_value * basiszins
            real_ertrag = entry["value"] - entry["amount_invested"]
            steuerbarer_ertrag = min(fiktiver_ertrag, real_ertrag)
            steuerfreibetrag = min(freistellungs_topf, steuerbarer_ertrag * teilfreistellung)
            zu_versteuern = max(0, (steuerbarer_ertrag * teilfreistellung) - steuerfreibetrag)
            steuer = max(0, zu_versteuern * full_tax_rate)
            if steuer > 0:
                entry["value"] -= steuer
                entry["vorabpauschalen_bereits_versteuert"] += steuerbarer_ertrag
                total_tax_paid += steuer
                freistellungs_topf -= steuerfreibetrag

    # TER, Verwaltergebühren, Stückkosten (jährlich)
    if is_january:
        jahreswert = sum([e["value"] for e in portfolio])
        kosten = jahreswert * (ter + verwalter_gebuehr) + stueckkosten
        for entry in portfolio:
            anteil = entry["value"] / jahreswert if jahreswert > 0 else 0
            entry["value"] -= kosten * anteil
        total_costs_paid += kosten

    # Wertentwicklung
    for entry in portfolio:
        entry["value"] *= (1 + monthly_return)

    # Rebalancing (Umschichtung)
    if is_january and 0 < month < total_months:
        rebalancing_value = sum(e["value"] for e in portfolio) * rebalancing_rate
        remaining = rebalancing_value
        while remaining > 0 and portfolio:
            entry = portfolio[0]
            if entry["value"] <= 0:
                portfolio.popleft()
                continue
            sell_value = min(entry["value"], remaining)
            prop = sell_value / entry["value"]
            cost_basis = entry["amount_invested"] * prop
            anteilig_vorab = entry["vorabpauschalen_bereits_versteuert"] * prop
            gain = sell_value - cost_basis - anteilig_vorab
            steuerbarer_gewinn = gain * teilfreistellung
            steuerfreibetrag = min(freistellungs_topf, steuerbarer_gewinn)
            steuer = max(0, (steuerbarer_gewinn - steuerfreibetrag) * full_tax_rate)
            freistellungs_topf -= steuerfreibetrag
            sell_value_netto = sell_value - steuer - (sell_value * ruecknahmeabschlag)
            total_tax_paid += steuer
            entry["value"] -= sell_value
            entry["amount_invested"] -= cost_basis
            entry["vorabpauschalen_bereits_versteuert"] -= anteilig_vorab
            remaining -= sell_value
            if entry["value"] < 1e-4:
                portfolio.popleft()
        # Wiederanlage nach Ausgabeaufschlag
        reinvest_netto = rebalancing_value * (1 - ruecknahmeabschlag - ausgabeaufschlag)
        portfolio.append({
            "date": current_date,
            "amount_invested": reinvest_netto,
            "units": reinvest_netto,
            "value": reinvest_netto,
            "start_of_prev_year_value": reinvest_netto,
            "vorabpauschalen_bereits_versteuert": 0.0
        })

    # Entnahmephase
    if month >= total_months:
        entnahme_monatlich = annual_withdrawal / 12
        remaining = entnahme_monatlich
        while remaining > 0 and portfolio:
            entry = portfolio[0]
            if entry["value"] <= 0:
                portfolio.popleft()
                continue
            sell_value = min(entry["value"], remaining)
            prop = sell_value / entry["value"]
            cost_basis = entry["amount_invested"] * prop
            anteilig_vorab = entry["vorabpauschalen_bereits_versteuert"] * prop
            gain = sell_value - cost_basis - anteilig_vorab
            steuerbarer_gewinn = gain * teilfreistellung
            steuerfreibetrag = min(freistellungs_topf, steuerbarer_gewinn)
            steuer = max(0, (steuerbarer_gewinn - steuerfreibetrag) * full_tax_rate)
            freistellungs_topf -= steuerfreibetrag
            sell_value_netto = sell_value - steuer
            total_tax_paid += steuer
            entry["value"] -= sell_value
            entry["amount_invested"] -= cost_basis
            entry["vorabpauschalen_bereits_versteuert"] -= anteilig_vorab
            remaining -= sell_value
            if entry["value"] < 1e-4:
                portfolio.popleft()

    # Logging
    depotwert = sum([e["value"] for e in portfolio])
    log.append({
        "Datum": current_date,
        "Depotwert": depotwert,
        "Steuern kumuliert": total_tax_paid,
        "Kosten kumuliert": total_costs_paid,
        "Freibetrag verbleibend": freistellungs_topf
    })

    # Jahresanfangswert aktualisieren für Vorabpauschale im Folgejahr
    if current_date.month == 12:
        for entry in portfolio:
            entry["start_of_prev_year_value"] = entry["value"]

# === AUSGABE ===
df = pd.DataFrame(log)
print(df.tail(12))
df['Datum'] = pd.to_datetime(df['Datum'])

plt.figure(figsize=(14, 8))
plt.plot(df['Datum'], df['Depotwert'], label='Depotwert', linewidth=2)
plt.plot(df['Datum'], df['Steuern kumuliert'], label='Kumulierte Steuern', linestyle='--')
plt.plot(df['Datum'], df['Kosten kumuliert'], label='Kumulierte Kosten', linestyle=':')
plt.title('Verlauf von Depotwert, Steuern und Kosten')
plt.xlabel('Datum')
plt.ylabel('Euro')
plt.legend()
plt.grid(True)
plt.tight_layout()
#plt.show()

print(f"Endwert: {df['Depotwert'].iloc[-1]:,.2f} €")
print(f"Summe gezahlter Steuern: {total_tax_paid:,.2f} €")
print(f"Summe gezahlter Kosten: {total_costs_paid:,.2f} €")
