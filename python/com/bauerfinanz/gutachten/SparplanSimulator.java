package com.bauerfinanz.gutachten;

import java.time.LocalDate;
import java.util.*;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;

public class SparplanSimulator {
    private final SparplanParameter params;
    private final Deque<Map<String, Object>> portfolio;
    private final List<Map<String, Object>> rebalancingLog;
    private final List<Map<String, Object>> monatlicheKostenLogs;
    private final List<Double> cashflows;

    private double ausgabeaufschlagSumme;
    private double ruecknahmeabschlagSumme;
    private double stueckkostenSumme;
    private double abschlusskostenSumme;
    private double verwaltungskostenSumme;
    private double terSumme;
    private double serviceentgeltSumme;
    private double kumulierteEntnahmen;
    private double totalTaxPaid;
    private double freistellungsTopf;
    private double monthlyInvestment;
    private final double[] abschlusskostenMonatlichRest;
    private final double[] abschlusskostenEinmaligRest;

    public SparplanSimulator(SparplanParameter params) {
        this.params = params;
        this.portfolio = new ArrayDeque<>();
        this.rebalancingLog = new ArrayList<>();
        this.monatlicheKostenLogs = new ArrayList<>();
        this.cashflows = new ArrayList<>();

        this.ausgabeaufschlagSumme = 0;
        this.ruecknahmeabschlagSumme = 0;
        this.stueckkostenSumme = 0;
        this.abschlusskostenSumme = 0;
        this.verwaltungskostenSumme = 0;
        this.terSumme = 0;
        this.serviceentgeltSumme = 0;
        this.kumulierteEntnahmen = 0;
        this.totalTaxPaid = 0;
        this.freistellungsTopf = params.freistellungsauftragJahr;
        this.monthlyInvestment = params.monthlyInvestment;
        this.abschlusskostenMonatlichRest = new double[params.laufzeit * 12];
        this.abschlusskostenEinmaligRest = new double[params.laufzeit * 12];
    }

    public SimulationResult runSimulation() {
        initializeSimulation();
        for (int month = 0; month < params.laufzeit * 12; month++) {
            simulateMonth(month);
        }
        finalizeSimulation();
        return new SimulationResult(monatlicheKostenLogs, rebalancingLog, cashflows);
    }

    private void initializeSimulation() {
        params.monthlyReturn = Math.pow(1 + params.annualReturn, 1.0 / 12) - 1;
        params.fullTaxRate = params.abgeltungssteuerRate * (1 + params.soliZuschlagOnAbgeltungssteuer + params.kirchensteuerOnAbgeltungssteuer);

        if (params.versicherungModus) {
            params.ausgabeaufschlag = 0.0;
            params.ruecknahmeabschlag = 0.0;
            params.stueckkosten = 0.0;
        } else {
            params.abschlusskostenEinmaligProzent = 0.0;
            params.abschlusskostenMonatlichProzent = 0.0;
            params.verwaltungskostenMonatlichProzent = 0.0;
        }

        double aufschlag = params.initialInvestment * params.ausgabeaufschlag;
        double nettobetrag = params.initialInvestment - aufschlag;
        ausgabeaufschlagSumme += aufschlag;
        cashflows.add(-params.initialInvestment);

        if (nettobetrag > 0) {
            Map<String, Object> initialInvestment = new HashMap<>();
            initialInvestment.put("date", LocalDate.of(2025, 1, 1));
            initialInvestment.put("amountInvested", nettobetrag);
            initialInvestment.put("units", nettobetrag);
            initialInvestment.put("value", nettobetrag);
            initialInvestment.put("startOfPrevYearValue", nettobetrag);
            initialInvestment.put("vorabpauschalenBereitsVersteuert", 0.0);
            portfolio.add(initialInvestment);
        }
    }

    private void simulateMonth(int month) {
        LocalDate currentDate = LocalDate.of(2025, 1, 1).plusMonths(month);
        boolean isJanuary = currentDate.getMonthValue() == 1;
        if (isJanuary) {
            freistellungsTopf = params.freistellungsauftragJahr;
        }
        handleMonthlyInvestment(month, currentDate);
        handleCosts(month, currentDate);
        handleTaxes(currentDate);
        handleRebalancing(currentDate);
        for (Map<String, Object> entry : portfolio) {
            entry.put("value", (double) entry.get("value") * (1 + params.monthlyReturn));
        }
        handleWithdrawals(month, currentDate);
        double depotwert = portfolio.stream().mapToDouble(e -> (double) e.get("value")).sum();
        Map<String, Object> logEntry = new HashMap<>();
        logEntry.put("Datum", currentDate);
        logEntry.put("Depotwert", depotwert);
        logEntry.put("Ausgabeaufschlag kum", ausgabeaufschlagSumme);
        logEntry.put("Rücknahmeabschlag kum", ruecknahmeabschlagSumme);
        logEntry.put("Stückkosten kum", stueckkostenSumme);
        logEntry.put("Gesamtfondkosten kum", terSumme);
        logEntry.put("Serviceentgelt kum", serviceentgeltSumme);
        logEntry.put("Abschlusskosten kum", abschlusskostenSumme);
        logEntry.put("Verwaltungskosten kum", verwaltungskostenSumme);
        logEntry.put("Steuern kumuliert", totalTaxPaid);
        logEntry.put("Kumulierte Entnahmen", kumulierteEntnahmen);
        monatlicheKostenLogs.add(logEntry);
        if (currentDate.getMonthValue() == 12) {
            for (Map<String, Object> entry : portfolio) {
                entry.put("startOfPrevYearValue", entry.get("value"));
            }
        }
    }

    private void handleMonthlyInvestment(int month, LocalDate currentDate) {
        // Adjust monthly investment based on dynamics
        if (month > 0 && month % params.dynamikTurnusMonate == 0) {
            monthlyInvestment *= (1 + params.monthlyDynamikRate);
        }

        // Check for one-time and regular payments
        boolean isEinmalig = month == params.sonderzahlungJahr * 12;
        boolean isRegelmaessig = params.regelSonderzahlungTurnusJahre > 0 && month > 0 && month % (params.regelSonderzahlungTurnusJahre * 12) == 0;

        // Process one-time and regular payments
        if (isEinmalig || isRegelmaessig) {
            double betrag = isEinmalig ? params.sonderzahlungBetrag : params.regelSonderzahlungBetrag;
            if (betrag > 0) {
                cashflows.add(-betrag);
                double netto;
                if (!params.versicherungModus) {
                    double aufschlag = betrag * params.ausgabeaufschlag;
                    netto = betrag - aufschlag;
                    ausgabeaufschlagSumme += aufschlag;
                } else {
                    netto = betrag;
                }
                portfolio.add(createPortfolioEntry(currentDate, netto));
            }
        }

        // Process monthly investment if within contribution period
        if (month < params.beitragszahldauer * 12) {
            double aufschlag = monthlyInvestment * params.ausgabeaufschlag;
            double netto = monthlyInvestment - aufschlag;
            ausgabeaufschlagSumme += aufschlag;
            cashflows.add(-monthlyInvestment);
            portfolio.add(createPortfolioEntry(currentDate, netto));
        }
    }

    private void handleCosts(int month, LocalDate currentDate) {
        double depotwert = portfolio.stream().mapToDouble(e -> (double) e.get("value")).sum();
        if (params.versicherungModus && month < params.beitragszahldauer * 12) {
            double verwaltungskosten = monthlyInvestment * params.verwaltungskostenMonatlichProzent;
            applyCostToPortfolio(depotwert, verwaltungskosten);
            verwaltungskostenSumme += verwaltungskosten;
            if (month < params.verrechnungsdauerMonate) {
                double abschlussKosten = abschlusskostenEinmaligRest[month] + abschlusskostenMonatlichRest[month];
                applyCostToPortfolio(depotwert, abschlussKosten);
                abschlusskostenSumme += abschlussKosten;
            }
        }
        if (currentDate.getMonthValue() == 1) {
            if (depotwert > 0) {
                double fondKosten = depotwert * params.ter;
                double serviceKosten = depotwert * params.serviceentgelt;
                double stueckKosten = params.stueckkosten;
                double totalKosten = fondKosten + serviceKosten + stueckKosten;
                applyCostToPortfolio(depotwert, totalKosten);
                terSumme += fondKosten;
                serviceentgeltSumme += serviceKosten;
                stueckkostenSumme += stueckKosten;
            }
        }
    }

    private void handleTaxes(LocalDate currentDate) {
        boolean isJanuary = currentDate.getMonthValue() == 1;
        if (!params.versicherungModus && isJanuary) {
            for (Map<String, Object> entry : portfolio) {
                double startValue = (double) entry.getOrDefault("startOfPrevYearValue", 0.0);
                double fiktiverErtrag = startValue * params.basiszins;
                double realErtrag = (double) entry.get("value") - startValue;
                double steuerbarerErtrag = Math.min(fiktiverErtrag, realErtrag);
                double steuerfreibetrag = Math.min(freistellungsTopf, steuerbarerErtrag * (1 - params.teilfreistellung));
                double zuVersteuern = Math.max(0, steuerbarerErtrag * (1 - params.teilfreistellung) - steuerfreibetrag);
                double steuer = Math.max(0, zuVersteuern * params.fullTaxRate);
                if (steuer > 0) {
                    entry.put("value", (double) entry.get("value") - steuer);
                    entry.put("vorabpauschalenBereitsVersteuert", (double) entry.getOrDefault("vorabpauschalenBereitsVersteuert", 0.0) + zuVersteuern);
                    totalTaxPaid += steuer;
                    freistellungsTopf -= steuerfreibetrag;
                }
            }
        }
    }

    private void handleRebalancing(LocalDate currentDate) {
        if (!params.versicherungModus && currentDate.getMonthValue() == 12 && params.rebalancingRate > 0) {
            double depotwert = portfolio.stream().mapToDouble(e -> (double) e.get("value")).sum();
            double umzuschichten = depotwert * params.rebalancingRate;
            if (umzuschichten > 0) {
                double remaining = umzuschichten;
                Deque<Map<String, Object>> tempQueue = new ArrayDeque<>();
                double totalVerkauf = 0.0;
                double totalSteuer = 0.0;
                double totalNetto = 0.0;
                while (remaining > 1e-9 && !portfolio.isEmpty()) {
                    Map<String, Object> entry = portfolio.pollFirst();
                    if ((double) entry.get("value") <= 0) continue;
                    double sellValue = Math.min((double) entry.get("value"), remaining);
                    double prop = sellValue / (double) entry.get("value");
                    double costBasis = (double) entry.get("amountInvested") * prop;
                    double gain = sellValue - costBasis;
                    double steuerbarerGewinn = gain * (1 - params.teilfreistellung);
                    double vorabUsed = Math.min((double) entry.getOrDefault("vorabpauschalenBereitsVersteuert", 0.0) * prop, steuerbarerGewinn);
                    steuerbarerGewinn = Math.max(0.0, steuerbarerGewinn - vorabUsed);
                    double steuerfreibetrag = Math.min(freistellungsTopf, steuerbarerGewinn);
                    freistellungsTopf -= steuerfreibetrag;
                    double effektiverSteuersatz = Math.min(params.fullTaxRate, params.persoenlicherSteuersatz);
                    double steuer = Math.max(0.0, (steuerbarerGewinn - steuerfreibetrag) * effektiverSteuersatz);
                    double ruecknahmeabschlag = sellValue * params.ruecknahmeabschlag;
                    double nettoReinvest = sellValue - steuer - ruecknahmeabschlag;
                    totalTaxPaid += steuer;
                    ruecknahmeabschlagSumme += ruecknahmeabschlag;
                    totalVerkauf += sellValue;
                    totalSteuer += steuer;
                    totalNetto += nettoReinvest;
                    entry.put("value", (double) entry.get("value") - sellValue);
                    entry.put("amountInvested", (double) entry.get("amountInvested") - costBasis);
                    entry.put("vorabpauschalenBereitsVersteuert", Math.max(0.0, (double) entry.getOrDefault("vorabpauschalenBereitsVersteuert", 0.0) - vorabUsed));
                    if ((double) entry.get("value") > 1e-9) {
                        tempQueue.add(entry);
                    }
                    remaining -= sellValue;
                }
                portfolio.addAll(tempQueue);
                if (totalNetto > 1e-9) {
                    portfolio.add(createPortfolioEntry(currentDate, totalNetto));
                }
                Map<String, Object> log = new HashMap<>();
                log.put("Datum", currentDate);
                log.put("Bruttoverkauf", totalVerkauf);
                log.put("Steuer", totalSteuer);
                log.put("Netto reinvestiert", totalNetto);
                rebalancingLog.add(log);
            }
        }
    }

    private void handleWithdrawals(int month, LocalDate currentDate) {
        if (month >= params.beitragszahldauer * 12) {
            double depotwert = portfolio.stream().mapToDouble(e -> (double) e.get("value")).sum();
            double entnahmeBetrag = 0;
            if ("jährlich".equals(params.entnahmeModus) && currentDate.getMonthValue() == 1) {
                entnahmeBetrag = Math.min(params.annualWithdrawal, depotwert);
            } else if ("monatlich".equals(params.entnahmeModus)) {
                entnahmeBetrag = Math.min(params.annualWithdrawal / 12, depotwert);
            }
            if (entnahmeBetrag > 0) {
                cashflows.add(entnahmeBetrag);
                double remainingEntnahme = entnahmeBetrag;
                while (remainingEntnahme > 1e-9 && !portfolio.isEmpty()) {
                    Map<String, Object> entry = portfolio.pollFirst();
                    double value = (double) entry.get("value");
                    if (value >= remainingEntnahme) {
                        entry.put("value", value - remainingEntnahme);
                        kumulierteEntnahmen += remainingEntnahme;
                        if ((double) entry.get("value") > 1e-9) {
                            portfolio.addFirst(entry);
                        }
                        remainingEntnahme = 0;
                    } else {
                        kumulierteEntnahmen += value;
                        remainingEntnahme -= value;
                    }
                }
            }
        }
    }

    private void finalizeSimulation() {
        double restwert = portfolio.stream().mapToDouble(e -> (double) e.get("value")).sum();
        double investiert = portfolio.stream().mapToDouble(e -> (double) e.get("amountInvested")).sum();
        LocalDate endDatum = LocalDate.of(2025, 1, 1).plusMonths(params.laufzeit * 12);
        if (restwert > 1e-9) {
            double gewinn = Math.max(0.0, restwert - investiert);
            double steuer = 0;
            if (params.versicherungModus) {
                int aktuelleLaufzeit = params.laufzeit;
                int aktuelleAlter = params.eintrittsalter + aktuelleLaufzeit;
                steuer = gewinn * (aktuelleAlter >= 62 && aktuelleLaufzeit >= 12 ? 0.5 : 0.85) * params.persoenlicherSteuersatz;
            } else {
                double steuerbar = gewinn * (1 - params.teilfreistellung);
                double bereitsVersteuert = portfolio.stream().mapToDouble(e -> (double) e.getOrDefault("vorabpauschalenBereitsVersteuert", 0.0)).sum();
                steuerbar = Math.max(0.0, steuerbar - bereitsVersteuert);
                double effektiverSteuersatz = Math.min(params.fullTaxRate, params.persoenlicherSteuersatz);
                steuer = steuerbar * effektiverSteuersatz;
            }
            double ruecknahmeabschlag = restwert * params.ruecknahmeabschlag;
            totalTaxPaid += steuer;
            ruecknahmeabschlagSumme += ruecknahmeabschlag;
            double restwertNet = restwert - steuer - ruecknahmeabschlag;
            cashflows.add(restwertNet);
            kumulierteEntnahmen += restwertNet;
        }
        Map<String, Object> finalLogEntry = new HashMap<>();
        finalLogEntry.put("Datum", endDatum);
        finalLogEntry.put("Depotwert", 0);
        finalLogEntry.put("Ausgabeaufschlag kum", ausgabeaufschlagSumme);
        finalLogEntry.put("Rücknahmeabschlag kum", ruecknahmeabschlagSumme);
        finalLogEntry.put("Stückkosten kum", stueckkostenSumme);
        finalLogEntry.put("Gesamtfondkosten kum", terSumme);
        finalLogEntry.put("Serviceentgelt kum", serviceentgeltSumme);
        finalLogEntry.put("Abschlusskosten kum", abschlusskostenSumme);
        finalLogEntry.put("Verwaltungskosten kum", verwaltungskostenSumme);
        finalLogEntry.put("Steuern kumuliert", totalTaxPaid);
        finalLogEntry.put("Kumulierte Entnahmen", kumulierteEntnahmen);
        monatlicheKostenLogs.add(finalLogEntry);
    }

    private Map<String, Object> createPortfolioEntry(LocalDate date, double value) {
        Map<String, Object> entry = new HashMap<>();
        entry.put("date", date);
        entry.put("amountInvested", value);
        entry.put("value", value);
        entry.put("startOfPrevYearValue", value);
        entry.put("vorabpauschalenBereitsVersteuert", 0.0);
        return entry;
    }

    private void applyCostToPortfolio(double depotwert, double kosten) {
        for (Map<String, Object> entry : portfolio) {
            double value = (double) entry.get("value");
            double anteil = depotwert > 0 ? value / depotwert : 0;
            entry.put("value", value - kosten * anteil);
        }
    }

    public static class SimulationResult {
        public List<Map<String, Object>> kostenLogs;
        public List<Map<String, Object>> rebalancingLogs;
        public List<Double> cashflows;
        public SimulationResult(List<Map<String, Object>> kostenLogs, List<Map<String, Object>> rebalancingLogs, List<Double> cashflows) {
            this.kostenLogs = kostenLogs;
            this.rebalancingLogs = rebalancingLogs;
            this.cashflows = cashflows;
        }
    }
}
