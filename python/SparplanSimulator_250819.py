# ==============================================================================
# SPARPPLANSIMULATOR
# ==============================================================================

# === IMPORTS ===
# Importe aller benötigten Bibliotheken und Module.
# `deque` für eine effiziente Warteschlange, `datetime` für Datumsberechnungen,
# `pandas` für die Datenverarbeitung und -analyse, `matplotlib` für die
# Diagrammerstellung und `pyxirr` für die XIRR-Berechnung.
from collections import deque
from dateutil.relativedelta import relativedelta
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import dataclasses
from typing import List, Dict, Any, Optional
import pyxirr

# === EINGANGSPARAMETER ALS DATENKLASSE ===
@dataclasses.dataclass
class SparplanParameter:
    """
    Dataclass, die alle Eingabeparameter für die Sparplansimulation kapselt.
    Dies sorgt für eine saubere und übersichtliche Struktur der Konfiguration.
    """
    label: str  # Eindeutige Bezeichnung für das Szenario (z.B. "Depot", "Versicherung")
    versicherung_modus: bool  # Steuert, ob eine Versicherungssimulation oder eine Depot-Simulation durchgeführt wird
    eintrittsalter: int  # Alter bei Simulationseintritt
    initial_investment: float  # Einmalige Anfangsinvestition
    monthly_investment: float  # Monatliche Sparrate
    laufzeit: int  # Gesamtlaufzeit des Sparplans in Jahren
    beitragszahldauer: int  # Dauer der monatlichen Einzahlungen in Jahren
    monthly_dynamik_rate: float  # Monatliche Dynamikrate der Sparrate
    dynamik_turnus_monate: int  # Turnus in Monaten, in dem die Dynamik angewendet wird
    sonderzahlung_jahr: float  # Jahr, in dem eine einmalige Sonderzahlung geleistet wird
    sonderzahlung_betrag: float  # Betrag der einmaligen Sonderzahlung
    regel_sonderzahlung_betrag: float  # Betrag einer regelmäßigen Sonderzahlung
    regel_sonderzahlung_turnus_jahre: int  # Turnus der regelmäßigen Sonderzahlungen in Jahren
    annual_withdrawal: float  # Jährliche Entnahme nach der Beitragsphase
    entnahme_plan: Optional[Dict[int, float]]  # Flexibler Entnahmeplan nach Jahr
    entnahme_modus: str  # "jährlich" oder "monatlich"
    annual_return: float  # Erwartete jährliche Nominalrendite
    ausgabeaufschlag: float  # Ausgabeaufschlag beim Kauf von Anteilen
    ruecknahmeabschlag: float  # Rücknahmeabschlag beim Verkauf von Anteilen
    ter: float  # Gesamtkostenquote des Fonds (Total Expense Ratio)
    serviceentgelt: float  # Jährliches Serviceentgelt (Depotgebühr)
    stueckkosten: float  # Jährliche Stückkosten pro Depot
    abschlusskosten_einmalig_prozent: float  # Einmalige prozentuale Abschlusskosten (Versicherung)
    abschlusskosten_monatlich_prozent: float  # Monatliche prozentuale Abschlusskosten (Versicherung)
    verrechnungsdauer_monate: int  # Dauer der Verrechnung der Abschlusskosten in Monaten
    verwaltungskosten_monatlich_prozent: float  # Monatliche prozentuale Verwaltungskosten (Versicherung)
    guthabenkosten: float  # Jährliche Kosten auf das Guthaben (Versicherung)
    abgeltungssteuer_rate: float  # Abgeltungssteuersatz
    soli_zuschlag_on_abgeltungssteuer: float  # Solidaritätszuschlag auf die Abgeltungssteuer
    kirchensteuer_on_abgeltungssteuer: float  # Kirchensteuer auf die Abgeltungssteuer
    persoenlicher_steuersatz: float  # Persönlicher Steuersatz für Versicherungen
    freistellungsauftrag_jahr: float  # Jährlicher Freistellungsbetrag
    teilfreistellung: float  # Teilfreistellungssatz für Investmentfonds
    basiszins: float  # Basiszinssatz für die Vorabpauschale
    rebalancing_rate: float  # Jährliche Rebalancing-Rate (als Prozentsatz des Depotwerts)
    bewertungsdauer: int  # Bewertungsdauer für Versicherungen
    inflation_rate: float  # Erwartete jährliche Inflationsrate
    inflation_volatility: float  # Volatilität der Inflation
    freistellungs_pauschbetrag_anpassung_rate: Optional[float] = 0.02  # Jährliche Anpassung des Freistellungsbetrags


class SparplanSimulator:
    """
    Hauptklasse, die die Simulation des Sparplans durchführt.
    Sie verwaltet den Portfolio-Zustand und führt die monatlichen
    Berechnungen durch.
    """

    def __init__(self, params: SparplanParameter, dynamic_returns: Optional[List[float]] = None):
        """
        Initialisiert den Simulator mit den Parametern und den Zählern für Kosten und Werte.
        """
        self.params = params
        self.dynamic_returns = dynamic_returns
        # `deque` effiziente, doppelseitige Matrix um die einzelnen Investitionen ("Tranchen") zu verfolgen für FIFO
        self.portfolio = deque()
        self.rebalancing_log = []
        self.monatliche_kosten_logs = []
        # Listen zur Speicherung der Cashflows und ihrer Daten für die XIRR-Berechnung.
        self.cashflows = []
        self.cashflow_dates = []
        self.real_cashflows = []

        # Kumulative Zähler für Kosten und Steuern (nominal)
        self.ausgabeaufschlag_summe = 0
        self.ruecknahmeabschlag_summe = 0
        self.stueckkosten_summe = 0
        self.abschlusskosten_summe = 0
        self.verwaltungskosten_summe = 0
        self.guthabenkosten_summe = 0
        self.ter_summe = 0
        self.serviceentgelt_summe = 0
        self.kumulierte_entnahmen = 0
        self.total_tax_paid = 0
        self.total_withdrawal_tax_paid = 0

        # Kumulative Zähler für Kosten und Steuern (real/inflationsbereinigt)
        self.ausgabeaufschlag_real_summe = 0
        self.ruecknahmeabschlag_real_summe = 0
        self.stueckkosten_real_summe = 0
        self.abschlusskosten_real_summe = 0
        self.verwaltungskosten_real_summe = 0
        self.guthabenkosten_real_summe = 0
        self.ter_real_summe = 0
        self.serviceentgelt_real_summe = 0
        self.kumulierte_entnahmen_real = 0
        self.total_tax_paid_real = 0
        self.total_withdrawal_tax_paid_real = 0

        self.freistellungs_topf = params.freistellungsauftrag_jahr
        self.monthly_investment = params.monthly_investment

        # Initialisierung der Versicherungskostenlogik (Verteilung über die Zeit)
        self.abschlusskosten_rest = 0.0
        self.verwaltungskosten_rest = 0.0
        self.kumulierte_inflation_factor = 1.0

        # Generierung monatlicher Inflationsraten auf Basis einer Normalverteilung
        self.monthly_inflation_rates = np.random.normal(
            loc=self.params.inflation_rate / 12,
            scale=self.params.inflation_volatility / np.sqrt(12),
            size=self.params.laufzeit * 12
        )

    def run_simulation(self) -> (pd.DataFrame, List[Dict[str, Any]], List[float], List[datetime.date]):
        """
        Führt die gesamte Sparplansimulation Monat für Monat durch.
        """
        self._initialisiere_simulation()
        for month in range(self.params.laufzeit * 12):
            self._simuliere_monat(month)
        self._finalisiere_simulation()
        df_kosten = pd.DataFrame(self.monatliche_kosten_logs)
        return df_kosten, self.rebalancing_log, self.cashflows, self.cashflow_dates, self.real_cashflows

    def _initialisiere_simulation(self):
        """
        Setzt die Anfangswerte für die Simulation, einschließlich des
        initialen Investments und der Berechnung der Versicherungskosten.
        """
        self.params.monthly_return = (1 + self.params.annual_return) ** (1 / 12) - 1
        self.params.full_tax_rate = self.params.abgeltungssteuer_rate * (
                1 + self.params.soli_zuschlag_on_abgeltungssteuer + self.params.kirchensteuer_on_abgeltungssteuer)

        # Logik für den Versicherungsmodus:
        if self.params.versicherung_modus:
            # Im Versicherungsmodus fallen keine Ausgabe-/Rücknahmeabschläge oder Stückkosten an.
            self.params.ausgabeaufschlag = 0.0
            self.params.ruecknahmeabschlag = 0.0
            self.params.stueckkosten = 0.0
            # Berechnung der Abschlusskosten, die über die Verrechnungsdauer verteilt werden.
            self.abschlusskosten_rest = (
                                                self.params.initial_investment * self.params.abschlusskosten_einmalig_prozent) + \
                                        (
                                                self.params.monthly_investment * self.params.beitragszahldauer * 12) * self.params.abschlusskosten_monatlich_prozent
        else:
            # Im Depot-Modus fallen keine Abschluss-/Verwaltungskosten oder Guthabenkosten an.
            self.params.abschlusskosten_einmalig_prozent = 0.0
            self.params.abschlusskosten_monatlich_prozent = 0.0
            self.params.verwaltungskosten_monatlich_prozent = 0.0
            self.params.guthabenkosten = 0.0

        # Verarbeitung der initialen Einzahlung
        aufschlag = self.params.initial_investment * self.params.ausgabeaufschlag
        nettobetrag = self.params.initial_investment - aufschlag
        self.ausgabeaufschlag_summe += aufschlag
        self.ausgabeaufschlag_real_summe += aufschlag / self.kumulierte_inflation_factor
        self.cashflows.append(-self.params.initial_investment)  # Negative Cashflow für die Investition
        self.real_cashflows.append(-self.params.initial_investment)
        self.cashflow_dates.append(datetime.date(2025, 1, 1))

        if nettobetrag > 0:
            # Erster Eintrag im Portfolio
            self.portfolio.append({
                "date": datetime.date(2025, 1, 1),
                "amount_invested": nettobetrag,
                "value": nettobetrag,
                "start_of_prev_year_value": nettobetrag,
                "vorabpauschalen_bereits_versteuert": 0.0
            })

    def _simuliere_monat(self, month: int):
        """
        Simuliert die Ereignisse eines einzelnen Monats (Zinsen, Kosten, Steuern).
        """
        current_date = datetime.date(2025, 1, 1) + relativedelta(months=month)
        is_january = current_date.month == 1

        if is_january:
            # Jährliche Anpassung des Freistellungsbetrags
            self.freistellungs_topf = self.params.freistellungsauftrag_jahr * (
                    1 + self.params.freistellungs_pauschbetrag_anpassung_rate) ** (
                                              current_date.year - 2025)

        self._handle_monthly_investment(month, current_date)
        self._handle_costs(month, current_date)

        # Anwenden der Rendite (entweder konstant oder dynamisch aus Monte-Carlo-Simulation)
        if self.dynamic_returns:
            monthly_return_val = self.dynamic_returns[month]
        else:
            monthly_return_val = self.params.monthly_return

        # Wertentwicklung des Portfolios
        for entry in self.portfolio:
            entry["value"] *= (1 + monthly_return_val)

        # Aktualisierung des kumulierten Inflationsfaktors
        self.kumulierte_inflation_factor *= (1 + self.monthly_inflation_rates[month])

        self._handle_taxes(current_date)
        self._handle_rebalancing(current_date)
        self._handle_withdrawals(month, current_date)

        # Ermittlung des aktuellen Depotwerts
        depotwert = sum(e["value"] for e in self.portfolio)
        depotwert_real = depotwert / self.kumulierte_inflation_factor

        # Hinzufügen der monatlichen Daten zum Log
        self.monatliche_kosten_logs.append({
            "Datum": current_date,
            "Depotwert": depotwert,
            "Depotwert real": depotwert_real,
            "Ausgabeaufschlag kum": self.ausgabeaufschlag_summe,
            "Ausgabeaufschlag kum real": self.ausgabeaufschlag_real_summe,
            "Rücknahmeabschlag kum": self.ruecknahmeabschlag_summe,
            "Rücknahmeabschlag kum real": self.ruecknahmeabschlag_real_summe,
            "Stückkosten kum": self.stueckkosten_summe,
            "Stückkosten kum real": self.stueckkosten_real_summe,
            "Gesamtfondkosten kum": self.ter_summe,
            "Gesamtfondkosten kum real": self.ter_real_summe,
            "Serviceentgelt kum": self.serviceentgelt_summe,
            "Serviceentgelt kum real": self.serviceentgelt_real_summe,
            "Guthabenkosten kum": self.guthabenkosten_summe,
            "Guthabenkosten kum real": self.guthabenkosten_real_summe,
            "Abschlusskosten kum": self.abschlusskosten_summe,
            "Abschlusskosten kum real": self.abschlusskosten_real_summe,
            "Verwaltungskosten kum": self.verwaltungskosten_summe,
            "Verwaltungskosten kum real": self.verwaltungskosten_real_summe,
            "Steuern kumuliert": self.total_tax_paid,
            "Steuern kumuliert real": self.total_tax_paid_real,
            "Steuern aus Entnahme": self.total_withdrawal_tax_paid,
            "Steuern aus Entnahme real": self.total_withdrawal_tax_paid_real,
            "Kumulierte Entnahmen": self.kumulierte_entnahmen,
            "Kumulierte Entnahmen real": self.kumulierte_entnahmen_real
        })

        if current_date.month == 12:
            # Speichert den Depotwert am Jahresende für die Berechnung der Vorabpauschale im nächsten Jahr
            for entry in self.portfolio:
                entry["start_of_prev_year_value"] = entry["value"]

    def _handle_monthly_investment(self, month, current_date):
        """
        Verarbeitet die monatlichen und einmaligen Investments sowie die Sparrate-Dynamik.
        """
        # Anpassung der Sparrate basierend auf der Dynamik
        if month > 0 and month % self.params.dynamik_turnus_monate == 0:
            self.monthly_investment *= (1 + self.params.monthly_dynamik_rate)

        is_einmalig = month == self.params.sonderzahlung_jahr * 12
        is_regelmaessig = (self.params.regel_sonderzahlung_turnus_jahre > 0 and month > 0 and month % (
                self.params.regel_sonderzahlung_turnus_jahre * 12) == 0)

        # Verarbeitung von Sonderzahlungen
        if is_einmalig or is_regelmaessig:
            # Logik zur Verarbeitung von Sonderzahlungen
            betrag = (self.params.sonderzahlung_betrag if is_einmalig else self.params.regel_sonderzahlung_betrag)
            if betrag > 0:
                self.cashflows.append(-betrag)
                self.real_cashflows.append(-betrag / self.kumulierte_inflation_factor)
                self.cashflow_dates.append(current_date)
                if not self.params.versicherung_modus:
                    aufschlag = betrag * self.params.ausgabeaufschlag
                    netto = betrag - aufschlag
                    self.ausgabeaufschlag_summe += aufschlag
                    self.ausgabeaufschlag_real_summe += aufschlag / self.kumulierte_inflation_factor
                    self.stueckkosten_summe += self.params.stueckkosten
                    self.stueckkosten_real_summe += self.params.stueckkosten / self.kumulierte_inflation_factor
                else:
                    netto = betrag
                self.portfolio.append(
                    {"date": current_date, "amount_invested": netto, "value": netto, "start_of_prev_year_value": netto,
                     "vorabpauschalen_bereits_versteuert": 0.0})

        # Verarbeitung der monatlichen Sparrate
        if month < self.params.beitragszahldauer * 12:
            aufschlag = self.monthly_investment * self.params.ausgabeaufschlag
            netto = self.monthly_investment - aufschlag
            self.ausgabeaufschlag_summe += aufschlag
            self.ausgabeaufschlag_real_summe += aufschlag / self.kumulierte_inflation_factor
            self.cashflows.append(-self.monthly_investment)
            self.real_cashflows.append(-self.monthly_investment / self.kumulierte_inflation_factor)
            self.cashflow_dates.append(current_date)
            self.portfolio.append(
                {"date": current_date, "amount_invested": netto, "value": netto, "start_of_prev_year_value": netto,
                 "vorabpauschalen_bereits_versteuert": 0.0})

    def _handle_costs(self, month, current_date):
        """
        Berechnet und zieht alle monatlichen und jährlichen Kosten ab.
        """
        depotwert = sum(e["value"] for e in self.portfolio) if self.portfolio else 0

        if not self.params.versicherung_modus and current_date.month == 1:
            # Jährliche Stückkosten (nur im Depot-Modus)
            if self.params.stueckkosten > 0:
                self.stueckkosten_summe += self.params.stueckkosten
                self.stueckkosten_real_summe += self.params.stueckkosten / self.kumulierte_inflation_factor
                self.cashflows.append(-self.params.stueckkosten)
                self.real_cashflows.append(-self.params.stueckkosten / self.kumulierte_inflation_factor)
                self.cashflow_dates.append(current_date)
                if depotwert > 0:
                    for entry in self.portfolio:
                        anteil = entry["value"] / depotwert
                        entry["value"] -= self.params.stueckkosten * anteil

        if depotwert > 0:
            # Monatliche Kosten basierend auf dem Depotwert (TER, Serviceentgelt, Guthabenkosten)
            fond_kosten = depotwert * self.params.ter / 12
            service_kosten = depotwert * self.params.serviceentgelt / 12
            guthaben_kosten = 0
            if self.params.versicherung_modus:
                guthaben_kosten = depotwert * self.params.guthabenkosten / 12

            total_kosten = fond_kosten + service_kosten + guthaben_kosten
            for entry in self.portfolio:
                entry["value"] -= total_kosten * (entry["value"] / depotwert)
            self.ter_summe += fond_kosten
            self.ter_real_summe += fond_kosten / self.kumulierte_inflation_factor
            self.serviceentgelt_summe += service_kosten
            self.serviceentgelt_real_summe += service_kosten / self.kumulierte_inflation_factor
            if self.params.versicherung_modus:
                self.guthabenkosten_summe += guthaben_kosten
                self.guthabenkosten_real_summe += guthaben_kosten / self.kumulierte_inflation_factor

        # Verarbeitung der Versicherungskosten
        if self.params.versicherung_modus:
            # Verteilte Abschlusskosten
            if month < self.params.verrechnungsdauer_monate and self.abschlusskosten_rest > 0:
                monatliche_abschlusskosten = self.abschlusskosten_rest / self.params.verrechnungsdauer_monate
                self.cashflows.append(-monatliche_abschlusskosten)
                self.real_cashflows.append(-monatliche_abschlusskosten / self.kumulierte_inflation_factor)
                self.cashflow_dates.append(current_date)
                if depotwert > 0:
                    for entry in self.portfolio:
                        anteil = entry["value"] / depotwert
                        entry["value"] -= monatliche_abschlusskosten * anteil
                self.abschlusskosten_summe += monatliche_abschlusskosten
                self.abschlusskosten_real_summe += monatliche_abschlusskosten / self.kumulierte_inflation_factor
            # Monatliche Verwaltungskosten (während der Einzahlungsphase)
            if month < self.params.beitragszahldauer * 12:
                monatliche_verwaltungskosten = self.monthly_investment * self.params.verwaltungskosten_monatlich_prozent
                self.cashflows.append(-monatliche_verwaltungskosten)
                self.real_cashflows.append(-monatliche_verwaltungskosten / self.kumulierte_inflation_factor)
                self.cashflow_dates.append(current_date)

                if depotwert > 0:
                    for entry in self.portfolio:
                        anteil = entry["value"] / depotwert
                        entry["value"] -= monatliche_verwaltungskosten * anteil
                self.verwaltungskosten_summe += monatliche_verwaltungskosten
                self.verwaltungskosten_real_summe += monatliche_verwaltungskosten / self.kumulierte_inflation_factor

    def _handle_taxes(self, current_date):
        """
        Berechnet und zieht Steuern ab. Im Depot-Modus wird die Vorabpauschale
        jährlich im Januar berechnet.
        """
        is_january = current_date.month == 1
        if not self.params.versicherung_modus and is_january:
            for entry in self.portfolio:
                start_value = entry.get("start_of_prev_year_value", 0.0)
                # Berechnung des fiktiven Ertrags nach dem Basiszinssatz
                fiktiver_ertrag = start_value * self.params.basiszins
                # Realisierter Ertrag seit dem Jahresanfang
                real_ertrag = entry["value"] - start_value
                # Der steuerbare Ertrag ist der kleinere der beiden Werte
                steuerbarer_ertrag = min(fiktiver_ertrag, real_ertrag)

                steuerfreibetrag_verfuegbar = self.freistellungs_topf
                zu_versteuern_temp = steuerbarer_ertrag * (1 - self.params.teilfreistellung)

                steuerfreibetrag_used = min(steuerfreibetrag_verfuegbar, max(0, zu_versteuern_temp))
                self.freistellungs_topf -= steuerfreibetrag_used

                zu_versteuern = max(0, zu_versteuern_temp - steuerfreibetrag_used)
                steuer = zu_versteuern * self.params.full_tax_rate

                if steuer > 0:
                    # Die Steuer wird direkt aus dem Portfolio-Wert abgezogen
                    entry["value"] -= steuer
                    self.cashflows.append(-steuer)
                    self.real_cashflows.append(-steuer / self.kumulierte_inflation_factor)
                    self.cashflow_dates.append(current_date)
                    # Der versteuerte Betrag wird im Eintrag vermerkt, um Doppelbesteuerung zu vermeiden
                    entry["vorabpauschalen_bereits_versteuert"] += zu_versteuern
                    self.total_tax_paid += steuer
                    self.total_tax_paid_real += steuer / self.kumulierte_inflation_factor

    def _handle_rebalancing(self, current_date):
        """
        Führt ein jährliches Rebalancing durch, indem Anteile verkauft und
        wieder reinvestiert werden. Steuern werden hierbei abgeführt.
        """
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

                    steuer = max(0.0, (steuerbarer_gewinn - steuerfreibetrag) * self.params.full_tax_rate)

                    ruecknahmeabschlag = sell_value * self.params.ruecknahmeabschlag
                    netto_reinvest = sell_value - steuer - ruecknahmeabschlag

                    self.total_tax_paid += steuer
                    self.total_tax_paid_real += steuer / self.kumulierte_inflation_factor
                    self.ruecknahmeabschlag_summe += ruecknahmeabschlag
                    self.ruecknahmeabschlag_real_summe += ruecknahmeabschlag / self.kumulierte_inflation_factor
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
        """
        Verarbeitet die jährlichen oder monatlichen Entnahmen.
        """
        if month < self.params.beitragszahldauer * 12:
            # Entnahmen beginnen erst nach der Beitragsphase
            return

        depotwert = sum(e["value"] for e in self.portfolio)
        entnahmebetrag_jahr = 0

        withdrawal_year = (current_date.year - datetime.date(2025, 1, 1).year) - self.params.beitragszahldauer + 1

        # Logik, um den korrekten Entnahmebetrag basierend auf dem Entnahmeplan zu finden
        if self.params.entnahme_plan:
            sorted_years = sorted(self.params.entnahme_plan.keys(), reverse=True)
            for plan_year in sorted_years:
                if withdrawal_year >= plan_year:
                    entnahmebetrag_jahr = self.params.entnahme_plan[plan_year]
                    break
        elif self.params.annual_withdrawal:
            entnahmebetrag_jahr = self.params.annual_withdrawal

        if entnahmebetrag_jahr <= 0:
            return

        entnahmebetrag = 0
        if self.params.entnahme_modus == "jährlich" and current_date.month == 1:
            entnahmebetrag = entnahmebetrag_jahr
        elif self.params.entnahme_modus == "monatlich":
            entnahmebetrag = entnahmebetrag_jahr / 12

        if entnahmebetrag <= 0 or depotwert < entnahmebetrag:
            return

        remaining_to_withdraw = entnahmebetrag
        netto_entnahme_summe = 0
        total_withdrawal_tax_this_year = 0

        temp_queue = deque()

        # Entnahme der ältesten Anteile zuerst (First-In, First-Out)
        while remaining_to_withdraw > 1e-9 and self.portfolio:
            oldest_entry = self.portfolio.popleft()
            if oldest_entry["value"] <= 0:
                continue

            sell_value = min(oldest_entry["value"], remaining_to_withdraw)
            anteil = sell_value / oldest_entry["value"]

            gewinn_anteil = (oldest_entry["value"] - oldest_entry["amount_invested"]) * anteil
            investiert_anteil = oldest_entry["amount_invested"] * anteil

            # Spezifische Steuerlogik für Versicherungen
            if self.params.versicherung_modus:
                aktuelle_laufzeit = (current_date - oldest_entry["date"]).days / 365.25
                aktuelle_alter = self.params.eintrittsalter + (
                        current_date - datetime.date(2025, 1, 1)).days / 365.25

                # Nach 12 Jahren Laufzeit und Alter 62 gilt die 50%-Steuerregelung
                if aktuelle_alter >= 62 and aktuelle_laufzeit >= 12:
                    steuer = gewinn_anteil * 0.5 * self.params.persoenlicher_steuersatz
                else:
                    steuer = gewinn_anteil * 0.85 * self.params.persoenlicher_steuersatz
            else:  # Steuerlogik für Depots
                vorabpauschalen_anteil = oldest_entry["vorabpauschalen_bereits_versteuert"] * anteil
                steuerbarer_gewinn = gewinn_anteil * (1 - self.params.teilfreistellung)

                steuerbarer_gewinn_nach_vp = max(0.0, steuerbarer_gewinn - vorabpauschalen_anteil)

                steuerfreibetrag_used = min(self.freistellungs_topf, steuerbarer_gewinn_nach_vp)
                self.freistellungs_topf -= steuerfreibetrag_used

                steuer = max(0.0, (steuerbarer_gewinn - steuerfreibetrag_used) * self.params.full_tax_rate)

                oldest_entry["vorabpauschalen_bereits_versteuert"] -= vorabpauschalen_anteil

            ruecknahmeabschlag = sell_value * self.params.ruecknahmeabschlag

            netto_entnahme = sell_value - steuer - ruecknahmeabschlag
            netto_entnahme_summe += netto_entnahme
            total_withdrawal_tax_this_year += steuer

            oldest_entry["value"] -= sell_value
            oldest_entry["amount_invested"] -= investiert_anteil

            if oldest_entry["value"] > 1e-9:
                temp_queue.append(oldest_entry)

            remaining_to_withdraw -= sell_value

        self.portfolio = deque(list(temp_queue) + list(self.portfolio))

        self.total_tax_paid += total_withdrawal_tax_this_year
        self.total_tax_paid_real += total_withdrawal_tax_this_year / self.kumulierte_inflation_factor
        self.total_withdrawal_tax_paid += total_withdrawal_tax_this_year
        self.total_withdrawal_tax_paid_real += total_withdrawal_tax_this_year / self.kumulierte_inflation_factor
        self.ruecknahmeabschlag_summe += entnahmebetrag * self.params.ruecknahmeabschlag
        self.ruecknahmeabschlag_real_summe += (
                                                      entnahmebetrag * self.params.ruecknahmeabschlag) / self.kumulierte_inflation_factor
        self.kumulierte_entnahmen += netto_entnahme_summe
        self.kumulierte_entnahmen_real += netto_entnahme_summe / self.kumulierte_inflation_factor
        self.cashflows.append(netto_entnahme_summe)  # Positive Cashflow für die Entnahme
        self.real_cashflows.append(netto_entnahme_summe / self.kumulierte_inflation_factor)
        self.cashflow_dates.append(current_date)

    def _finalisiere_simulation(self):
        """
        Führt die letzten Berechnungen am Ende der Gesamtlaufzeit durch,
        einschließlich der Versteuerung des Restwerts.
        """
        depotwert_final = sum(e["value"] for e in self.portfolio)
        depotwert_final_real = depotwert_final / self.kumulierte_inflation_factor

        self.monatliche_kosten_logs.append({
            "Datum": datetime.date(2025, 1, 1) + relativedelta(months=self.params.laufzeit * 12),
            "Depotwert": depotwert_final,
            "Depotwert real": depotwert_final_real,
            "Ausgabeaufschlag kum": self.ausgabeaufschlag_summe,
            "Ausgabeaufschlag kum real": self.ausgabeaufschlag_real_summe,
            "Rücknahmeabschlag kum": self.ruecknahmeabschlag_summe,
            "Rücknahmeabschlag kum real": self.ruecknahmeabschlag_real_summe,
            "Stückkosten kum": self.stueckkosten_summe,
            "Stückkosten kum real": self.stueckkosten_real_summe,
            "Gesamtfondkosten kum": self.ter_summe,
            "Gesamtfondkosten kum real": self.ter_real_summe,
            "Serviceentgelt kum": self.serviceentgelt_summe,
            "Serviceentgelt kum real": self.serviceentgelt_real_summe,
            "Guthabenkosten kum": self.guthabenkosten_summe,
            "Guthabenkosten kum real": self.guthabenkosten_real_summe,
            "Abschlusskosten kum": self.abschlusskosten_summe,
            "Abschlusskosten kum real": self.abschlusskosten_real_summe,
            "Verwaltungskosten kum": self.verwaltungskosten_summe,
            "Verwaltungskosten kum real": self.verwaltungskosten_real_summe,
            "Steuern kumuliert": self.total_tax_paid,
            "Steuern kumuliert real": self.total_tax_paid_real,
            "Steuern aus Entnahme": self.total_withdrawal_tax_paid,
            "Steuern aus Entnahme real": self.total_withdrawal_tax_paid_real,
            "Kumulierte Entnahmen": self.kumulierte_entnahmen,
            "Kumulierte Entnahmen real": self.kumulierte_entnahmen_real
        })

        # Berechnung der Steuer auf den finalen Restwert
        restwert = sum(e["value"] for e in self.portfolio)
        if restwert > 1e-9:
            investiert = sum(e["amount_invested"] for e in self.portfolio)
            gewinn = max(0.0, restwert - investiert)
            steuer = 0

            if self.params.versicherung_modus:
                # Steuer auf den Gewinn nach Laufzeit- und Altersregeln
                aktuelle_laufzeit = self.params.laufzeit
                aktuelle_alter = self.params.eintrittsalter + aktuelle_laufzeit
                if aktuelle_alter >= 62 and aktuelle_laufzeit >= 12:
                    steuer = gewinn * 0.5 * self.params.persoenlicher_steuersatz
                else:
                    steuer = gewinn * 0.85 * self.params.persoenlicher_steuersatz
            else:
                # Steuer auf den Gewinn nach Teilfreistellung und Vorabpauschale
                steuerbar = gewinn * (1 - self.params.teilfreistellung)
                bereits_versteuert = sum(e.get("vorabpauschalen_bereits_versteuert", 0.0) for e in self.portfolio)
                steuerbar = max(0.0, steuerbar - bereits_versteuert)
                steuer = steuerbar * self.params.full_tax_rate
                self.total_withdrawal_tax_paid += steuer
                self.total_withdrawal_tax_paid_real += steuer / self.kumulierte_inflation_factor

            ruecknahmeabschlag = restwert * self.params.ruecknahmeabschlag
            self.total_tax_paid += steuer
            self.total_tax_paid_real += steuer / self.kumulierte_inflation_factor
            self.ruecknahmeabschlag_summe += ruecknahmeabschlag
            self.ruecknahmeabschlag_real_summe += ruecknahmeabschlag / self.kumulierte_inflation_factor
            restwert_net = restwert - steuer - ruecknahmeabschlag
            self.cashflows.append(restwert_net)
            self.real_cashflows.append(restwert_net / self.kumulierte_inflation_factor)
            self.cashflow_dates.append(datetime.date(2025, 1, 1) + relativedelta(months=self.params.laufzeit * 12))
            self.kumulierte_entnahmen += restwert_net
            self.kumulierte_entnahmen_real += restwert_net / self.kumulierte_inflation_factor


# === HILFSFUNKTIONEN SIND NICHT TEIL DER KLASSEN ===
def berechne_xirr_und_print(cashflows, dates, real_cashflows, label):  # HILFSFUNKTION für XIRR
    """
    Berechnet den internen Zinsfuß (XIRR) für nominale und reale Cashflows.
    Der XIRR ist ein Maß für die effektive jährliche Rendite.
    Die Ergebnisse werden direkt in der Konsole ausgegeben.
    """
    xirr_nominal = None
    xirr_real = None
    try:
        # XIRR berechnen
        xirr_nominal = pyxirr.xirr(dates, cashflows)
        print(f"Effektive Nettorendite (XIRR) nominal für {label}: {xirr_nominal:.2%}")
    except Exception as e:
        # Fehlermeldung, falls die Berechnung fehlschlägt
        print(f"Warnung: Nominale XIRR-Berechnung für {label} fehlgeschlagen. Grund: {e}")

    try:
        # realen (inflationsbereinigten) XIRR berechnen
        xirr_real = pyxirr.xirr(dates, real_cashflows)
        print(f"Effektive Nettorendite (XIRR) real für {label}: {xirr_real:.2%}")
    except Exception as e:
        # Fehlermeldung, falls die Berechnung fehlschlägt
        print(f"Warnung: Reale XIRR-Berechnung für {label} fehlgeschlagen. Grund: {e}")

    return xirr_nominal, xirr_real


def auswerten_kosten(df_kosten: pd.DataFrame, params: SparplanParameter, label: str) -> pd.DataFrame:
    """
    Bereitet die monatlichen Kosten- und Depotwerte für die jährliche
    Auswertung auf. Gruppiert die Daten nach Jahren und berechnet
    die kumulierten Werte am Ende jedes Jahres.
    """
    df_kosten["Jahr"] = pd.to_datetime(df_kosten["Datum"]).dt.year
    numerische_spalten = df_kosten.drop(columns=["Datum", "Jahr"]).select_dtypes(include="number").columns
    # Kumuliert die letzten Werte jedes Jahres
    kosten_jahr_detail = df_kosten.groupby("Jahr")[numerische_spalten].last().reset_index()

    spalten_kum = ["Ausgabeaufschlag kum", "Rücknahmeabschlag kum", "Stückkosten kum", "Serviceentgelt kum",
                   "Gesamtfondkosten kum", "Guthabenkosten kum", "Abschlusskosten kum", "Verwaltungskosten kum",
                   "Steuern kumuliert", "Steuern aus Entnahme", "Kumulierte Entnahmen", "Depotwert", "Depotwert real"]
    spalten_kum_real = ["Ausgabeaufschlag kum real", "Rücknahmeabschlag kum real", "Stückkosten kum real",
                        "Serviceentgelt kum real",
                        "Gesamtfondkosten kum real", "Guthabenkosten kum real", "Abschlusskosten kum real",
                        "Verwaltungskosten kum real",
                        "Steuern kumuliert real", "Steuern aus Entnahme real", "Kumulierte Entnahmen real"]

    alle_spalten = spalten_kum + spalten_kum_real

    # 'NAV-Kosten real' nur im Versicherungsmodus
    if params.versicherung_modus:
        kosten_jahr_detail.rename(columns={
            "Serviceentgelt kum": "NAV-Kosten kum",
            "Serviceentgelt kum real": "NAV-Kosten kum real",
        }, inplace=True)

    # NEU: Kumulierung der Verwaltungskosten und Guthabenkosten
    if params.versicherung_modus:
        kosten_jahr_detail["Versicherungskosten kum"] = kosten_jahr_detail["Guthabenkosten kum"] + kosten_jahr_detail[
            "Verwaltungskosten kum"]
        kosten_jahr_detail["Versicherungskosten kum real"] = kosten_jahr_detail["Guthabenkosten kum real"] + \
                                                             kosten_jahr_detail["Verwaltungskosten kum real"]

    for spalte in alle_spalten:
        if spalte not in kosten_jahr_detail:
            kosten_jahr_detail[spalte] = 0

    kosten_jahr_detail["Kosten Kapitalanlage"] = kosten_jahr_detail["Gesamtfondkosten kum"]
    kosten_jahr_detail["Kosten Kapitalanlage real"] = kosten_jahr_detail["Gesamtfondkosten kum real"]

    # Auswahl der korrekten Service-Spalte basierend auf dem Modus
    service_spalte = "Serviceentgelt kum"
    service_spalte_real = "Serviceentgelt kum real"
    if params.versicherung_modus:
        service_spalte = "NAV-Kosten kum"
        service_spalte_real = "NAV-Kosten kum real"

    kosten_jahr_detail["Kosten Service"] = kosten_jahr_detail[service_spalte]
    kosten_jahr_detail["Kosten Service real"] = kosten_jahr_detail[service_spalte_real]

    if params.versicherung_modus:
        # Hier werden die Kosten für den Versicherungsmodus zusammengefasst.
        kosten_jahr_detail["Kosten Depot"] = kosten_jahr_detail["Ausgabeaufschlag kum"] + kosten_jahr_detail[
            "Rücknahmeabschlag kum"]
        kosten_jahr_detail["Kosten Depot real"] = kosten_jahr_detail["Ausgabeaufschlag kum real"] + kosten_jahr_detail[
            "Rücknahmeabschlag kum real"]
        kosten_jahr_detail["Kosten Versicherung"] = kosten_jahr_detail["Guthabenkosten kum"] + kosten_jahr_detail[
            "Verwaltungskosten kum"]
        kosten_jahr_detail["Kosten Versicherung real"] = kosten_jahr_detail["Guthabenkosten kum real"] + \
                                                         kosten_jahr_detail["Verwaltungskosten kum real"]
    else:
        # Hier werden die Kosten für den Depot-Modus zusammengefasst.
        kosten_jahr_detail["Kosten Depot"] = kosten_jahr_detail["Ausgabeaufschlag kum"] + kosten_jahr_detail[
            "Rücknahmeabschlag kum"] + kosten_jahr_detail["Stückkosten kum"]
        kosten_jahr_detail["Kosten Depot real"] = kosten_jahr_detail["Ausgabeaufschlag kum real"] + kosten_jahr_detail[
            "Rücknahmeabschlag kum real"] + kosten_jahr_detail["Stückkosten kum real"]
        kosten_jahr_detail["Kosten Versicherung"] = 0
        kosten_jahr_detail["Kosten Versicherung real"] = 0

    kosten_jahr_detail = kosten_jahr_detail.round(2)
    kosten_jahr_detail.to_csv(f"{label}_Kostenarten_Jahr.csv", index=False)
    print(f"Kostenaufschlüsselung für '{label}' in '{label}_Kostenarten_Jahr.csv' exportiert.")
    return kosten_jahr_detail


def plotten_kosten(df_kosten, params):
    """
    Erstellt ein gestapeltes Flächendiagramm der kumulierten Kosten pro Jahr.
    """
    df_kosten["Jahr"] = pd.to_datetime(df_kosten["Datum"]).dt.year
    # `last()` wird verwendet, um die kumulierten Werte am Jahresende zu erhalten
    df_kum_kosten = df_kosten.groupby("Jahr").last().reset_index()

    kosten_spalten = []
    if params.versicherung_modus:
        # Kombinierte Spalte für Versicherungskosten
        df_kosten["Versicherungskosten kum"] = df_kosten["Guthabenkosten kum"] + df_kosten["Verwaltungskosten kum"]
        df_kum_kosten["Versicherungskosten kum"] = df_kum_kosten["Guthabenkosten kum"] + df_kum_kosten[
            "Verwaltungskosten kum"]

        # Liste der anzuzeigenden Spalten
        kosten_spalten = ["Abschlusskosten kum", "Versicherungskosten kum", "NAV-Kosten kum", "Gesamtfondkosten kum",
                          "Steuern kumuliert"]
        df_kosten.rename(columns={
            "Serviceentgelt kum": "NAV-Kosten kum",
        }, inplace=True)
        df_kum_kosten.rename(columns={
            "Serviceentgelt kum": "NAV-Kosten kum",
        }, inplace=True)
    else:
        # Alte Logik für Depot
        kosten_spalten = ["Ausgabeaufschlag kum", "Rücknahmeabschlag kum", "Stückkosten kum", "Gesamtfondkosten kum",
                          "Steuern kumuliert", "Serviceentgelt kum"]

    df_kosten_plot = df_kum_kosten[[col for col in kosten_spalten if col in df_kum_kosten.columns] + ["Jahr"]]
    df_kosten_plot.index = df_kosten_plot["Jahr"]
    df_kosten_plot = df_kosten_plot.drop(columns="Jahr")

    plt.figure(figsize=(14, 8))
    df_kosten_plot.plot(kind="area", stacked=True, ax=plt.gca(), legend=False)

    handles, labels = plt.gca().get_legend_handles_labels()

    labels_ger = {
        "Versicherungskosten kum": "Versicherungskosten",
        "Abschlusskosten kum": "Abschlusskosten",
        "Verwaltungskosten kum": "Verwaltungskosten",
        "Guthabenkosten kum": "Guthabenkosten",
        "Ausgabeaufschlag kum": "Ausgabeaufschlag",
        "Rücknahmeabschlag kum": "Rücknahmeabschlag",
        "Stückkosten kum": "Stückkosten",
        "Gesamtfondkosten kum": "Gesamtfondkosten (TER)",
        "Steuern kumuliert": "Steuern",
        "Steuern aus Entnahme": "Steuern aus Entnahme",
        "NAV-Kosten kum": "NAV-Kosten",
        "Serviceentgelt kum": "Serviceentgelt"
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


def plotten_vergleich(df_list, params_list):
    """
    Erstellt ein Liniendiagramm zum Vergleich der Depotentwicklung
    (nominal und real) über die Zeit.
    """
    plt.figure(figsize=(14, 8))
    for df, params in zip(df_list, params_list):
        df["Jahr"] = pd.to_datetime(df["Datum"]).dt.year
        df_vergleich = df.groupby("Jahr").last().reset_index()
        # Plotten der nominalen und realen Depotwerte
        plt.plot(df_vergleich['Jahr'], df_vergleich['Depotwert'], label=f"{params.label} (nominal)", linewidth=2)
        plt.plot(df_vergleich['Jahr'], df_vergleich['Depotwert real'], label=f"{params.label} (real)", linewidth=2,
                 linestyle="--")

    plt.xlabel("Jahr")
    plt.ylabel("Depotwert in Euro")
    plt.title("Vergleich der Depotentwicklung")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("vergleich_depotentwicklung.png")
    plt.close()


def plotten_entnahmen(df_kosten, params):
    """
    Erstellt ein Liniendiagramm der kumulierten Entnahmen pro Jahr.
    """
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


def exportiere_rebalancing_daten(rebalancing_log, label):
    """
    Exportiert das Rebalancing-Protokoll in eine CSV-Datei.
    """
    if rebalancing_log:
        df_rebal = pd.DataFrame(rebalancing_log)
        df_rebal.to_csv(f"{label}_Rebalancing.csv", index=False)
        return df_rebal
    return None


def run_monte_carlo(params, num_runs, std_dev):
    """
    Führt eine Monte-Carlo-Simulation durch, um das Renditerisiko zu bewerten.
    Es werden zufällige jährliche Renditen generiert und die Simulation
    mehrfach mit diesen Renditen durchgeführt.
    """
    print(f"\nStarte Monte-Carlo-Simulation für '{params.label}' mit {num_runs} Durchläufen...")
    final_values = []
    annual_return_logs = []

    end_of_beitrags_period_index = params.beitragszahldauer * 12
    if end_of_beitrags_period_index >= params.laufzeit * 12:
        end_of_beitrags_period_index = (params.laufzeit * 12) - 1

    for i in range(num_runs):
        # Generiert jährliche Renditen aus einer Normalverteilung
        random_annual_returns = np.random.normal(params.annual_return, std_dev, params.laufzeit)
        annual_return_logs.append(random_annual_returns.tolist())
        # Konvertiert die jährlichen Renditen in monatliche
        monthly_returns = [(1 + r) ** (1 / 12) - 1 for r in random_annual_returns for _ in range(12)]

        mc_params = dataclasses.replace(params)
        simulator = SparplanSimulator(mc_params, dynamic_returns=monthly_returns)
        df_kosten, _, _, _, _ = simulator.run_simulation()

        final_values.append(df_kosten["Depotwert"].iloc[end_of_beitrags_period_index])

    mean_value = np.mean(final_values)
    median_value = np.median(final_values)
    # Berechnet das 95%-Konfidenzintervall (2.5. und 97.5. Perzentil)
    ci_lower = np.percentile(final_values, 2.5)
    ci_upper = np.percentile(final_values, 97.5)

    df_returns = pd.DataFrame(annual_return_logs).T
    df_returns.columns = [f"Simulation_{i + 1}" for i in range(num_runs)]
    df_returns.index.name = "Jahr"
    df_returns.to_csv(f"{params.label}_monte_carlo_returns.csv")
    print(f"Jährliche Renditen der Monte-Carlo-Durchläufe in '{params.label}_monte_carlo_returns.csv' exportiert.")

    # Erstellt ein Histogramm der Endwerte
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


def erzeuge_report(df_kosten_det, df_rebal, xirr_nominal, xirr_real, mc_results, params):
    """
    Generiert einen umfassenden Markdown-Report mit den Simulationsergebnissen
    und den Links zu den generierten Diagrammen und Tabellen.
    """
    xirr_nominal_formatted = f"{xirr_nominal:.2%}" if xirr_nominal is not None else "Berechnung fehlgeschlagen"
    xirr_real_formatted = f"{xirr_real:.2%}" if xirr_real is not None else "Berechnung fehlgeschlagen"

    end_beitragsdauer_index = min(params.beitragszahldauer * 12 - 1, len(df_kosten_det) - 1)
    depotwert_ende_beitrags = df_kosten_det['Depotwert'].iloc[end_beitragsdauer_index]
    depotwert_ende_beitrags_real = df_kosten_det['Depotwert real'].iloc[end_beitragsdauer_index]

    report_text = f"""
# Report für {params.label}

---

## Ergebnisse der Simulation
### Deterministische Simulation
* **Depotwert am Ende der Einzahlungsphase (nominal):** {depotwert_ende_beitrags:,.2f} €
* **Depotwert am Ende der Einzahlungsphase (real):** {depotwert_ende_beitrags_real:,.2f} €
* **Finaler Depotwert am Ende der Laufzeit (nominal):** {df_kosten_det['Depotwert'].iloc[-1]:,.2f} €
* **Finaler Depotwert am Ende der Laufzeit (real):** {df_kosten_det['Depotwert real'].iloc[-1]:,.2f} €
* **Effektive Nettorendite (XIRR) nominal:** {xirr_nominal_formatted}
* **Effektive Nettorendite (XIRR) real:** {xirr_real_formatted}

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
{df_kosten_det.to_markdown(index=False)}

### Rebalancing-Log (falls zutreffend)
{df_rebal.to_markdown(index=False) if df_rebal is not None else "Keine Rebalancing-Vorgänge aufgezeichnet."}

---
    """
    md_filename = f"{params.label}_Report.md"
    with open(md_filename, "w") as f:
        f.write(report_text)
    print(f"Report für '{params.label}' in '{md_filename}' erstellt.")


if __name__ == "__main__":
    """
    Hauptausführungsblock des Programms.
    Hier werden die Parameter für die verschiedenen Szenarien definiert,
    die Simulationen gestartet und die Ergebnisse generiert.
    """
    all_scenarios = []

    # Konfiguration für die Monte-Carlo-Simulation
    MONTE_CARLO_RUNS = 5
    MONTE_CARLO_STD_DEV = 0.10

    # Szenario 1: Depot
    params_depot = SparplanParameter(
        label="Depot",
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
        annual_withdrawal=0,
        entnahme_plan={1: 20000, 11: 20000},
        entnahme_modus="jährlich",
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
        guthabenkosten=0.0,
        abgeltungssteuer_rate=0.25,
        soli_zuschlag_on_abgeltungssteuer=0.055,
        kirchensteuer_on_abgeltungssteuer=0.09,
        persoenlicher_steuersatz=0.3,
        freistellungsauftrag_jahr=0,
        teilfreistellung=0.3,
        basiszins=0.0255,
        rebalancing_rate=0.2,
        bewertungsdauer=0,
        inflation_rate=0.02,
        inflation_volatility=0.01,
        freistellungs_pauschbetrag_anpassung_rate=0.02
    )
    all_scenarios.append(params_depot)

    # Szenario 2: Versicherung
    params_versicherung = SparplanParameter(
        label="Versicherung",
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
        annual_withdrawal=0,
        entnahme_plan={1: 20000, 11: 20000},
        entnahme_modus="jährlich",
        annual_return=0.06,
        ausgabeaufschlag=0.0,
        ruecknahmeabschlag=0.0,
        ter=0.0045,
        serviceentgelt=0.1,  # NAVKOSTEN
        guthabenkosten=0.0018,
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
        bewertungsdauer=35,
        inflation_rate=0.02,
        inflation_volatility=0.01,
        freistellungs_pauschbetrag_anpassung_rate=0.02
    )
    all_scenarios.append(params_versicherung)

    # Szenario 3: Depot DIY
    params_depot_diy = SparplanParameter(
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
        annual_withdrawal=0,
        entnahme_plan={1: 20000, 11: 20000},
        entnahme_modus="jährlich",
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
        guthabenkosten=0.0,
        abgeltungssteuer_rate=0.25,
        soli_zuschlag_on_abgeltungssteuer=0.055,
        kirchensteuer_on_abgeltungssteuer=0.09,
        persoenlicher_steuersatz=0.3,
        freistellungsauftrag_jahr=0,
        teilfreistellung=0.3,
        basiszins=0.0255,
        rebalancing_rate=0.1,
        bewertungsdauer=0,
        inflation_rate=0.02,
        inflation_volatility=0.01,
        freistellungs_pauschbetrag_anpassung_rate=0.02
    )
    all_scenarios.append(params_depot_diy)

    df_results = []
    xirr_list = []

    # Haupt-Loop zur Durchführung der Simulationen für jedes Szenario
    for params in all_scenarios:
        print(f"\n--- Simulation für {params.label} gestartet ---")
        simulator = SparplanSimulator(params)
        df_kosten, rebalancing_log, cashflows, cashflow_dates, real_cashflows = simulator.run_simulation()
        xirr_nominal, xirr_real = berechne_xirr_und_print(cashflows, cashflow_dates, real_cashflows, params.label)
        df_results.append(df_kosten)
        xirr_list.append((xirr_nominal, xirr_real))

        # Aufruf der Analyse- und Plot-Funktionen
        df_kosten_detail = auswerten_kosten(df_kosten.copy(), params, params.label)
        rebal_df = exportiere_rebalancing_daten(rebalancing_log, params.label)
        plotten_kosten(df_kosten, params)
        plotten_entnahmen(df_kosten, params)

        mc_results = run_monte_carlo(params, MONTE_CARLO_RUNS, MONTE_CARLO_STD_DEV)
        erzeuge_report(df_kosten_detail, rebal_df, xirr_nominal, xirr_real, mc_results, params)

        print(f"--- Simulation für {params.label} beendet ---")

    # Plotten des Vergleichsdiagramms für alle Szenarien
    plotten_vergleich(df_results, all_scenarios)

    """
    Gespräch Sebastian:
     Inflationsbereinigt Werte reduzieren, 2 Ausgaben für nominal und real, evtl Freibeträge erhöhen'
     'Entnahme ändern auf das man es wechseln kann, bspw von 20000 zu beginn auf 10000 nach 10 Jahren'
     'Entnahme auch Inflationsbereingit die Möglichkeit geben'
     Diagramm mit Service/Verwaltungskosten anpassen
     'Monte Carlo komplett neue Simulation'
     'Es werden aus historischen Kursdaten die rendite und volatilität bestimmt, daraus kann man dann entweder stochastisch die Zukunftswerte bestimmen oder historical Werte neu mischen'
     'Die Werte aus der MC Sim müssten dann in die SparplanSim übernommen werden können'
     'Historische Werte aus my.dimensional.com Login Tools Returns Web MyCustom Bauer Portfolios. Könnte ich mir auch über Python Bibliotheken wie yfinancial ausgeben lassen, da könnte ich auch Fonds erstellen und historische Kurse her bekommen'
     'MC Sim dann im sinne von portfoliovisualizer.com mymodels saved portfolios und Tools Monte Carlo Sim, da steht das uach erklärt mit Historical und Forecastet Returns'
     'In einer Monte-Carlo-Simulation zum Kursverlauf eines ETF ist das 10. Perzentil die Grenze, unter die 10 % aller simulierten Ergebnisse fallen. 10 % der Simulationen endeten in einem Szenario, das schlechter war als dieser Wert. 90 % der Simulationen endeten in einem Szenario, das besser war als dieser Wert'
     'time weighted rate of return nominal und real- zeitgewichtet rendite(real abzüglich inflationsrate), annual mean return (jährliche durchschnittsrendite), annualized volatility'
    """
