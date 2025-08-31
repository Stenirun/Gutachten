# ==============================================================================
# Gutachten250817.py
#
# Beschreibung:
# Dieses Skript dient als leistungsstarkes Werkzeug zur Finanzmodellierung.
# Es simuliert, wie sich verschiedene Sparpläne (wie ein Depot oder eine
# Versicherung) über lange Zeiträume entwickeln. Dabei werden alle wichtigen
# Faktoren berücksichtigt, wie Einzahlungen, die erwartete Rendite,
# laufende Kosten, Steuern, Entnahmen und sogar unvorhersehbare
# Marktschwankungen. Die Ergebnisse werden in übersichtlichen Grafiken
# und einem finalen PDF-Report zusammengefasst.
#
# Letzte Aktualisierung: 2025-08-17
# ==============================================================================

# === IMPORTS: Erforderliche Werkzeuge importieren ===
# Hier werden alle notwendigen "Werkzeuge" (sogenannte Bibliotheken)
# geladen, die das Programm benötigt, um seine Aufgaben zu erfüllen.
from collections import \
    deque  # Hilft, Investitionen in einer chronologischen Reihenfolge zu verwalten (wie eine Warteschlange).
from dateutil.relativedelta import relativedelta  # Erleichtert die genaue Berechnung von Zeiträumen (Monate, Jahre).
import datetime  # Dient zur Arbeit mit Kalenderdaten.
import pandas as pd  # Das Herzstück für die Datenanalyse; erstellt und bearbeitet Tabellen (DataFrames).
import matplotlib.pyplot as plt  # Ermöglicht das Zeichnen von Diagrammen und Grafiken.
import \
    numpy_financial as npf  # Eine Bibliothek für finanzmathematische Berechnungen, wie z. B. den Internen Zinsfuß (IRR).
import numpy as np  # Für komplexe mathematische Operationen und statistische Funktionen.
import dataclasses  # Ein Werkzeug, das es uns ermöglicht, Eingabeparameter übersichtlich zu strukturieren.
from typing import List, Dict, Any, \
    Optional  # Dient dazu, den Code lesbarer zu machen, indem wir die Art der Daten (z.B. Liste, Wörterbuch) definieren.
import os  # Hilft bei der Verwaltung von Dateien und Ordnern.
from fpdf import FPDF, XPos, YPos  # Dient zum Erstellen des finalen Reports im PDF-Format.


# === EINGANGSPARAMETER ALS DATENKLASSE ===
@dataclasses.dataclass
class SparplanParameter:
    """
    Diese Klasse dient als zentraler Ort, an dem alle Einstellungen
    für ein Sparplan-Szenario gespeichert werden. Sie ist wie ein Formular,
    in dem alle relevanten Informationen für die Simulation gesammelt werden.
    Jeder Parameter ist klar benannt und definiert, um die Lesbarkeit zu
    erhöhen.
    """
    label: str  # Ein Name für das Szenario (z.B. "Depot mit hohem Risiko").
    versicherung_modus: bool  # Bestimmt, ob die Simulation eine Versicherung oder ein Depot ist.
    eintrittsalter: int  # Das Alter des Anlegers zu Beginn der Simulation.
    initial_investment: float  # Die einmalige Anfangsinvestition.
    monthly_investment: float  # Der monatlich gesparte Betrag.
    laufzeit: int  # Die gesamte Laufzeit des Sparplans in Jahren.
    beitragszahldauer: int  # Die Dauer der Phase, in der monatlich eingezahlt wird.
    monthly_dynamik_rate: float  # Die jährliche prozentuale Steigerung der Sparrate.
    dynamik_turnus_monate: int  # Das Intervall für die Steigerung (z.B. 12 Monate für jährlich).
    sonderzahlung_jahr: int  # Das Jahr, in dem eine einmalige Sonderzahlung erfolgt.
    sonderzahlung_betrag: float  # Der Betrag der einmaligen Sonderzahlung.
    regel_sonderzahlung_betrag: float  # Der Betrag einer regelmäßig wiederkehrenden Sonderzahlung.
    regel_sonderzahlung_turnus_jahre: int  # Der Turnus (z.B. alle 5 Jahre) der regelmäßigen Sonderzahlung.
    annual_withdrawal: float  # Der jährliche Betrag, der in der Entnahmephase entnommen wird.
    annual_return: float  # Die erwartete durchschnittliche jährliche Rendite.
    ausgabeaufschlag: float  # Einmalige Gebühr beim Kauf von Fondsanteilen.
    ruecknahmeabschlag: float  # Gebühr beim Verkauf von Fondsanteilen.
    ter: float  # Die Gesamtkostenquote des Fonds (z.B. für Verwaltungsgebühren).
    serviceentgelt: float  # Eine zusätzliche jährliche Servicegebühr.
    stueckkosten: float  # Fixe Kosten pro Transaktion (oft bei Depots).
    abschlusskosten_einmalig_prozent: float  # Einmalige Abschlusskosten bei Versicherungen.
    abschlusskosten_monatlich_prozent: float  # Monatliche Abschlusskosten bei Versicherungen.
    verrechnungsdauer_monate: int  # Zeitraum, über den Abschlusskosten verrechnet werden.
    verwaltungskosten_monatlich_prozent: float  # Monatliche Verwaltungskosten bei Versicherungen.
    abgeltungssteuer_rate: float  # Steuersatz für Kapitalerträge.
    soli_zuschlag_on_abgeltungssteuer: float  # Solidaritätszuschlag auf die Abgeltungssteuer.
    kirchensteuer_on_abgeltungssteuer: float  # Kirchensteuer auf die Abgeltungssteuer.
    persoenlicher_steuersatz: float  # Persönlicher Steuersatz (relevant für die Halbeinkunftsregelung).
    freistellungsauftrag_jahr: float  # Betrag, bis zu dem Kapitalerträge steuerfrei sind.
    teilfreistellung: float  # Prozentsatz der Erträge, der bei bestimmten Fonds steuerfrei ist.
    basiszins: float  # Basiszins für die Berechnung der Vorabpauschale.
    rebalancing_rate: float  # Prozentsatz des Depots, der jährlich angepasst wird (Rebalancing).
    entnahme_modus: str  # Entnahme-Strategie ("jährlich" oder "monatlich").
    bewertungsdauer: int  # Relevant für die Besteuerung von Versicherungen.
    annual_std_dev: float = 0.15  # Die statistische Abweichung der Rendite; wichtig für die Monte-Carlo-Simulation.


class SparplanSimulator:
    """
    Diese Klasse ist der Kern des Programms. Sie führt die eigentliche Simulation
    durch und kümmert sich um alle monatlichen Berechnungen. Sie verwaltet den
    aktuellen Zustand des Depots (oder der Versicherung), loggt alle Kosten und
    speichert die Ein- und Auszahlungen.
    """

    def __init__(self, params: SparplanParameter):
        """Initialisiert die Simulation mit den übergebenen Parametern."""
        self.params = params  # Speichert die Einstellungen für die Simulation.
        self.portfolio = deque()  # Die "Warteschlange" unserer Investitionen, in der ältere Investitionen zuerst abgearbeitet werden (FIFO).
        self.rebalancing_log = []  # Eine Liste, die alle durchgeführten Rebalancing-Vorgänge aufzeichnet.
        self.monatliche_kosten_logs = []  # Eine Liste, die monatlich den Depotwert und alle Kosten festhält.
        self.cashflows = []  # Eine Liste, die alle Ein- und Auszahlungen für die IRR-Berechnung speichert.

        # Initialisiert alle Zähler, um die Gesamtsumme der Kosten und Steuern zu verfolgen.
        self.ausgabeaufschlag_summe = 0
        self.ruecknahmeabschlag_summe = 0
        self.stueckkosten_summe = 0
        self.abschlusskosten_summe = 0
        self.verwaltungskosten_summe = 0
        self.ter_summe = 0
        self.serviceentgelt_summe = 0
        self.kumulierte_entnahmen = 0
        self.total_tax_paid = 0
        self.freistellungs_topf = params.freistellungsauftrag_jahr  # Der Freistellungsauftrag für das aktuelle Jahr.
        self.monthly_investment = params.monthly_investment  # Der aktuelle monatliche Sparbetrag.
        self.abschlusskosten_monatlich_rest = [0.0] * (params.laufzeit * 12)
        self.abschlusskosten_einmalig_rest = [0.0] * (params.laufzeit * 12)

    def run_simulation(self) -> (pd.DataFrame, List[Dict[str, Any]], List[float]):
        """
        Diese Funktion startet die komplette Simulation.
        Sie ruft alle anderen Methoden monatlich auf, bis die gesamte Laufzeit
        vorbei ist. Am Ende gibt sie die gesammelten Daten zurück.
        """
        self._initialisiere_simulation()  # Startet mit den einmaligen Anfangseinstellungen.
        for month in range(self.params.laufzeit * 12):  # Eine Schleife, die jeden Monat einzeln durchspielt.
            self._simuliere_monat(month)
        self._finalisiere_simulation()  # Führt die finalen Berechnungen am Ende der Laufzeit durch.
        df_kosten = pd.DataFrame(self.monatliche_kosten_logs)  # Erstellt eine Tabelle aus den gesammelten Log-Daten.
        return df_kosten, self.rebalancing_log, self.cashflows

    def _initialisiere_simulation(self):
        """
        Führt einmalige Berechnungen und Einstellungen zu Beginn der Simulation durch.
        Dazu gehört die Umrechnung der jährlichen Rendite in eine monatliche
        und das Anlegen der ersten Investition.
        """
        # Umrechnung der jährlichen Rendite in eine monatliche Rate.
        self.params.monthly_return = (1 + self.params.annual_return) ** (1 / 12) - 1
        # Berechnung des gesamten Steuersatzes, inklusive Soli und Kirchensteuer.
        self.params.full_tax_rate = self.params.abgeltungssteuer_rate * (
                1 + self.params.soli_zuschlag_on_abgeltungssteuer + self.params.kirchensteuer_on_abgeltungssteuer)

        # Kosten werden je nach Sparplan-Typ (Depot vs. Versicherung) auf 0 gesetzt.
        if self.params.versicherung_modus:
            self.params.ausgabeaufschlag = 0.0
            self.params.ruecknahmeabschlag = 0.0
            self.params.stueckkosten = 0.0
        else:
            self.params.abschlusskosten_einmalig_prozent = 0.0
            self.params.abschlusskosten_monatlich_prozent = 0.0
            self.params.verwaltungskosten_monatlich_prozent = 0.0

        # Verarbeitet die erste, einmalige Anfangsinvestition.
        aufschlag = self.params.initial_investment * self.params.ausgabeaufschlag
        nettobetrag = self.params.initial_investment - aufschlag
        self.ausgabeaufschlag_summe += aufschlag
        self.cashflows.append(-self.params.initial_investment)  # Die Einzahlung wird als negativer Cashflow erfasst.

        if nettobetrag > 0:
            # Die erste Investition wird zum Portfolio hinzugefügt.
            self.portfolio.append({
                "date": datetime.date(2025, 1, 1),
                "amount_invested": nettobetrag,
                "units": nettobetrag,
                "value": nettobetrag,
                "start_of_prev_year_value": nettobetrag,
                "vorabpauschalen_bereits_versteuert": 0.0
            })

    def _simuliere_monat(self, month: int):
        """
        Diese Funktion simuliert einen einzelnen Monat.
        Sie führt die monatlichen Aktionen in der korrekten Reihenfolge aus:
        Einzahlung -> Kosten -> Steuern -> Rebalancing -> Wertentwicklung -> Entnahmen.
        """
        current_date = datetime.date(2025, 1, 1) + relativedelta(months=month)
        is_january = current_date.month == 1

        if is_january:
            # Setzt den Freistellungsauftrag zu Beginn jedes Jahres zurück.
            self.freistellungs_topf = self.params.freistellungsauftrag_jahr

        self._handle_monthly_investment(month, current_date)  # Verarbeitet monatliche Sparraten.
        self._handle_costs(month, current_date)  # Berechnet und zieht die Kosten ab.
        self._handle_taxes(current_date)  # Berechnet die Steuern (Vorabpauschale).
        self._handle_rebalancing(current_date)  # Führt ein Rebalancing durch.

        # Die Wertentwicklung des Portfolios basierend auf der monatlichen Rendite.
        for entry in self.portfolio:
            entry["value"] *= (1 + self.params.monthly_return)

        self._handle_withdrawals(month, current_date)  # Verarbeitet Entnahmen in der Entnahmephase.

        # Der aktuelle Stand des Depots und die Kosten werden für diesen Monat protokolliert.
        depotwert = sum(e["value"] for e in self.portfolio)
        self.monatliche_kosten_logs.append({
            "Datum": current_date, "Depotwert": depotwert, "Ausgabeaufschlag kum": self.ausgabeaufschlag_summe,
            "Rücknahmeabschlag kum": self.ruecknahmeabschlag_summe, "Stückkosten kum": self.stueckkosten_summe,
            "Gesamtfondkosten kum": self.ter_summe, "Serviceentgelt kum": self.serviceentgelt_summe,
            "Abschlusskosten kum": self.abschlusskosten_summe, "Verwaltungskosten kum": self.verwaltungskosten_summe,
            "Steuern kumuliert": self.total_tax_paid, "Kumulierte Entnahmen": self.kumulierte_entnahmen
        })

        if current_date.month == 12:
            # Speichert den Wert des Depots am Jahresende für die Vorabpauschale des nächsten Jahres.
            for entry in self.portfolio:
                entry["start_of_prev_year_value"] = entry["value"]

    def _handle_monthly_investment(self, month, current_date):
        """Verarbeitet alle Arten von Einzahlungen."""
        # Anpassung der monatlichen Rate basierend auf der Dynamik.
        if month > 0 and month % self.params.dynamik_turnus_monate == 0:
            self.monthly_investment *= (1 + self.params.monthly_dynamik_rate)

        is_einmalig = month == self.params.sonderzahlung_jahr * 12
        is_regelmaessig = (self.params.regel_sonderzahlung_turnus_jahre > 0 and month > 0 and month % (
                self.params.regel_sonderzahlung_turnus_jahre * 12) == 0)

        # Verarbeitung von Sonderzahlungen, falls fällig.
        if is_einmalig or is_regelmaessig:
            betrag = (self.params.sonderzahlung_betrag if is_einmalig else self.params.regel_sonderzahlung_betrag)
            if betrag > 0:
                self.cashflows.append(-betrag)  # Sonderzahlung wird als negativer Cashflow erfasst.
                if not self.params.versicherung_modus:
                    aufschlag = betrag * self.params.ausgabeaufschlag
                    netto = betrag - aufschlag
                    self.ausgabeaufschlag_summe += aufschlag
                else:
                    netto = betrag
                self.portfolio.append(
                    {"date": current_date, "amount_invested": netto, "value": netto, "start_of_prev_year_value": netto,
                     "vorabpauschalen_bereits_versteuert": 0.0})

        # Verarbeitung der monatlichen Einzahlung, solange die Beitragszahldauer noch läuft.
        if month < self.params.beitragszahldauer * 12:
            aufschlag = self.monthly_investment * self.params.ausgabeaufschlag
            netto = self.monthly_investment - aufschlag
            self.ausgabeaufschlag_summe += aufschlag
            self.cashflows.append(
                -self.monthly_investment)  # Monatliche Einzahlung wird als negativer Cashflow erfasst.
            self.portfolio.append(
                {"date": current_date, "amount_invested": netto, "value": netto, "start_of_prev_year_value": netto,
                 "vorabpauschalen_bereits_versteuert": 0.0})

    def _handle_costs(self, month, current_date):
        """Berechnet und zieht die monatlichen und jährlichen Kosten ab."""
        depotwert = sum(e["value"] for e in self.portfolio) if self.portfolio else 0
        # Kosten, die nur bei einem Versicherungs-Sparplan anfallen.
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

        # Kosten, die jährlich anfallen, wie die Gesamtkostenquote (TER) und Servicegebühren.
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
        """Berechnet und zieht die jährliche Vorabpauschale ab (nur bei Depots)."""
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
        """
        Führt ein jährliches Rebalancing durch, um die gewünschte Verteilung im Depot zu halten.
        Dabei werden Anteile verkauft und der Erlös wieder investiert.
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
                    entry = self.portfolio.popleft()  # Die ältesten Positionen werden zuerst verkauft (FIFO-Prinzip).
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
        """Verarbeitet Entnahmen in der Entnahmephase."""
        # Überprüft, ob die Entnahmephase begonnen hat.
        if month >= self.params.beitragszahldauer * 12:
            depotwert = sum(e["value"] for e in self.portfolio)
            entnahme_betrag = 0
            # Bestimmt, ob die Entnahme jährlich oder monatlich erfolgt.
            if self.params.entnahme_modus == "jährlich" and current_date.month == 1:
                entnahme_betrag = min(self.params.annual_withdrawal, depotwert)
            elif self.params.entnahme_modus == "monatlich":
                entnahme_betrag = min(self.params.annual_withdrawal / 12, depotwert)

            if entnahme_betrag >= 0:
                self.cashflows.append(entnahme_betrag)  # Die Entnahme wird als positiver Cashflow erfasst.

                remaining_entnahme = entnahme_betrag

                # Die Entnahme wird aus den ältesten Portfolio-Positionen genommen, um die Buchführung zu vereinfachen.
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
        """
        Führt die letzten Berechnungen am Ende der Laufzeit durch,
        insbesondere die Besteuerung des finalen Restwerts.
        """
        restwert = sum(e["value"] for e in self.portfolio)
        investiert = sum(e["amount_invested"] for e in self.portfolio)
        end_datum = datetime.date(2025, 1, 1) + relativedelta(months=self.params.laufzeit * 12)

        if restwert > 1e-9:
            gewinn = max(0.0, restwert - investiert)
            steuer = 0
            if self.params.versicherung_modus:
                aktuelle_laufzeit = self.params.laufzeit
                aktuelle_alter = self.params.eintrittsalter + aktuelle_laufzeit
                # Besteuerung des Gewinns je nach Laufzeit und Alter (Halbeinkunftsregelung).
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
            self.cashflows.append(restwert_net)  # Der Netto-Verkauf am Ende wird als letzter Cashflow erfasst.
            self.kumulierte_entnahmen += restwert_net

        # Führt den letzten Eintrag in das monatliche Log ein, der das Ende der Simulation darstellt.
        self.monatliche_kosten_logs.append({
            "Datum": end_datum, "Depotwert": 0, "Ausgabeaufschlag kum": self.ausgabeaufschlag_summe,
            "Rücknahmeabschlag kum": self.ruecknahmeabschlag_summe, "Stückkosten kum": self.stueckkosten_summe,
            "Gesamtfondkosten kum": self.ter_summe, "Serviceentgelt kum": self.serviceentgelt_summe,
            "Abschlusskosten kum": self.abschlusskosten_summe, "Verwaltungskosten kum": self.verwaltungskosten_summe,
            "Steuern kumuliert": self.total_tax_paid, "Kumulierte Entnahmen": self.kumulierte_entnahmen
        })


# === HILFSFUNKTIONEN: Werkzeuge außerhalb der Hauptsimulation ===
# Diese Funktionen führen Aufgaben aus, die nicht direkt zur monatlichen
# Simulation gehören, wie z. B. die Auswertung der Ergebnisse, das Erstellen
# von Grafiken und die Generierung des finalen Berichts.
def auswerten_kosten(df_kosten: pd.DataFrame, params: SparplanParameter, label: str,
                     mc_results: Optional[List[float]] = None) -> pd.DataFrame:
    """
    Diese Funktion nimmt die monatlichen Kosten und fasst sie in einer
    übersichtlichen jährlichen Tabelle zusammen. Sie kategorisiert die
    Kosten und fügt, falls vorhanden, die Ergebnisse der Monte-Carlo-Simulation hinzu.
    """
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
    """Erstellt ein einziges Diagramm, das die Depotentwicklung mehrerer Szenarien miteinander vergleicht."""
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
    """Erstellt ein gestapeltes Flächendiagramm, das die kumulierten Kosten pro Jahr visualisiert."""
    df_kosten["Jahr"] = pd.to_datetime(df_kosten["Datum"]).dt.year
    df_kum_kosten = df_kosten.groupby("Jahr").last().reset_index()

    kosten_spalten = []
    if params.versicherung_modus:
        kosten_spalten = ["Abschlusskosten kum", "Verwaltungskosten kum", "Gesamtfondkosten kum", "Steuern kumuliert"]
    else:
        kosten_spalten = ["Ausgabeaufschlag kum", "Rücknahmeabschlag kum", "Stückkosten kum", "Gesamtfondkosten kum",
                          "Steuern kumuliert"]

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
    """Erstellt ein Diagramm, das die Entwicklung der kumulierten Entnahmen zeigt."""
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
    """
    Berechnet den Internen Zinsfuß (IRR). Der IRR ist die Rendite, die den
    Wert aller Einzahlungen und Entnahmen auf Null setzt. Er gibt eine
    genaue Vorstellung davon, wie profitabel der Gesamtplan ist.
    """
    try:
        irr_monthly = npf.irr(cashflows)
        irr_annual = (1 + irr_monthly) ** 12 - 1
        return irr_annual
    except (ValueError, IndexError) as e:
        print(f"IRR für {label} konnte nicht berechnet werden. Grund: {e}")
        return None


def exportiere_rebalancing_daten(rebalancing_log, label):
    """Exportiert das Rebalancing-Log in eine CSV-Datei."""
    if rebalancing_log:
        df_rebal = pd.DataFrame(rebalancing_log)
        df_rebal.to_csv(f"{label}_Rebalancing.csv", index=False)
        return df_rebal
    return None


def run_monte_carlo(params, num_runs):
    """
    Diese Funktion führt eine Monte-Carlo-Simulation durch. Sie simuliert
    den Sparplan mehrfach (z.B. 1000-mal) mit zufälligen, aber realistischen
    Renditen. Dies gibt eine Bandbreite möglicher Ergebnisse, die das
    Risiko und die Unsicherheit der Kapitalmärkte widerspiegelt.
    """
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

    # Erstellt ein Histogramm, das die Verteilung der Ergebnisse darstellt.
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
    """
    Diese Funktion erstellt einen finalen Report im Markdown-Format,
    der die wichtigsten Ergebnisse und Links zu den Grafiken enthält.
    """
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


# === HAUPTPROGRAMM: Skript-Ausführung ===
# Dieser Code-Block wird ausgeführt, wenn das Skript gestartet wird.
# Er definiert die Szenarien und ruft die Simulationsfunktionen auf.
if __name__ == "__main__":
    # --- Definition der Sparplan-Szenarien ---

    # Szenario 1: Klassisches Depot
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

    # Szenario 2: Versicherungsbasierter Sparplan
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
        ausgabeaufschlag=0.0,  # Nicht relevant im Versicherungsmodus
        ruecknahmeabschlag=0.0,  # Nicht relevant im Versicherungsmodus
        ter=0.0045,
        serviceentgelt=0.0018,
        stueckkosten=0.0,  # Nicht relevant im Versicherungsmodus
        abschlusskosten_einmalig_prozent=0.025,
        abschlusskosten_monatlich_prozent=0.0252,
        verrechnungsdauer_monate=60,
        verwaltungskosten_monatlich_prozent=0.09,
        abgeltungssteuer_rate=0.25,
        soli_zuschlag_on_abgeltungssteuer=0.055,
        kirchensteuer_on_abgeltungssteuer=0.09,
        persoenlicher_steuersatz=0.3,
        freistellungsauftrag_jahr=0,
        teilfreistellung=0.0,  # Nicht relevant im Versicherungsmodus
        basiszins=0.0,  # Nicht relevant im Versicherungsmodus
        rebalancing_rate=0.0,  # Rebalancing ist oft im Versicherungsmodus integriert und nicht als separate Rate
        entnahme_modus="jährlich",
        bewertungsdauer=35,
        annual_std_dev=0.15
    )

    # Szenario 3: Depot mit hohen Kosten, oft als "DIY" bezeichnet
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
        ausgabeaufschlag=0.03,  # Hoher Ausgabeaufschlag
        ruecknahmeabschlag=0.03,  # Hoher Rücknahmeabschlag
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

    # Liste der zu simulierenden Szenarien
    params_list = [params_depot, params_versicherung, params_diy]
    df_list = []

    # --- Hauptsimulationsschleife ---
    # Diese Schleife durchläuft jedes der oben definierten Szenarien
    # und führt die vollständige Analyse durch.
    for params in params_list:
        print(f"\n--- Simulation für {params.label} wird gestartet ---")

        # 1. Simulierter Lauf für deterministische Ergebnisse (ohne Zufallsfaktor).
        simulator = SparplanSimulator(params)
        df_kosten, rebalancing_log, cashflows = simulator.run_simulation()
        df_list.append(df_kosten)

        # 2. Auswertung und Plotten der Grafiken.
        irr_annual = berechne_irr_und_print(cashflows, params.label)
        df_rebal = exportiere_rebalancing_daten(rebalancing_log, params.label)
        plotten_kosten(df_kosten, params)
        plotten_entnahmen(df_kosten, params)

        # 3. Durchführung der Monte-Carlo-Simulation, um die Bandbreite der Ergebnisse zu zeigen.
        mc_results_tuple = run_monte_carlo(params, num_runs=100)

        # 4. Erstellung des finalen PDF-Reports mit allen Ergebnissen.
        erzeuge_report(df_kosten, df_rebal, irr_annual, mc_results_tuple, params)

    # 5. Erstellung des Vergleichsdiagramms, das alle Szenarien nebeneinander zeigt.
    plotten_vergleich(df_list, params_list)
    print("\nAlle Simulationen und Reports wurden erfolgreich erstellt.")