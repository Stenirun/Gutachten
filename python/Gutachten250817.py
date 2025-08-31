# === IMPORTS ===
from collections import deque
from dateutil.relativedelta import relativedelta
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy_financial as npf
import numpy as np
import dataclasses
from typing import List, Dict, Any, Optional



# === EINGANGSPARAMETER ALS DATENKLASSE ===
@dataclasses.dataclass
class SparplanParameter:
    """
    Dataclass für die Eingabeparameter eines Sparplans.
    """
    label: str
    versicherung_modus: bool
    eintrittsalter: int
    initial_investment: float
    monthly_investment: float
    laufzeit: int
    beitragszahldauer: int
    monthly_dynamik_rate: float
    dynamik_turnus_monate: int
    sonderzahlung_jahr: int
    sonderzahlung_betrag: float
    regel_sonderzahlung_betrag: float
    regel_sonderzahlung_turnus_jahre: int
    annual_withdrawal: float
    annual_return: float
    ausgabeaufschlag: float
    ruecknahmeabschlag: float
    ter: float
    serviceentgelt: float
    stueckkosten: float
    abschlusskosten_einmalig_prozent: float
    abschlusskosten_monatlich_prozent: float
    verrechnungsdauer_monate: int
    verwaltungskosten_monatlich_prozent: float
    abgeltungssteuer_rate: float
    soli_zuschlag_on_abgeltungssteuer: float
    kirchensteuer_on_abgeltungssteuer: float
    persoenlicher_steuersatz: float
    freistellungsauftrag_jahr: float
    teilfreistellung: float
    basiszins: float
    rebalancing_rate: float
    entnahme_modus: str
    bewertungsdauer: int
    annual_std_dev: float = 0.15  # Hinzugefügt für Monte-Carlo


class SparplanSimulator:
    """
    Simulation eines Sparplans auf Basis der übergebenen Parameter.
    Die Klasse kapselt den gesamten Zustand und die Logik der Simulation.
    """

    def __init__(self, params: SparplanParameter):
        self.params = params
        self.portfolio = deque()
        self.rebalancing_log = []
        self.monatliche_kosten_logs = []
        self.cashflows = []

        self.ausgabeaufschlag_summe = 0
        self.ruecknahmeabschlag_summe = 0
        self.stueckkosten_summe = 0
        self.abschlusskosten_summe = 0
        self.verwaltungskosten_summe = 0
        self.ter_summe = 0
        self.serviceentgelt_summe = 0
        self.kumulierte_entnahmen = 0
        self.total_tax_paid = 0
        self.freistellungs_topf = params.freistellungsauftrag_jahr
        self.monthly_investment = params.monthly_investment
        self.abschlusskosten_monatlich_rest = [0.0] * (params.laufzeit * 12)
        self.abschlusskosten_einmalig_rest = [0.0] * (params.laufzeit * 12)

    def run_simulation(self) -> (pd.DataFrame, List[Dict[str, Any]], List[float]):
        self._initialisiere_simulation()
        for month in range(self.params.laufzeit * 12):
            self._simuliere_monat(month)
        self._finalisiere_simulation()
        df_kosten = pd.DataFrame(self.monatliche_kosten_logs)
        return df_kosten, self.rebalancing_log, self.cashflows

    def _initialisiere_simulation(self):
        self.params.monthly_return = (1 + self.params.annual_return) ** (1 / 12) - 1
        self.params.full_tax_rate = self.params.abgeltungssteuer_rate * (
                1 + self.params.soli_zuschlag_on_abgeltungssteuer + self.params.kirchensteuer_on_abgeltungssteuer)

        if self.params.versicherung_modus:
            self.params.ausgabeaufschlag = 0.0
            self.params.ruecknahmeabschlag = 0.0
            self.params.stueckkosten = 0.0
        else:
            self.params.abschlusskosten_einmalig_prozent = 0.0
            self.params.abschlusskosten_monatlich_prozent = 0.0
            self.params.verwaltungskosten_monatlich_prozent = 0.0

        aufschlag = self.params.initial_investment * self.params.ausgabeaufschlag
        nettobetrag = self.params.initial_investment - aufschlag
        self.ausgabeaufschlag_summe += aufschlag
        self.cashflows.append(-self.params.initial_investment)

        if nettobetrag > 0:
            self.portfolio.append({
                "date": datetime.date(2025, 1, 1),
                "amount_invested": nettobetrag,
                "units": nettobetrag,
                "value": nettobetrag,
                "start_of_prev_year_value": nettobetrag,
                "vorabpauschalen_bereits_versteuert": 0.0
            })

    def _simuliere_monat(self, month: int):
        current_date = datetime.date(2025, 1, 1) + relativedelta(months=month)
        is_january = current_date.month == 1

        if is_january:
            self.freistellungs_topf = self.params.freistellungsauftrag_jahr

        self._handle_monthly_investment(month, current_date)
        self._handle_costs(month, current_date)
        self._handle_taxes(current_date)
        self._handle_rebalancing(current_date)

        # Wertentwicklung des Portfolios im aktuellen Monat
        for entry in self.portfolio:
            entry["value"] *= (1 + self.params.monthly_return)

        self._handle_withdrawals(month, current_date)

        depotwert = sum(e["value"] for e in self.portfolio)
        self.monatliche_kosten_logs.append({
            "Datum": current_date, "Depotwert": depotwert, "Ausgabeaufschlag kum": self.ausgabeaufschlag_summe,
            "Rücknahmeabschlag kum": self.ruecknahmeabschlag_summe, "Stückkosten kum": self.stueckkosten_summe,
            "Gesamtfondkosten kum": self.ter_summe, "Serviceentgelt kum": self.serviceentgelt_summe,
            "Abschlusskosten kum": self.abschlusskosten_summe, "Verwaltungskosten kum": self.verwaltungskosten_summe,
            "Steuern kumuliert": self.total_tax_paid, "Kumulierte Entnahmen": self.kumulierte_entnahmen
        })

        if current_date.month == 12:
            for entry in self.portfolio:
                entry["start_of_prev_year_value"] = entry["value"]

    def _handle_monthly_investment(self, month, current_date):
        if month > 0 and month % self.params.dynamik_turnus_monate == 0:
            self.monthly_investment *= (1 + self.params.monthly_dynamik_rate)

        is_einmalig = month == self.params.sonderzahlung_jahr * 12
        is_regelmaessig = (self.params.regel_sonderzahlung_turnus_jahre > 0 and month > 0 and month % (
                self.params.regel_sonderzahlung_turnus_jahre * 12) == 0)

        # Verarbeitung von Sonderzahlungen
        if is_einmalig or is_regelmaessig:
            betrag = (self.params.sonderzahlung_betrag if is_einmalig else self.params.regel_sonderzahlung_betrag)
            if betrag > 0:
                self.cashflows.append(-betrag)
                if not self.params.versicherung_modus:
                    aufschlag = betrag * self.params.ausgabeaufschlag
                    netto = betrag - aufschlag
                    self.ausgabeaufschlag_summe += aufschlag
                else:
                    netto = betrag
                self.portfolio.append(
                    {"date": current_date, "amount_invested": netto, "value": netto, "start_of_prev_year_value": netto,
                     "vorabpauschalen_bereits_versteuert": 0.0})

        # Monatliche Einzahlung
        if month < self.params.beitragszahldauer * 12:
            aufschlag = self.monthly_investment * self.params.ausgabeaufschlag
            netto = self.monthly_investment - aufschlag
            self.ausgabeaufschlag_summe += aufschlag
            self.cashflows.append(-self.monthly_investment)
            self.portfolio.append(
                {"date": current_date, "amount_invested": netto, "value": netto, "start_of_prev_year_value": netto,
                 "vorabpauschalen_bereits_versteuert": 0.0})

    def _handle_costs(self, month, current_date):
        depotwert = sum(e["value"] for e in self.portfolio) if self.portfolio else 0
        if self.params.versicherung_modus and month < self.params.beitragszahldauer * 12:
            verwaltungskosten = self.monthly_investment * self.params.verwaltungskosten_monatlich_prozent
            for entry in self.portfolio:
                anteil = entry["value"] / depotwert if depotwert > 0 else 0
                entry["value"] -= verwaltungskosten * anteil
            self.verwaltungskosten_summe += verwaltungskosten

            if month < self.params.verrechnungsdauer_monate:
                abschluss_kosten = (
                        self.abschlusskosten_einmalig_rest[month] + self.abschlusskosten_monatlich_rest[month])
                for entry in self.portfolio:
                    anteil = entry["value"] / depotwert if depotwert > 0 else 0
                    entry["value"] -= abschluss_kosten * anteil
                self.abschlusskosten_summe += abschluss_kosten

        if current_date.month == 1:
            if depotwert > 0:
                fond_kosten = depotwert * self.params.ter
                service_kosten = depotwert * self.params.serviceentgelt
                stueck_kosten = self.params.stueckkosten

                total_kosten = fond_kosten + service_kosten + stueck_kosten

                for entry in self.portfolio:
                    anteil = entry["value"] / depotwert if depotwert > 0 else 0
                    entry["value"] -= total_kosten * anteil

                self.ter_summe += fond_kosten
                self.serviceentgelt_summe += service_kosten
                self.stueckkosten_summe += stueck_kosten

    def _handle_taxes(self, current_date):
        is_january = current_date.month == 1
        if not self.params.versicherung_modus and is_january:
            for entry in self.portfolio:
                start_value = entry["start_of_prev_year_value"]
                fiktiver_ertrag = start_value * self.params.basiszins
                real_ertrag = entry["value"] - start_value
                steuerbarer_ertrag = min(fiktiver_ertrag, real_ertrag)
                steuerfreibetrag = min(self.freistellungs_topf, steuerbarer_ertrag * (1 - self.params.teilfreistellung))
                zu_versteuern = max(0, (steuerbarer_ertrag * (1 - self.params.teilfreistellung)) - steuerfreibetrag)
                steuer = max(0, zu_versteuern * self.params.full_tax_rate)

                if steuer > 0:
                    entry["value"] -= steuer
                    entry["vorabpauschalen_bereits_versteuert"] += zu_versteuern
                    self.total_tax_paid += steuer
                    self.freistellungs_topf -= steuerfreibetrag

    def _handle_rebalancing(self, current_date):
        if not self.params.versicherung_modus and current_date.month == 12 and self.params.rebalancing_rate > 0:
            depotwert = sum(e["value"] for e in self.portfolio)
            umzuschichten = depotwert * self.params.rebalancing_rate
            if umzuschichten > 0:
                remaining = umzuschichten
                temp_queue = deque()
                total_verkauf = 0.0
                total_steuer = 0.0
                total_netto = 0.0
                while remaining > 1e-9 and self.portfolio:
                    entry = self.portfolio.popleft()
                    if entry["value"] <= 0: continue
                    sell_value = min(entry["value"], remaining)
                    prop = sell_value / entry["value"]
                    cost_basis = entry["amount_invested"] * prop
                    gain = sell_value - cost_basis
                    steuerbarer_gewinn = gain * (1 - self.params.teilfreistellung)
                    vorab_used = min(entry.get("vorabpauschalen_bereits_versteuert", 0.0) * prop, steuerbarer_gewinn)
                    steuerbarer_gewinn = max(0.0, steuerbarer_gewinn - vorab_used)
                    steuerfreibetrag = min(self.freistellungs_topf, steuerbarer_gewinn)
                    self.freistellungs_topf -= steuerfreibetrag
                    effektiver_steuersatz = min(self.params.full_tax_rate, self.params.persoenlicher_steuersatz)
                    steuer = max(0.0, (steuerbarer_gewinn - steuerfreibetrag) * effektiver_steuersatz)
                    ruecknahmeabschlag = sell_value * self.params.ruecknahmeabschlag
                    netto_reinvest = sell_value - steuer - ruecknahmeabschlag

                    self.total_tax_paid += steuer
                    self.ruecknahmeabschlag_summe += ruecknahmeabschlag
                    total_verkauf += sell_value
                    total_steuer += steuer
                    total_netto += netto_reinvest

                    entry["value"] -= sell_value
                    entry["amount_invested"] -= cost_basis
                    entry["vorabpauschalen_bereits_versteuert"] = max(0.0,
                                                                      entry.get("vorabpauschalen_bereits_versteuert",
                                                                                0.0) - vorab_used)
                    if entry["value"] > 1e-9:
                        temp_queue.append(entry)
                    remaining -= sell_value

                self.portfolio = deque(list(temp_queue) + list(self.portfolio))
                if total_netto > 1e-9:
                    self.portfolio.append({"date": current_date, "amount_invested": total_netto, "value": total_netto,
                                           "start_of_prev_year_value": total_netto,
                                           "vorabpauschalen_bereits_versteuert": 0.0})
                self.rebalancing_log.append(
                    {"Datum": current_date, "Bruttoverkauf": total_verkauf, "Steuer": total_steuer,
                     "Netto reinvestiert": total_netto})

    def _handle_withdrawals(self, month, current_date):
        if month >= self.params.beitragszahldauer * 12:
            depotwert = sum(e["value"] for e in self.portfolio)
            entnahme_betrag = 0
            if self.params.entnahme_modus == "jährlich" and current_date.month == 1:
                entnahme_betrag = min(self.params.annual_withdrawal, depotwert)
            elif self.params.entnahme_modus == "monatlich":
                entnahme_betrag = min(self.params.annual_withdrawal / 12, depotwert)

            if entnahme_betrag >= 0:
                self.cashflows.append(entnahme_betrag)

                remaining_entnahme = entnahme_betrag

                # Entnahme aus dem ältesten Depot-Eintrag
                if self.portfolio:
                    oldest_entry = self.portfolio.popleft()

                    if oldest_entry["value"] >= remaining_entnahme:
                        oldest_entry["value"] -= remaining_entnahme
                        self.kumulierte_entnahmen += remaining_entnahme
                        if oldest_entry["value"] > 1e-9:
                            self.portfolio.appendleft(oldest_entry)
                    else:
                        remaining_entnahme -= oldest_entry["value"]
                        self.kumulierte_entnahmen += oldest_entry["value"]

                        while remaining_entnahme > 1e-9 and self.portfolio:
                            current_entry = self.portfolio.popleft()
                            if current_entry["value"] >= remaining_entnahme:
                                current_entry["value"] -= remaining_entnahme
                                self.kumulierte_entnahmen += remaining_entnahme
                                if current_entry["value"] > 1e-9:
                                    self.portfolio.appendleft(current_entry)
                                remaining_entnahme = 0
                            else:
                                remaining_entnahme -= current_entry["value"]
                                self.kumulierte_entnahmen += current_entry["value"]

    def _finalisiere_simulation(self):
        restwert = sum(e["value"] for e in self.portfolio)
        investiert = sum(e["amount_invested"] for e in self.portfolio)
        end_datum = datetime.date(2025, 1, 1) + relativedelta(months=self.params.laufzeit * 12)

        if restwert > 1e-9:
            gewinn = max(0.0, restwert - investiert)
            steuer = 0
            if self.params.versicherung_modus:
                aktuelle_laufzeit = self.params.laufzeit
                aktuelle_alter = self.params.eintrittsalter + aktuelle_laufzeit
                steuer = gewinn * (
                    0.5 if aktuelle_alter >= 62 and aktuelle_laufzeit >= 12 else 0.85) * self.params.persoenlicher_steuersatz
            else:
                steuerbar = gewinn * (1 - self.params.teilfreistellung)
                bereits_versteuert = sum(e.get("vorabpauschalen_bereits_versteuert", 0.0) for e in self.portfolio)
                steuerbar = max(0.0, steuerbar - bereits_versteuert)
                effektiver_steuersatz = min(self.params.full_tax_rate, self.params.persoenlicher_steuersatz)
                steuer = steuerbar * effektiver_steuersatz

            ruecknahmeabschlag = restwert * self.params.ruecknahmeabschlag
            self.total_tax_paid += steuer
            self.ruecknahmeabschlag_summe += ruecknahmeabschlag
            restwert_net = restwert - steuer - ruecknahmeabschlag
            self.cashflows.append(restwert_net)
            self.kumulierte_entnahmen += restwert_net

        self.monatliche_kosten_logs.append({
            "Datum": end_datum, "Depotwert": 0, "Ausgabeaufschlag kum": self.ausgabeaufschlag_summe,
            "Rücknahmeabschlag kum": self.ruecknahmeabschlag_summe, "Stückkosten kum": self.stueckkosten_summe,
            "Gesamtfondkosten kum": self.ter_summe, "Serviceentgelt kum": self.serviceentgelt_summe,
            "Abschlusskosten kum": self.abschlusskosten_summe, "Verwaltungskosten kum": self.verwaltungskosten_summe,
            "Steuern kumuliert": self.total_tax_paid, "Kumulierte Entnahmen": self.kumulierte_entnahmen
        })


# === HILFSFUNKTIONEN SIND NICHT TEIL DER KLASSEN ===
def auswerten_kosten(df_kosten: pd.DataFrame, params: SparplanParameter, label: str,
                     mc_results: Optional[List[float]] = None) -> pd.DataFrame:
    df_kosten["Jahr"] = pd.to_datetime(df_kosten["Datum"]).dt.year
    numerische_spalten = df_kosten.drop(columns=["Datum", "Jahr"]).select_dtypes(include="number").columns
    kosten_jahr_detail = df_kosten.groupby("Jahr")[numerische_spalten].last().reset_index()

    for spalte in ["Ausgabeaufschlag kum", "Rücknahmeabschlag kum", "Stückkosten kum", "Serviceentgelt kum",
                   "Gesamtfondkosten kum", "Abschlusskosten kum", "Verwaltungskosten kum"]:
        if spalte not in kosten_jahr_detail:
            kosten_jahr_detail[spalte] = 0

    kosten_jahr_detail["Kosten Kapitalanlage"] = kosten_jahr_detail["Gesamtfondkosten kum"]

    if params.versicherung_modus:
        kosten_jahr_detail["Kosten Depot"] = kosten_jahr_detail["Ausgabeaufschlag kum"] + kosten_jahr_detail[
            "Rücknahmeabschlag kum"]
        kosten_jahr_detail["Kosten Versicherung"] = kosten_jahr_detail["Verwaltungskosten kum"] + kosten_jahr_detail[
            "Abschlusskosten kum"] + kosten_jahr_detail["Stückkosten kum"] + kosten_jahr_detail["Serviceentgelt kum"]
    else:
        kosten_jahr_detail["Kosten Depot"] = kosten_jahr_detail["Ausgabeaufschlag kum"] + kosten_jahr_detail[
            "Rücknahmeabschlag kum"] + kosten_jahr_detail["Stückkosten kum"]
        kosten_jahr_detail["Kosten Versicherung"] = kosten_jahr_detail["Serviceentgelt kum"]

    if mc_results is not None:
        mean_value = np.mean(mc_results)
        median_value = np.median(mc_results)
        ci_lower = np.percentile(mc_results, 2.5)
        ci_upper = np.percentile(mc_results, 97.5)

        mc_row = pd.DataFrame([{
            "Jahr": "Monte-Carlo",
            "Depotwert": f"Mittelwert: {mean_value:,.2f} €",
            "Kumulierte Entnahmen": f"Median: {median_value:,.2f} €",
            "Ausgabeaufschlag kum": f"95% CI: [{ci_lower:,.2f} € - {ci_upper:,.2f} €]",
        }])
        kosten_jahr_detail = pd.concat([kosten_jahr_detail, mc_row], ignore_index=True)

    kosten_jahr_detail = kosten_jahr_detail.round(2)
    kosten_jahr_detail.to_csv(f"{label}_Kostenarten_Jahr.csv", index=False)
    print(f"Kostenaufschlüsselung für '{label}' in '{label}_Kostenarten_Jahr.csv' exportiert.")
    return kosten_jahr_detail


def plotten_vergleich(df_list, params_list):
    plt.figure(figsize=(14, 8))
    for df, params in zip(df_list, params_list):
        plt.plot(df['Datum'], df['Depotwert'], label=params.label, linewidth=2)
    plt.xlabel("Datum")
    plt.ylabel("Depotwert in Euro")
    plt.title("Vergleich der Depotentwicklung")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("vergleich_depotentwicklung.png")
    plt.close()


def plotten_kosten(df_kosten, params):
    df_kosten["Jahr"] = pd.to_datetime(df_kosten["Datum"]).dt.year
    df_kum_kosten = df_kosten.groupby("Jahr").last().reset_index()

    kosten_spalten = []
    if params.versicherung_modus:
        kosten_spalten = ["Abschlusskosten kum", "Verwaltungskosten kum", "Gesamtfondkosten kum", "Steuern kumuliert"]
    else:
        kosten_spalten = ["Ausgabeaufschlag kum", "Rücknahmeabschlag kum", "Stückkosten kum", "Gesamtfondkosten kum",
                          "Steuern kumuliert"]

    # Korrektur: Die 'Jahr'-Spalte muss ebenfalls für den Plot ausgewählt werden
    df_kosten_plot = df_kum_kosten[kosten_spalten + ["Jahr"]]
    df_kosten_plot.index = df_kosten_plot["Jahr"]

    plt.figure(figsize=(14, 8))
    df_kosten_plot[kosten_spalten].plot(kind="area", stacked=True, ax=plt.gca(), legend=False)

    handles, labels = plt.gca().get_legend_handles_labels()

    labels_ger = {
        "Abschlusskosten kum": "Abschlusskosten",
        "Verwaltungskosten kum": "Verwaltungskosten",
        "Ausgabeaufschlag kum": "Ausgabeaufschlag",
        "Rücknahmeabschlag kum": "Rücknahmeabschlag",
        "Stückkosten kum": "Stückkosten",
        "Gesamtfondkosten kum": "Gesamtfondkosten (TER)",
        "Steuern kumuliert": "Steuern"
    }

    new_labels = [labels_ger.get(label, label) for label in labels]

    plt.legend(handles, new_labels, title="Kostenarten", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.title(f"Kumulierte Kostenaufschlüsselung für {params.label}")
    plt.xlabel("Jahr")
    plt.ylabel("Kumulierte Kosten in Euro")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{params.label}_kosten_aufschluesselung.png")
    plt.close()


def plotten_entnahmen(df_kosten, params):
    df_kosten["Jahr"] = pd.to_datetime(df_kosten["Datum"]).dt.year
    df_kum_entnahmen = df_kosten.groupby("Jahr").last().reset_index()

    plt.figure(figsize=(14, 8))
    plt.plot(df_kum_entnahmen["Jahr"], df_kum_entnahmen["Kumulierte Entnahmen"], label="Kumulierte Entnahmen",
             linewidth=2)
    plt.xlabel("Jahr")
    plt.ylabel("Kumulierte Entnahmen in Euro")
    plt.title(f"Entwicklung der kumulierten Entnahmen für {params.label}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{params.label}_entnahmen_aufschluesselung.png")
    plt.close()


def berechne_irr_und_print(cashflows, label):
    try:
        irr_monthly = npf.irr(cashflows)
        irr_annual = (1 + irr_monthly) ** 12 - 1
        return irr_annual
    except (ValueError, IndexError) as e:
        print(f"IRR für {label} konnte nicht berechnet werden. Grund: {e}")
        return None


def exportiere_rebalancing_daten(rebalancing_log, label):
    if rebalancing_log:
        df_rebal = pd.DataFrame(rebalancing_log)
        df_rebal.to_csv(f"{label}_Rebalancing.csv", index=False)
        return df_rebal
    return None


def run_monte_carlo(params, num_runs):
    print(f"\nStarte Monte-Carlo-Simulation für '{params.label}' mit {num_runs} Durchläufen...")
    final_values = []

    end_of_beitrags_period_index = params.beitragszahldauer * 12
    if end_of_beitrags_period_index >= params.laufzeit * 12:
        end_of_beitrags_period_index = (params.laufzeit * 12) - 1

    for i in range(num_runs):
        random_annual_return = np.random.normal(params.annual_return, params.annual_std_dev)
        mc_params = dataclasses.replace(params, annual_return=random_annual_return)

        simulator = SparplanSimulator(mc_params)
        df_kosten, _, _ = simulator.run_simulation()
        final_values.append(df_kosten["Depotwert"].iloc[end_of_beitrags_period_index])

    mean_value = np.mean(final_values)
    median_value = np.median(final_values)
    ci_lower = np.percentile(final_values, 2.5)
    ci_upper = np.percentile(final_values, 97.5)

    plt.figure(figsize=(14, 8))
    plt.hist(final_values, bins=50, edgecolor='black', alpha=0.7)
    plt.axvline(mean_value, color='red', linestyle='dashed', linewidth=2, label=f'Mittelwert: {mean_value:,.0f} €')
    plt.axvline(median_value, color='green', linestyle='dashed', linewidth=2, label=f'Median: {median_value:,.0f} €')
    plt.title(f"Monte-Carlo-Simulation der Depotwerte für '{params.label}' am Ende der Einzahlungsphase")
    plt.xlabel("Endwert in Euro")
    plt.ylabel("Anzahl der Simulationen")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{params.label}_monte_carlo_histogramm.png")
    plt.close()

    return final_values, mean_value, median_value, ci_lower, ci_upper


def erzeuge_report(df_kosten_det, df_rebal, irr_annual, mc_results, params):
    report_text = f"""
# Report für {params.label}

---

## Ergebnisse der Simulation
### Deterministische Simulation
* **Depotwert am Ende der Einzahlungsphase:** {df_kosten_det['Depotwert'].iloc[params.beitragszahldauer * 12]:,.2f} €
* **Finaler Depotwert am Ende der Laufzeit:** {df_kosten_det['Depotwert'].iloc[-1]:,.2f} €
* **Interne Zinsfuß (IRR):** {irr_annual:.2%}

### Monte-Carlo-Simulation (am Ende der Einzahlungsphase)
* **Durchschnittlicher Endwert:** {mc_results[1]:,.2f} €
* **Median Endwert:** {mc_results[2]:,.2f} €
* **95% Konfidenzintervall:** [{mc_results[3]:,.2f} € - {mc_results[4]:,.2f} €]

---

## Visualisierungen
* **Vergleich der Depotentwicklung:** ![Vergleich der Depotentwicklung](vergleich_depotentwicklung.png)
* **Kostenaufschlüsselung:** ![Kostenaufschlüsselung für {params.label}]({params.label}_kosten_aufschluesselung.png)
* **Kumulierte Entnahmen:** ![Kumulierte Entnahmen für {params.label}]({params.label}_entnahmen_aufschluesselung.png)
* **Monte-Carlo-Verteilung:** ![Monte-Carlo-Verteilung für {params.label}]({params.label}_monte_carlo_histogramm.png)

---

## Detailierte Kosten- und Rebalancing-Daten

### Jährliche Kostenaufschlüsselung
{auswerten_kosten(df_kosten_det, params, params.label).to_markdown(index=False)}

### Rebalancing-Log (falls zutreffend)
{df_rebal.to_markdown(index=False) if df_rebal is not None else "Keine Rebalancing-Vorgänge aufgezeichnet."}

---
    """
    md_filename = f"{params.label}_Report.md"
    pdf_filename = f"{params.label}_Report.pdf"
    with open(md_filename, "w") as f:
        f.write(report_text)
    print(f"Report für '{params.label}' in '{md_filename}' erstellt.")

if __name__ == "__main__":
    params_depot = SparplanParameter(
        label="Depot 1",
        versicherung_modus=False,
        eintrittsalter=35,
        initial_investment=10000,
        monthly_investment=400,
        laufzeit=50,
        beitragszahldauer=30,
        monthly_dynamik_rate=0.0,
        dynamik_turnus_monate=12,
        sonderzahlung_jahr=0,
        sonderzahlung_betrag=0,
        regel_sonderzahlung_betrag=0,
        regel_sonderzahlung_turnus_jahre=0,
        annual_withdrawal=20000,
        annual_return=0.06,
        ausgabeaufschlag=0.002,
        ruecknahmeabschlag=0.002,
        ter=0.0045,
        serviceentgelt=0.0119,
        stueckkosten=45,
        abschlusskosten_einmalig_prozent=0.0,
        abschlusskosten_monatlich_prozent=0.0,
        verrechnungsdauer_monate=60,
        verwaltungskosten_monatlich_prozent=0.0,
        abgeltungssteuer_rate=0.25,
        soli_zuschlag_on_abgeltungssteuer=0.055,
        kirchensteuer_on_abgeltungssteuer=0.09,
        persoenlicher_steuersatz=0.3,
        freistellungsauftrag_jahr=0,
        teilfreistellung=0.3,
        basiszins=0.0255,
        rebalancing_rate=0.2,
        entnahme_modus="jährlich",
        bewertungsdauer=0,
        annual_std_dev=0.15
    )

    params_versicherung = SparplanParameter(
        label="Versicherung 1",
        versicherung_modus=True,
        eintrittsalter=35,
        initial_investment=10000,
        monthly_investment=400,
        laufzeit=50,
        beitragszahldauer=30,
        monthly_dynamik_rate=0.0,
        dynamik_turnus_monate=12,
        sonderzahlung_jahr=0,
        sonderzahlung_betrag=0,
        regel_sonderzahlung_betrag=0,
        regel_sonderzahlung_turnus_jahre=0,
        annual_withdrawal=20000,
        annual_return=0.06,
        ausgabeaufschlag=0.0,
        ruecknahmeabschlag=0.0,
        ter=0.0045,
        serviceentgelt=0.0018,
        stueckkosten=0.0,
        abschlusskosten_einmalig_prozent=0.025,
        abschlusskosten_monatlich_prozent=0.0252,
        verrechnungsdauer_monate=60,
        verwaltungskosten_monatlich_prozent=0.09,
        abgeltungssteuer_rate=0.25,
        soli_zuschlag_on_abgeltungssteuer=0.055,
        kirchensteuer_on_abgeltungssteuer=0.09,
        persoenlicher_steuersatz=0.3,
        freistellungsauftrag_jahr=0,
        teilfreistellung=0.0,
        basiszins=0.0,
        rebalancing_rate=0.0,
        entnahme_modus="jährlich",
        bewertungsdauer=35,
        annual_std_dev=0.15
    )

    params_diy = SparplanParameter(
        label="Depot DIY",
        versicherung_modus=False,
        eintrittsalter=35,
        initial_investment=10000,
        monthly_investment=400,
        laufzeit=50,
        beitragszahldauer=30,
        monthly_dynamik_rate=0.0,
        dynamik_turnus_monate=12,
        sonderzahlung_jahr=0,
        sonderzahlung_betrag=0,
        regel_sonderzahlung_betrag=0,
        regel_sonderzahlung_turnus_jahre=0,
        annual_withdrawal=20000,
        annual_return=0.06,
        ausgabeaufschlag=0.03,
        ruecknahmeabschlag=0.03,
        ter=0.005,
        serviceentgelt=0.0,
        stueckkosten=10.0,
        abschlusskosten_einmalig_prozent=0.0,
        abschlusskosten_monatlich_prozent=0.0,
        verrechnungsdauer_monate=60,
        verwaltungskosten_monatlich_prozent=0.0,
        abgeltungssteuer_rate=0.25,
        soli_zuschlag_on_abgeltungssteuer=0.055,
        kirchensteuer_on_abgeltungssteuer=0.09,
        persoenlicher_steuersatz=0.3,
        freistellungsauftrag_jahr=0,
        teilfreistellung=0.3,
        basiszins=0.0255,
        rebalancing_rate=0.1,
        entnahme_modus="jährlich",
        bewertungsdauer=15,
        annual_std_dev=0.15
    )

    params_list = [params_depot, params_versicherung, params_diy]
    df_list = []

    for params in params_list:
        print(f"\n--- Simulation für {params.label} ---")
        simulator = SparplanSimulator(params)
        df_kosten, rebalancing_log, cashflows = simulator.run_simulation()

        df_list.append(df_kosten)

        irr_annual = berechne_irr_und_print(cashflows, params.label)
        df_rebal = exportiere_rebalancing_daten(rebalancing_log, params.label)

        plotten_kosten(df_kosten, params)
        plotten_entnahmen(df_kosten, params)

        mc_results_tuple = run_monte_carlo(params, num_runs=100)

        erzeuge_report(df_kosten, df_rebal, irr_annual, mc_results_tuple, params)

    plotten_vergleich(df_list, params_list)