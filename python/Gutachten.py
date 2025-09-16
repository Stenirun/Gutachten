# SPARPPLAN- UND MONTE-CARLO-SIMULATOR
# ==============================================================================

# === IMPORTS ===
from collections import deque
from dateutil.relativedelta import relativedelta
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import dataclasses
from typing import List, Dict, Any, Optional
import pyxirr
import os
import warnings

# Unterdrückt RuntimeWarnings und FutureWarnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Import der Funktionen aus der Monte-Carlo-Datei
from monte_carlo_simulator import (
    load_and_analyze_data,
    get_worst_3_years,
    get_worst_3_years_from_simulations,
    run_monte_carlo_simulation,
    analyze_and_plot_results
)

# === EINGANGSPARAMETER ALS DATENKLASSE ===
@dataclasses.dataclass
class BasisParameter:
    eintrittsalter: int
    initial_investment: float
    monthly_investment: float
    laufzeit: int
    beitragszahldauer: int
    monthly_dynamik_rate: float
    dynamik_turnus_monate: int
    sonderzahlung_jahr: float
    sonderzahlung_betrag: float
    regel_sonderzahlung_betrag: float
    regel_sonderzahlung_turnus_jahre: int
    annual_withdrawal: float
    entnahme_plan: Optional[Dict[int, float]]
    entnahme_modus: str
    abgeltungssteuer_rate: float
    soli_zuschlag_on_abgeltungssteuer: float
    kirchensteuer_on_abgeltungssteuer: float
    persoenlicher_steuersatz: float
    freistellungsauftrag_jahr: float
    inflation_rate: float
    inflation_volatility: float
    freistellungs_pauschbetrag_anpassung_rate: Optional[float] = 0.02
    start_date: Optional[datetime.date] = datetime.date.today().replace(day=1)
    death_year: Optional[int] = None


@dataclasses.dataclass
class DepotParameter(BasisParameter):
    ausgabeaufschlag: float = 0.0
    monthly_ausgabeaufschlag: float = 0.0
    ruecknahmeabschlag: float = 0.0
    ter: float = 0.0
    serviceentgelt: float = 0.0
    stueckkosten: float = 0.0
    teilfreistellung: float = 0.3
    basiszins: float = 0.0255
    rebalancing_rate: float = 0.0
    label: str = "Depot"
    versicherung_modus: bool = False


@dataclasses.dataclass
class DepotDIYParameter(BasisParameter):
    ausgabeaufschlag: float = 0.0
    monthly_ausgabeaufschlag: float = 0.0
    ruecknahmeabschlag: float = 0.0
    ter: float = 0.0
    serviceentgelt: float = 0.0
    stueckkosten: float = 0.0
    teilfreistellung: float = 0.3
    basiszins: float = 0.0255
    rebalancing_rate: float = 0.0
    label: str = "Depot DIY"
    versicherung_modus: bool = False


@dataclasses.dataclass
class VersicherungParameter(BasisParameter):
    ter: float = 0.0
    serviceentgelt: float = 0.0
    guthabenkosten: float = 0.0
    abschlusskosten_einmalig_prozent: float = 0.0
    abschlusskosten_monatlich_prozent: float = 0.0
    verrechnungsdauer_monate: int = 0
    verwaltungskosten_monatlich_prozent: float = 0.0
    bewertungsdauer: int = 0
    label: str = "Versicherung"
    versicherung_modus: bool = True


# === SIMULATORKLASSE ===
class SparplanSimulator:
    def __init__(self, params: Any, annual_return: float):
        self.params = params
        self.annual_return = annual_return
        self.portfolio = deque()
        self.rebalancing_log = []
        self.monatliche_kosten_logs = []
        self.cashflows = []
        self.cashflow_dates = []
        self.real_cashflows = []
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
        self.freistellungs_topf = self.params.freistellungsauftrag_jahr
        self.monthly_investment = self.params.monthly_investment
        self.abschlusskosten_rest = 0.0
        self.kumulierte_inflation_factor = 1.0
        self.monthly_inflation_rates = np.random.normal(
            loc=self.params.inflation_rate / 12,
            scale=self.params.inflation_volatility / np.sqrt(12),
            size=self.params.laufzeit * 12
        )
        self.monthly_return = (1 + self.annual_return) ** (1 / 12) - 1
        self.full_tax_rate = self.params.abgeltungssteuer_rate * (
                1 + self.params.soli_zuschlag_on_abgeltungssteuer + self.params.kirchensteuer_on_abgeltungssteuer)
        self.death_triggered = False
        self.verrechnungs_monate_verbleibend = 0
        self.monatliche_abschlusskosten_fix = 0
        self.death_abschlusskosten_pro_monat = 0
        self.death_abschlusskosten_remaining_months = 0

    def run_simulation(self) -> (pd.DataFrame, List[Dict[str, Any]], List[float], List[datetime.date], List[float]):
        self._initialisiere_simulation()
        for month in range(self.params.laufzeit * 12):
            self._simuliere_monat(month)
        self._finalisiere_simulation()
        df_kosten = pd.DataFrame(self.monatliche_kosten_logs)
        return df_kosten, self.rebalancing_log, self.cashflows, self.cashflow_dates, self.real_cashflows

    def _initialisiere_simulation(self):
        if self.params.versicherung_modus:
            abschlusskosten_einmalig = self.params.initial_investment * getattr(self.params,
                                                                                "abschlusskosten_einmalig_prozent", 0.0)
            abschlusskosten_monatlich_total = (
                                                      self.params.monthly_investment * self.params.beitragszahldauer * 12) * getattr(
                self.params, "abschlusskosten_monatlich_prozent", 0.0)
            self.abschlusskosten_rest = abschlusskosten_einmalig + abschlusskosten_monatlich_total
            if self.params.verrechnungsdauer_monate > 0:
                self.monatliche_abschlusskosten_fix = self.abschlusskosten_rest / self.params.verrechnungsdauer_monate
                self.verrechnungs_monate_verbleibend = self.params.verrechnungsdauer_monate

        ausgabeaufschlag = getattr(self.params, "ausgabeaufschlag", 0.0)
        aufschlag = self.params.initial_investment * ausgabeaufschlag
        nettobetrag = self.params.initial_investment - aufschlag
        self.ausgabeaufschlag_summe += aufschlag
        self.ausgabeaufschlag_real_summe += aufschlag / self.kumulierte_inflation_factor
        self.cashflows.append(-self.params.initial_investment)
        self.real_cashflows.append(-self.params.initial_investment)
        self.cashflow_dates.append(datetime.date(2025, 1, 1))

        if nettobetrag > 0:
            self.portfolio.append({
                "date": datetime.date(2025, 1, 1),
                "amount_invested": nettobetrag,
                "value": nettobetrag,
                "start_of_prev_year_value": nettobetrag,
                "vorabpauschalen_bereits_versteuert": 0.0
            })

    def _simuliere_monat(self, month: int):
        current_date = datetime.date(2025, 1, 1) + relativedelta(months=month)
        current_year = current_date.year - 2025

        if self.params.death_year and current_year == self.params.death_year and not self.death_triggered:
            self._handle_death(current_date)
            self.death_triggered = True

        is_january = current_date.month == 1
        if is_january:
            self.freistellungs_topf = self.params.freistellungsauftrag_jahr * (
                    1 + self.params.freistellungs_pauschbetrag_anpassung_rate) ** (
                                              current_date.year - 2025)

        self._handle_monthly_investment(month, current_date)

        depotwert_brutto = sum(e["value"] for e in self.portfolio)
        self._monatliche_kosten_abziehen(current_date, depotwert_brutto)

        for entry in self.portfolio:
            entry["value"] *= (1 + self.monthly_return)

        self.kumulierte_inflation_factor *= (1 + self.monthly_inflation_rates[month])

        self._handle_taxes(current_date)
        self._handle_rebalancing(current_date)
        self._handle_withdrawals(month, current_date)

        depotwert = sum(e["value"] for e in self.portfolio)
        depotwert_real = depotwert / self.kumulierte_inflation_factor

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
            for entry in self.portfolio:
                entry["start_of_prev_year_value"] = entry["value"]

    def _handle_death(self, current_date):
        if not self.params.versicherung_modus or self.death_triggered:
            return
        self.death_triggered = True
        depotwert_brutto = sum(e["value"] for e in self.portfolio)
        print(f"Todesfall simuliert in Jahr {self.params.death_year}. Depotwert (Brutto): {depotwert_brutto:,.2f} €")
        ruecknahmeabschlag = getattr(self.params, "ruecknahmeabschlag", 0.0)
        ruecknahmeabschlag_val = depotwert_brutto * ruecknahmeabschlag
        total_netto_entnahme = depotwert_brutto - ruecknahmeabschlag_val
        self.portfolio.clear()
        if total_netto_entnahme > 0:
            self.portfolio.append({
                "date": current_date,
                "amount_invested": total_netto_entnahme,
                "value": total_netto_entnahme,
                "start_of_prev_year_value": total_netto_entnahme,
                "vorabpauschalen_bereits_versteuert": 0.0
            })
        print(f"Kapital nach Auszahlung und Re-Investment: {total_netto_entnahme:,.2f} €")

    def _handle_monthly_investment(self, month, current_date):
        if month > 0 and month % self.params.dynamik_turnus_monate == 0:
            self.monthly_investment *= (1 + self.params.monthly_dynamik_rate)
        is_einmalig = month == self.params.sonderzahlung_jahr * 12
        is_regelmaessig = (self.params.regel_sonderzahlung_turnus_jahre > 0 and month > 0 and month % (
                self.params.regel_sonderzahlung_turnus_jahre * 12) == 0)
        if is_einmalig or is_regelmaessig:
            betrag = (self.params.sonderzahlung_betrag if is_einmalig else self.params.regel_sonderzahlung_betrag)
            if betrag > 0:
                self.cashflows.append(-betrag)
                self.real_cashflows.append(-betrag / self.kumulierte_inflation_factor)
                self.cashflow_dates.append(current_date)
                ausgabeaufschlag = getattr(self.params, "ausgabeaufschlag", 0.0)
                aufschlag = betrag * ausgabeaufschlag
                netto = betrag - aufschlag
                self.ausgabeaufschlag_summe += aufschlag
                self.ausgabeaufschlag_real_summe += aufschlag / self.kumulierte_inflation_factor
                self.portfolio.append(
                    {"date": current_date, "amount_invested": netto, "value": netto, "start_of_prev_year_value": netto,
                     "vorabpauschalen_bereits_versteuert": 0.0})

        if month < self.params.beitragszahldauer * 12:
            monthly_ausgabeaufschlag = getattr(self.params, "monthly_ausgabeaufschlag", 0.0)
            aufschlag = self.monthly_investment * monthly_ausgabeaufschlag
            netto = self.monthly_investment - aufschlag
            self.ausgabeaufschlag_summe += aufschlag
            self.ausgabeaufschlag_real_summe += aufschlag / self.kumulierte_inflation_factor
            self.cashflows.append(-self.monthly_investment)
            self.real_cashflows.append(-self.monthly_investment / self.kumulierte_inflation_factor)
            self.cashflow_dates.append(current_date)
            self.portfolio.append(
                {"date": current_date, "amount_invested": netto, "value": netto, "start_of_prev_year_value": netto,
                 "vorabpauschalen_bereits_versteuert": 0.0})

    def _monatliche_kosten_abziehen(self, current_date, depotwert_brutto):
        ter_kosten = depotwert_brutto * self.params.ter / 12
        self.ter_summe += ter_kosten
        self.ter_real_summe += ter_kosten / self.kumulierte_inflation_factor
        if self.params.versicherung_modus:
            abschlusskosten_monatlich = 0
            if self.verrechnungs_monate_verbleibend > 0:
                abschlusskosten_monatlich = self.monatliche_abschlusskosten_fix
                self.verrechnungs_monate_verbleibend -= 1
            if getattr(self, "death_abschlusskosten_remaining_months", 0) > 0:
                abschlusskosten_monatlich += self.death_abschlusskosten_pro_monat
                self.death_abschlusskosten_remaining_months -= 1
            verwaltungskosten_monatlich = self.monthly_investment * self.params.verwaltungskosten_monatlich_prozent
            guthabenkosten_monatlich = depotwert_brutto * self.params.guthabenkosten / 12
            serviceentgelt_monatlich = depotwert_brutto * self.params.serviceentgelt / 12
            self.abschlusskosten_summe += abschlusskosten_monatlich
            self.verwaltungskosten_summe += verwaltungskosten_monatlich
            self.guthabenkosten_summe += guthabenkosten_monatlich
            self.serviceentgelt_summe += serviceentgelt_monatlich
            self.abschlusskosten_real_summe += abschlusskosten_monatlich / self.kumulierte_inflation_factor
            self.verwaltungskosten_real_summe += verwaltungskosten_monatlich / self.kumulierte_inflation_factor
            self.guthabenkosten_real_summe += guthabenkosten_monatlich / self.kumulierte_inflation_factor
            self.serviceentgelt_real_summe += serviceentgelt_monatlich / self.kumulierte_inflation_factor
            gesamtkosten_monatlich = (
                    ter_kosten + abschlusskosten_monatlich + verwaltungskosten_monatlich + guthabenkosten_monatlich + serviceentgelt_monatlich
            )
        else:
            ausgabeaufschlag_monatlich = self.params.monthly_investment * getattr(self.params, "monthly_ausgabeaufschlag", 0.0)
            stueckkosten_monatlich = getattr(self.params, "stueckkosten", 0.0) / 12
            serviceentgelt_monatlich = depotwert_brutto * self.params.serviceentgelt / 12
            self.ausgabeaufschlag_summe += ausgabeaufschlag_monatlich
            self.stueckkosten_summe += stueckkosten_monatlich
            self.serviceentgelt_summe += serviceentgelt_monatlich
            self.ausgabeaufschlag_real_summe += ausgabeaufschlag_monatlich / self.kumulierte_inflation_factor
            self.stueckkosten_real_summe += stueckkosten_monatlich / self.kumulierte_inflation_factor
            self.serviceentgelt_real_summe += serviceentgelt_monatlich / self.kumulierte_inflation_factor
            gesamtkosten_monatlich = (
                    ter_kosten + ausgabeaufschlag_monatlich + stueckkosten_monatlich + serviceentgelt_monatlich
            )
        if depotwert_brutto > 1e-9:
            anteil_kosten = gesamtkosten_monatlich / depotwert_brutto
            for entry in self.portfolio:
                entry["value"] -= entry["value"] * anteil_kosten
        else:
            gesamtkosten_monatlich = 0.0
        return depotwert_brutto - gesamtkosten_monatlich

    def _finalisiere_simulation(self):
        depotwert_final = sum(e["value"] for e in self.portfolio)
        depotwert_final_real = depotwert_final / self.kumulierte_inflation_factor
        restwert = depotwert_final
        investiert = sum(e["amount_invested"] for e in self.portfolio)
        gewinn = max(0.0, restwert - investiert)
        steuer = 0
        ruecknahmeabschlag_val = 0.0
        if restwert > 1e-9 and gewinn > 0 and not self.death_triggered:
            if self.params.versicherung_modus:
                aktuelle_laufzeit = self.params.laufzeit
                aktuelle_alter = self.params.eintrittsalter + aktuelle_laufzeit
                if aktuelle_alter >= 62 and aktuelle_laufzeit >= 12:
                    steuer = gewinn * 0.5 * self.params.persoenlicher_steuersatz
                else:
                    steuer = gewinn * 0.85 * self.params.persoenlicher_steuersatz
            else:
                teilfreistellung = getattr(self.params, "teilfreistellung", 0.0)
                steuerbar = gewinn * (1 - teilfreistellung)
                bereits_versteuert = sum(e.get("vorabpauschalen_bereits_versteuert", 0.0) for e in self.portfolio)
                steuerbar = max(0.0, steuerbar - bereits_versteuert)
                steuerfreibetrag_used = min(self.freistellungs_topf, steuerbar)
                self.freistellungs_topf -= steuerfreibetrag_used
                zu_versteuern = max(0, steuerbar - steuerfreibetrag_used)
                # Korrigierte Zeile: Verwendet self.full_tax_rate anstelle von self.params.full_tax_rate
                steuer = zu_versteuern * self.full_tax_rate
            self.total_tax_paid += steuer
            self.total_tax_paid_real += steuer / self.kumulierte_inflation_factor
            self.total_withdrawal_tax_paid += steuer
            self.total_withdrawal_tax_paid_real += steuer / self.kumulierte_inflation_factor
        if not self.params.versicherung_modus:
            ruecknahmeabschlag = getattr(self.params, "ruecknahmeabschlag", 0.0)
            ruecknahmeabschlag_val = restwert * ruecknahmeabschlag
            self.ruecknahmeabschlag_summe += ruecknahmeabschlag_val
            self.ruecknahmeabschlag_real_summe += ruecknahmeabschlag_val / self.kumulierte_inflation_factor
        restwert_net = restwert - steuer - ruecknahmeabschlag_val
        self.cashflows.append(restwert_net)
        self.real_cashflows.append(restwert_net / self.kumulierte_inflation_factor)
        self.cashflow_dates.append(datetime.date(2025, 1, 1) + relativedelta(months=self.params.laufzeit * 12))
        self.kumulierte_entnahmen += restwert_net
        self.kumulierte_entnahmen_real += restwert_net / self.kumulierte_inflation_factor
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

    def _handle_taxes(self, current_date):
        is_january = current_date.month == 1
        teilfreistellung = getattr(self.params, "teilfreistellung", 0.0)
        basiszins = getattr(self.params, "basiszins", 0.0)
        if not self.params.versicherung_modus and is_january:
            for entry in self.portfolio:
                start_value = entry.get("start_of_prev_year_value", 0.0)
                fiktiver_ertrag = start_value * basiszins
                real_ertrag = entry["value"] - start_value
                steuerbarer_ertrag = min(fiktiver_ertrag, real_ertrag)
                zu_versteuern_temp = steuerbarer_ertrag * (1 - teilfreistellung)
                steuerfreibetrag_used = min(self.freistellungs_topf, max(0, zu_versteuern_temp))
                self.freistellungs_topf -= steuerfreibetrag_used
                zu_versteuern = max(0, zu_versteuern_temp - steuerfreibetrag_used)
                steuer = zu_versteuern * self.full_tax_rate
                if steuer > 0:
                    entry["value"] -= steuer
                    self.total_tax_paid += steuer
                    self.total_tax_paid_real += steuer / self.kumulierte_inflation_factor
                    entry["vorabpauschalen_bereits_versteuert"] += zu_versteuern

    def _handle_rebalancing(self, current_date):
        rebalancing_rate = getattr(self.params, "rebalancing_rate", 0.0)
        ruecknahmeabschlag = getattr(self.params, "ruecknahmeabschlag", 0.0)
        teilfreistellung = getattr(self.params, "teilfreistellung", 0.0)
        if not self.params.versicherung_modus and current_date.month == 12 and rebalancing_rate > 0:
            depotwert = sum(e["value"] for e in self.portfolio)
            umzuschichten = depotwert * rebalancing_rate
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
                    steuerbarer_gewinn = gain * (1 - teilfreistellung)
                    vorab_used = min(entry.get("vorabpauschalen_bereits_versteuert", 0.0) * prop, steuerbarer_gewinn)
                    steuerbarer_gewinn_nach_vp = max(0.0, steuerbarer_gewinn - vorab_used)
                    steuerfreibetrag = min(self.freistellungs_topf, steuerbarer_gewinn_nach_vp)
                    self.freistellungs_topf -= steuerfreibetrag
                    zu_versteuern = max(0.0, steuerbarer_gewinn_nach_vp - steuerfreibetrag)
                    steuer = zu_versteuern * self.full_tax_rate
                    ruecknahmeabschlag_val = sell_value * ruecknahmeabschlag
                    netto_reinvest = sell_value - steuer - ruecknahmeabschlag_val
                    self.total_tax_paid += steuer
                    self.total_tax_paid_real += steuer / self.kumulierte_inflation_factor
                    self.ruecknahmeabschlag_summe += ruecknahmeabschlag_val
                    self.ruecknahmeabschlag_real_summe += ruecknahmeabschlag_val / self.kumulierte_inflation_factor
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
        if month < self.params.beitragszahldauer * 12:
            return
        depotwert = sum(e["value"] for e in self.portfolio)
        entnahmebetrag_jahr = 0
        withdrawal_year = (current_date.year - datetime.date(2025, 1, 1).year) - self.params.beitragszahldauer + 1
        if self.params.entnahme_plan:
            sorted_years = sorted(self.params.entnahme_plan.keys(), reverse=True)
            for plan_year in sorted_years:
                if withdrawal_year >= plan_year:
                    entnahmebetrag_jahr = self.params.entnahme_plan[plan_year]
                    break
        elif self.params.annual_withdrawal:
            entnahmebetrag_jahr = self.params.annual_withdrawal
        if entnahmebetrag_jahr <= 0: return
        entnahmebetrag = 0
        if self.params.entnahme_modus == "jährlich" and current_date.month == 1:
            entnahmebetrag = entnahmebetrag_jahr
        elif self.params.entnahme_modus == "monatlich":
            entnahmebetrag = entnahmebetrag_jahr / 12
        entnahmebetrag_effektiv = min(entnahmebetrag, depotwert)
        if entnahmebetrag_effektiv <= 0:
            return
        remaining_to_withdraw = entnahmebetrag_effektiv
        netto_entnahme_summe = 0
        total_withdrawal_tax_this_year = 0
        temp_queue = deque()
        while remaining_to_withdraw > 1e-9 and self.portfolio:
            oldest_entry = self.portfolio.popleft()
            if oldest_entry["value"] <= 0: continue
            sell_value = min(oldest_entry["value"], remaining_to_withdraw)
            anteil = sell_value / oldest_entry["value"]
            gewinn_anteil = (oldest_entry["value"] - oldest_entry["amount_invested"]) * anteil
            investiert_anteil = oldest_entry["amount_invested"] * anteil
            steuer = 0
            if self.params.versicherung_modus:
                aktuelle_laufzeit = (current_date - oldest_entry["date"]).days / 365.25
                aktuelle_alter = self.params.eintrittsalter + (current_date - datetime.date(2025, 1, 1)).days / 365.25
                if aktuelle_alter >= 62 and aktuelle_laufzeit >= 12:
                    steuer = gewinn_anteil * 0.5 * self.params.persoenlicher_steuersatz
                else:
                    steuer = gewinn_anteil * 0.85 * self.params.persoenlicher_steuersatz
            else:
                vorabpauschalen_anteil = oldest_entry["vorabpauschalen_bereits_versteuert"] * anteil
                teilfreistellung = getattr(self.params, "teilfreistellung", 0.0)
                steuerbarer_gewinn = gewinn_anteil * (1 - teilfreistellung)
                steuerbarer_gewinn_nach_vp = max(0.0, steuerbarer_gewinn - vorabpauschalen_anteil)
                steuerfreibetrag_used = min(self.freistellungs_topf, steuerbarer_gewinn_nach_vp)
                self.freistellungs_topf -= steuerfreibetrag_used
                zu_versteuern = max(0, steuerbarer_gewinn_nach_vp - steuerfreibetrag_used)
                steuer = zu_versteuern * self.full_tax_rate
                oldest_entry["vorabpauschalen_bereits_versteuert"] -= vorabpauschalen_anteil
            ruecknahmeabschlag = getattr(self.params, "ruecknahmeabschlag", 0.0)
            ruecknahmeabschlag_val = sell_value * ruecknahmeabschlag
            netto_entnahme = sell_value - steuer - ruecknahmeabschlag_val
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
        self.ruecknahmeabschlag_summe += entnahmebetrag_effektiv * ruecknahmeabschlag
        self.ruecknahmeabschlag_real_summe += (
                                                      entnahmebetrag_effektiv * ruecknahmeabschlag) / self.kumulierte_inflation_factor
        self.kumulierte_entnahmen += netto_entnahme_summe
        self.kumulierte_entnahmen_real += netto_entnahme_summe / self.kumulierte_inflation_factor
        self.cashflows.append(netto_entnahme_summe)
        self.real_cashflows.append(netto_entnahme_summe / self.kumulierte_inflation_factor)
        self.cashflow_dates.append(current_date)


# === HILFSFUNKTIONEN FÜR PLOTS UND AUSWERTUNG ===

def berechne_xirr_und_print(cashflows, cashflow_dates, real_cashflows, label):
    try:
        xirr_nominal = pyxirr.xirr(cashflow_dates, cashflows)
        xirr_real = pyxirr.xirr(cashflow_dates, real_cashflows)
        print(f"XIRR (nominal) für {label}: {xirr_nominal:,.2%}")
        print(f"XIRR (real) für {label}: {xirr_real:,.2%}")
        return xirr_nominal, xirr_real
    except ValueError as e:
        print(f"Fehler bei der XIRR-Berechnung für {label}: {e}")
        return 0, 0


def auswerten_kosten(df_monatlich: pd.DataFrame, params: Any, label: str) -> pd.DataFrame:
    df_monatlich["Jahr"] = pd.to_datetime(df_monatlich["Datum"]).dt.year
    df_jaehrlich = df_monatlich.groupby("Jahr").last().reset_index()
    df_jaehrlich["Kosten_Kapitalanlage_nominal"] = df_jaehrlich["Gesamtfondkosten kum"]
    df_jaehrlich["Kosten_Kapitalanlage_real"] = df_jaehrlich["Gesamtfondkosten kum real"]
    if params.versicherung_modus:
        df_jaehrlich["Kosten_Depot_nominal"] = 0
        df_jaehrlich["Kosten_Depot_real"] = 0
        df_jaehrlich["Kosten_Versicherung_nominal"] = df_jaehrlich["Guthabenkosten kum"] + \
                                                      df_jaehrlich["Verwaltungskosten kum"] + \
                                                      df_jaehrlich["Abschlusskosten kum"]
        df_jaehrlich["Kosten_Versicherung_real"] = df_jaehrlich["Guthabenkosten kum real"] + \
                                                   df_jaehrlich["Verwaltungskosten kum real"] + \
                                                   df_jaehrlich["Abschlusskosten kum real"]
    else:
        df_jaehrlich["Kosten_Depot_nominal"] = df_jaehrlich["Ausgabeaufschlag kum"] + \
                                               df_jaehrlich["Rücknahmeabschlag kum"] + \
                                               df_jaehrlich["Stückkosten kum"]
        df_jaehrlich["Kosten_Depot_real"] = df_jaehrlich["Ausgabeaufschlag kum real"] + \
                                            df_jaehrlich["Rücknahmeabschlag kum real"] + \
                                            df_jaehrlich["Stückkosten kum real"]
        df_jaehrlich["Kosten_Versicherung_nominal"] = 0
        df_jaehrlich["Kosten_Versicherung_real"] = 0
    df_jaehrlich["Kosten_Service_nominal"] = df_jaehrlich["Serviceentgelt kum"]
    df_jaehrlich["Kosten_Service_real"] = df_jaehrlich["Serviceentgelt kum real"]
    df_jaehrlich["Steuern_nominal"] = df_jaehrlich["Steuern kumuliert"]
    df_jaehrlich["Steuern_real"] = df_jaehrlich["Steuern kumuliert real"]
    df_jaehrlich = df_jaehrlich.round(2)
    df_jaehrlich.to_csv(f"{label}_Kostenarten_Jahr.csv", index=False)
    print(f"Kostenaufschlüsselung für '{label}' in '{label}_Kostenarten_Jahr.csv' exportiert.")
    return df_jaehrlich


def plotten_kosten(df_kosten_jaehrlich, params):
    if params.versicherung_modus:
        kosten_spalten = [
            "Abschlusskosten kum",
            "Verwaltungskosten kum",
            "Guthabenkosten kum",
            "Gesamtfondkosten kum",
            "Serviceentgelt kum",
            "Steuern kumuliert"
        ]
    else:
        kosten_spalten = [
            "Ausgabeaufschlag kum",
            "Rücknahmeabschlag kum",
            "Stückkosten kum",
            "Gesamtfondkosten kum",
            "Serviceentgelt kum",
            "Steuern kumuliert"
        ]
    df_plot = df_kosten_jaehrlich[[col for col in kosten_spalten if col in df_kosten_jaehrlich.columns] + ["Jahr"]]
    df_plot.index = df_plot["Jahr"]
    df_plot = df_plot.drop(columns="Jahr")
    plt.figure(figsize=(14, 8))
    ax = plt.gca()
    df_plot.plot(kind="area", stacked=True, ax=ax, legend=False)
    handles, labels = ax.get_legend_handles_labels()
    new_labels_map = {
        "Abschlusskosten kum": "Abschlusskosten",
        "Verwaltungskosten kum": "Verwaltungskosten",
        "Guthabenkosten kum": "Guthabenkosten",
        "Gesamtfondkosten kum": "Kapitalanlagekosten (TER)",
        "Serviceentgelt kum": "Servicegebühren",
        "Steuern kumuliert": "Steuern",
        "Ausgabeaufschlag kum": "Ausgabeaufschlag",
        "Rücknahmeabschlag kum": "Rücknahmeabschlag",
        "Stückkosten kum": "Stückkosten",
    }
    if params.versicherung_modus:
        legend_labels = [
            "Versicherungskosten:",
            f"  - {new_labels_map['Abschlusskosten kum']}",
            f"  - {new_labels_map['Verwaltungskosten kum']}",
            f"  - {new_labels_map['Guthabenkosten kum']}",
            "Kapitalanlagekosten (TER)",
            "Servicegebühren",
            "Steuern"
        ]
        legend_handles = [
            plt.Rectangle((0, 0), 1, 1, fc="white", ec="white", lw=0),
            handles[0],
            handles[1],
            handles[2],
            handles[3],
            handles[4],
            handles[5]
        ]
    else:
        legend_labels = [
            "Depotkosten:",
            f"  - {new_labels_map['Ausgabeaufschlag kum']}",
            f"  - {new_labels_map['Rücknahmeabschlag kum']}",
            f"  - {new_labels_map['Stückkosten kum']}",
            "Kapitalanlagekosten (TER)",
            "Servicegebühren",
            "Steuern"
        ]
        legend_handles = [
            plt.Rectangle((0, 0), 1, 1, fc="white", ec="white", lw=0),
            handles[0],
            handles[1],
            handles[2],
            handles[3],
            handles[4],
            handles[5]
        ]
    plt.legend(legend_handles, legend_labels, title="Kostenarten", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.title(f"Kumulierte Kostenaufschlüsselung für {params.label}")
    plt.xlabel("Jahr")
    plt.ylabel("Kumulierte Kosten in Euro")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{params.label}_kosten_aufschluesselung.png")
    plt.close()


def plotten_entnahmen(df_kosten_jaehrlich, params):
    plt.figure(figsize=(14, 8))
    plt.plot(df_kosten_jaehrlich["Jahr"], df_kosten_jaehrlich["Kumulierte Entnahmen"], label="Kumulierte Entnahmen",
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
    if rebalancing_log:
        df_rebal = pd.DataFrame(rebalancing_log)
        df_rebal.to_csv(f"{label}_Rebalancing.csv", index=False)
        return df_rebal
    return None


def erzeuge_report(df_kosten_det, df_rebal, xirr_nominal, xirr_real, mc_results, params, market_params):
    xirr_nominal_formatted = f"{xirr_nominal:.2%}" if xirr_nominal is not None else "Berechnung fehlgeschlagen"
    xirr_real_formatted = f"{xirr_real:.2%}" if xirr_real is not None else "Berechnung fehlgeschlagen"
    end_beitragsdauer_index = min(params.beitragszahldauer * 12 - 1, len(df_kosten_det) - 1)
    depotwert_ende_beitrags = df_kosten_det['Depotwert'].iloc[end_beitragsdauer_index]
    depotwert_ende_beitrags_real = df_kosten_det['Depotwert real'].iloc[end_beitragsdauer_index]
    report_text = f"""
# Report für {params.label}
---
## Eingabeparameter
* **Eintrittsalter:** {params.eintrittsalter}
* **Laufzeit:** {params.laufzeit} Jahre
* **Monatliche Einzahlung:** {params.monthly_investment:,.2f} €
* **Jährliche Rendite (Annahme):** {market_params["annual_return"]:.2%}
* **Inflationsrate (Annahme):** {params.inflation_rate:.2%}
* **Simulierter Todesfall:** {"Ja, in Jahr " + str(params.death_year) if params.death_year else "Nein"}
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
* **Durchschnittlicher Endwert:** {mc_results["mean_value"]:,.2f} €
* **Median Endwert:** {mc_results["median_value"]:,.2f} €
* **95% Konfidenzintervall:** [{mc_results["ci_lower"]:,.2f} € - {mc_results["ci_upper"]:,.2f} €]
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


def plotten_vergleich(df_list, params_list):
    plt.figure(figsize=(14, 8))
    for df, params in zip(df_list, params_list):
        df["Jahr"] = pd.to_datetime(df["Datum"]).dt.year
        df_vergleich = df.groupby("Jahr").last().reset_index()
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

# === HAUPTPROGRAMM ===
def run_all_scenarios():
    import os
    output_path = "output/"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    all_scenarios = []

    basis_params = {
        "eintrittsalter": 35,
        "initial_investment": 150000,
        "monthly_investment": 500,
        "laufzeit": 27,
        "beitragszahldauer": 27,
        "monthly_dynamik_rate": 0.00,
        "dynamik_turnus_monate": 12,
        "sonderzahlung_jahr": 0,
        "sonderzahlung_betrag": 0,
        "regel_sonderzahlung_betrag": 0,
        "regel_sonderzahlung_turnus_jahre": 0,
        "annual_withdrawal": 0,
        "entnahme_plan": {},
        "entnahme_modus": "jährlich",
        "abgeltungssteuer_rate": 0.25,
        "soli_zuschlag_on_abgeltungssteuer": 0.055,
        "kirchensteuer_on_abgeltungssteuer": 0.0,
        "persoenlicher_steuersatz": 0.3,
        "freistellungsauftrag_jahr": 0,
        "inflation_rate": 0.02,
        "inflation_volatility": 0.01,
        "freistellungs_pauschbetrag_anpassung_rate": 0.02
    }

    market_params = {
        "annual_return": 0.06,
        "annual_volatility": 0.15,
        "csv_file": "historische_daten.csv",
        "date_column": "date",
        "price_column": "price"
    }

    params_depot = DepotParameter(
        **basis_params,
        label="Depot",
        ausgabeaufschlag=0.002,
        monthly_ausgabeaufschlag=0.002,
        ruecknahmeabschlag=0.002,
        ter=0.0045,
        serviceentgelt=0.0119,
        stueckkosten=45,
        teilfreistellung=0.3,
        basiszins=0.0255,
        rebalancing_rate=0.3,
    )
    all_scenarios.append(params_depot)

    params_versicherung = VersicherungParameter(
        **basis_params,
        label="Versicherung",
        ter=0.0045,
        serviceentgelt=0.0,
        guthabenkosten=0.0018,
        abschlusskosten_einmalig_prozent=0.025,
        abschlusskosten_monatlich_prozent=0.0252,
        verrechnungsdauer_monate=60,
        verwaltungskosten_monatlich_prozent=0.09,
        bewertungsdauer=22,
        death_year=20
    )
    all_scenarios.append(params_versicherung)

    params_depot_diy = DepotDIYParameter(
        **basis_params,
        label="Depot DIY",
        ausgabeaufschlag=0.01,
        monthly_ausgabeaufschlag=0.01,
        ruecknahmeabschlag=0.01,
        ter=0.005,
        serviceentgelt=0.0,
        stueckkosten=10.0,
        teilfreistellung=0.3,
        basiszins=0.0255,
        rebalancing_rate=0.1,
    )
    all_scenarios.append(params_depot_diy)

    df_results_all = []

    try:
        # Lade und analysiere historische Daten
        monthly_returns_hist, mean_monthly_return, std_dev_monthly_return = load_and_analyze_data(
            market_params["csv_file"],
            market_params["date_column"],
            market_params["price_column"],
            basis_params["inflation_rate"]
        )

        for params in all_scenarios:
            print(f"\n--- Simulation für {params.label} gestartet ---")

            # 1. Deterministische Simulation ausführen
            simulator = SparplanSimulator(params, annual_return=market_params["annual_return"])
            df_monatlich_log, rebalancing_log, cashflows, cashflow_dates, real_cashflows = simulator.run_simulation()

            # 2. Ergebnisse der deterministischen Simulation verarbeiten
            xirr_nominal, xirr_real = berechne_xirr_und_print(cashflows, cashflow_dates, real_cashflows, params.label)
            df_results_all.append(df_monatlich_log)
            df_kosten_jaehrlich = auswerten_kosten(df_monatlich_log.copy(), params, params.label)
            rebal_df = exportiere_rebalancing_daten(rebalancing_log, params.label)
            plotten_kosten(df_kosten_jaehrlich, params)
            plotten_entnahmen(df_kosten_jaehrlich, params)

            # 3. Monte-Carlo-Simulation (Normal-Szenario) ausführen und analysieren
            num_simulations_normal = 5000
            mc_results_normal, final_values_normal, annual_returns_normal, max_drawdowns_normal = run_monte_carlo_simulation(
                mean_monthly_return,
                std_dev_monthly_return,
                params.initial_investment,
                params.laufzeit,
                num_simulations_normal,
                monthly_investment=params.monthly_investment,
                monthly_dynamik_rate=params.monthly_dynamik_rate,
                dynamik_turnus_monate=params.dynamik_turnus_monate,
                beitragszahldauer_monate=params.beitragszahldauer * 12
            )

            # 4. Report und Plots erstellen
            erzeuge_report(
                df_kosten_jaehrlich, rebal_df, xirr_nominal, xirr_real,
                {"mean_value": np.mean(final_values_normal[params.laufzeit]),
                 "median_value": np.median(final_values_normal[params.laufzeit]),
                 "ci_lower": np.percentile(final_values_normal[params.laufzeit], 2.5),
                 "ci_upper": np.percentile(final_values_normal[params.laufzeit], 97.5)},
                params,
                market_params
            )
            analyze_and_plot_results(
                mc_results_normal, final_values_normal, annual_returns_normal, max_drawdowns_normal,
                f"Normales Szenario: {params.label}", params.laufzeit, params.initial_investment, num_simulations_normal
            )
            print(f"--- Simulation für {params.label} beendet ---")

        # Vergleichsplots für alle Szenarien
        plotten_vergleich(df_results_all, all_scenarios)

        # === ERWEITERTE WORST-CASE-ANALYSE FÜR ALLE SZENARIEN ===
        print("\n=== Erweiterte Monte-Carlo-Szenarien ===")

        # Historische Worst-Case-Daten einmalig laden und Details ausgeben
        worst_returns_historical, worst_historical_start_year, worst_historical_return = get_worst_3_years(
            monthly_returns_hist)
        print(
            f"Der historisch schlechteste 3-Jahres-Zeitraum war {worst_historical_start_year}-{worst_historical_start_year + 2} mit einer kumulierten Rendite von {worst_historical_return:.2%}.")
        print("-" * 50)

        num_simulations_worst_case = 5000

        for params in all_scenarios:
            print(f"\n--- Worst-Case-Analyse für {params.label} gestartet ---")

            # Führe eine erste MC-Simulation im normalen Szenario aus, um die Pfade zu generieren
            mc_results_normal, _, _, _ = run_monte_carlo_simulation(
                mean_monthly_return,
                std_dev_monthly_return,
                params.initial_investment,
                params.laufzeit,
                num_simulations_worst_case,
                monthly_investment=params.monthly_investment,
                monthly_dynamik_rate=params.monthly_dynamik_rate,
                dynamik_turnus_monate=params.dynamik_turnus_monate,
                beitragszahldauer_monate=params.beitragszahldauer * 12
            )

            # Extrahieren des schlechtesten simulierten Pfads aus den Ergebnissen der normalen MC-Simulation
            worst_returns_simulated, worst_simulated_return = get_worst_3_years_from_simulations(mc_results_normal,
                                                                                                 params.laufzeit)
            print(
                f"Der schlechteste simulierte 3-Jahres-Zeitraum hatte eine kumulierte Rendite von {worst_simulated_return:.2%}.")
            print("-" * 50)

            # 1. Historisches Worst-Case-Szenario am Anfang
            print("--- Simulation: Worst-Case (Historisch) am Anfang ---")
            mc_results_hist_start, final_values_hist_start, annual_returns_hist_start, max_drawdowns_hist_start = run_monte_carlo_simulation(
                mean_monthly_return, std_dev_monthly_return, params.initial_investment, params.laufzeit,
                num_simulations_worst_case, scenario='start', worst_returns=worst_returns_historical,
                monthly_investment=params.monthly_investment,
                monthly_dynamik_rate=params.monthly_dynamik_rate,
                dynamik_turnus_monate=params.dynamik_turnus_monate,
                beitragszahldauer_monate=params.beitragszahldauer * 12
            )
            analyze_and_plot_results(
                mc_results_hist_start, final_values_hist_start, annual_returns_hist_start, max_drawdowns_hist_start,
                f"Worst-Case (Historisch) am Anfang: {params.label}", params.laufzeit, params.initial_investment,
                num_simulations_worst_case
            )

            # 2. Historisches Worst-Case-Szenario zu Beginn der Entnahmephase
            print("--- Simulation: Worst-Case (Historisch) bei Entnahme ---")
            mc_results_hist_withdrawal, final_values_hist_withdrawal, annual_returns_hist_withdrawal, max_drawdowns_hist_withdrawal = run_monte_carlo_simulation(
                mean_monthly_return, std_dev_monthly_return, params.initial_investment, params.laufzeit,
                num_simulations_worst_case, scenario='withdrawal', worst_returns=worst_returns_historical,
                monthly_investment=params.monthly_investment,
                monthly_dynamik_rate=params.monthly_dynamik_rate,
                dynamik_turnus_monate=params.dynamik_turnus_monate,
                beitragszahldauer_monate=params.beitragszahldauer * 12
            )
            analyze_and_plot_results(
                mc_results_hist_withdrawal, final_values_hist_withdrawal, annual_returns_hist_withdrawal,
                max_drawdowns_hist_withdrawal,
                f"Worst-Case (Historisch) bei Entnahme: {params.label}", params.laufzeit, params.initial_investment,
                num_simulations_worst_case
            )

            # 3. Simuliertes Worst-Case-Szenario am Anfang
            print("--- Simulation: Worst-Case (Simuliert) am Anfang ---")
            mc_results_sim_start, final_values_sim_start, annual_returns_sim_start, max_drawdowns_sim_start = run_monte_carlo_simulation(
                mean_monthly_return, std_dev_monthly_return, params.initial_investment, params.laufzeit,
                num_simulations_worst_case, scenario='start', worst_returns=worst_returns_simulated,
                monthly_investment=params.monthly_investment,
                monthly_dynamik_rate=params.monthly_dynamik_rate,
                dynamik_turnus_monate=params.dynamik_turnus_monate,
                beitragszahldauer_monate=params.beitragszahldauer * 12
            )
            analyze_and_plot_results(
                mc_results_sim_start, final_values_sim_start, annual_returns_sim_start, max_drawdowns_sim_start,
                f"Worst-Case (Simuliert) am Anfang: {params.label}", params.laufzeit, params.initial_investment,
                num_simulations_worst_case
            )

            # 4. Simuliertes Worst-Case-Szenario zu Beginn der Entnahmephase
            print("--- Simulation: Worst-Case (Simuliert) bei Entnahme ---")
            mc_results_sim_withdrawal, final_values_sim_withdrawal, annual_returns_sim_withdrawal, max_drawdowns_sim_withdrawal = run_monte_carlo_simulation(
                mean_monthly_return, std_dev_monthly_return, params.initial_investment, params.laufzeit,
                num_simulations_worst_case, scenario='withdrawal', worst_returns=worst_returns_simulated,
                monthly_investment=params.monthly_investment,
                monthly_dynamik_rate=params.monthly_dynamik_rate,
                dynamik_turnus_monate=params.dynamik_turnus_monate,
                beitragszahldauer_monate=params.beitragszahldauer * 12
            )
            analyze_and_plot_results(
                mc_results_sim_withdrawal, final_values_sim_withdrawal, annual_returns_sim_withdrawal,
                max_drawdowns_sim_withdrawal,
                f"Worst-Case (Simuliert) bei Entnahme: {params.label}", params.laufzeit, params.initial_investment,
                num_simulations_worst_case
            )

            print(f"--- Worst-Case-Analyse für {params.label} beendet ---")

    except FileNotFoundError as e:
        print(
            f"Fehler: {e}. Bitte stellen Sie sicher, dass die Datei '{market_params['csv_file']}' im selben Verzeichnis liegt.")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")


if __name__ == "__main__":
    run_all_scenarios()