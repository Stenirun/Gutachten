package com.bauerfinanz.gutachten;

import java.util.*;

public class SimulationUtils {
    /**
     * Berechnet den Internen Zinsfuß (IRR) aus einer Liste von Cashflows.
     * Gibt den jährlichen IRR zurück oder Double.NaN bei Fehler.
     */
    public static double calculateIRR(List<Double> cashflows) {
        // Newton-Raphson für monatlichen IRR, annualisiert
        double guess = 0.1;
        int maxIter = 1000;
        double tol = 1e-7;
        double irr = guess;
        for (int iter = 0; iter < maxIter; iter++) {
            double npv = 0.0;
            double d_npv = 0.0;
            for (int t = 0; t < cashflows.size(); t++) {
                double cf = cashflows.get(t);
                npv += cf / Math.pow(1 + irr, t);
                d_npv -= t * cf / Math.pow(1 + irr, t + 1);
            }
            if (Math.abs(npv) < tol) return Math.pow(1 + irr, 12) - 1;
            if (Math.abs(d_npv) < tol) return Double.NaN;
            irr -= npv / d_npv;
            if (irr < -0.9999 || irr > 10) return Double.NaN; // Unplausible Werte
        }
        return Double.NaN;
    }

    /**
     * Führt eine Monte-Carlo-Simulation für die Sparplan-Parameter aus.
     * Gibt die Liste der Endwerte und statistische Kennzahlen zurück.
     */
    public static MonteCarloResult runMonteCarlo(SparplanParameter params, int numRuns) {
        List<Double> finalValues = new ArrayList<>();
        int endOfBeitragsPeriodIndex = params.beitragszahldauer * 12;
        if (endOfBeitragsPeriodIndex >= params.laufzeit * 12) {
            endOfBeitragsPeriodIndex = params.laufzeit * 12 - 1;
        }
        Random rand = new Random();
        for (int i = 0; i < numRuns; i++) {
            double randomAnnualReturn = params.annualReturn + rand.nextGaussian() * params.annualStdDev;
            SparplanParameter mcParams = cloneWithNewReturn(params, randomAnnualReturn);
            SparplanSimulator simulator = new SparplanSimulator(mcParams);
            SparplanSimulator.SimulationResult result = simulator.runSimulation();
            List<Map<String, Object>> kostenLogs = result.kostenLogs;
            double depotwert = (double) kostenLogs.get(endOfBeitragsPeriodIndex).get("Depotwert");
            finalValues.add(depotwert);
        }
        double mean = finalValues.stream().mapToDouble(Double::doubleValue).average().orElse(Double.NaN);
        double median = getMedian(finalValues);
        double ciLower = getPercentile(finalValues, 2.5);
        double ciUpper = getPercentile(finalValues, 97.5);
        return new MonteCarloResult(finalValues, mean, median, ciLower, ciUpper);
    }

    private static SparplanParameter cloneWithNewReturn(SparplanParameter params, double newReturn) {
        SparplanParameter clone = new SparplanParameter();
        // Kopiere alle Felder
        clone.label = params.label;
        clone.versicherungModus = params.versicherungModus;
        clone.eintrittsalter = params.eintrittsalter;
        clone.initialInvestment = params.initialInvestment;
        clone.monthlyInvestment = params.monthlyInvestment;
        clone.laufzeit = params.laufzeit;
        clone.beitragszahldauer = params.beitragszahldauer;
        clone.monthlyDynamikRate = params.monthlyDynamikRate;
        clone.dynamikTurnusMonate = params.dynamikTurnusMonate;
        clone.sonderzahlungJahr = params.sonderzahlungJahr;
        clone.sonderzahlungBetrag = params.sonderzahlungBetrag;
        clone.regelSonderzahlungBetrag = params.regelSonderzahlungBetrag;
        clone.regelSonderzahlungTurnusJahre = params.regelSonderzahlungTurnusJahre;
        clone.annualWithdrawal = params.annualWithdrawal;
        clone.annualReturn = newReturn;
        clone.ausgabeaufschlag = params.ausgabeaufschlag;
        clone.ruecknahmeabschlag = params.ruecknahmeabschlag;
        clone.ter = params.ter;
        clone.serviceentgelt = params.serviceentgelt;
        clone.stueckkosten = params.stueckkosten;
        clone.abschlusskostenEinmaligProzent = params.abschlusskostenEinmaligProzent;
        clone.abschlusskostenMonatlichProzent = params.abschlusskostenMonatlichProzent;
        clone.verrechnungsdauerMonate = params.verrechnungsdauerMonate;
        clone.verwaltungskostenMonatlichProzent = params.verwaltungskostenMonatlichProzent;
        clone.abgeltungssteuerRate = params.abgeltungssteuerRate;
        clone.soliZuschlagOnAbgeltungssteuer = params.soliZuschlagOnAbgeltungssteuer;
        clone.kirchensteuerOnAbgeltungssteuer = params.kirchensteuerOnAbgeltungssteuer;
        clone.persoenlicherSteuersatz = params.persoenlicherSteuersatz;
        clone.freistellungsauftragJahr = params.freistellungsauftragJahr;
        clone.teilfreistellung = params.teilfreistellung;
        clone.basiszins = params.basiszins;
        clone.rebalancingRate = params.rebalancingRate;
        clone.entnahmeModus = params.entnahmeModus;
        clone.bewertungsdauer = params.bewertungsdauer;
        clone.annualStdDev = params.annualStdDev;
        return clone;
    }

    private static double getMedian(List<Double> values) {
        List<Double> sorted = new ArrayList<>(values);
        Collections.sort(sorted);
        int n = sorted.size();
        if (n == 0) return Double.NaN;
        if (n % 2 == 1) return sorted.get(n / 2);
        return (sorted.get(n / 2 - 1) + sorted.get(n / 2)) / 2.0;
    }

    private static double getPercentile(List<Double> values, double percentile) {
        List<Double> sorted = new ArrayList<>(values);
        Collections.sort(sorted);
        int n = sorted.size();
        if (n == 0) return Double.NaN;
        double rank = percentile / 100.0 * (n - 1);
        int low = (int) Math.floor(rank);
        int high = (int) Math.ceil(rank);
        if (low == high) return sorted.get(low);
        double weight = rank - low;
        return sorted.get(low) * (1 - weight) + sorted.get(high) * weight;
    }

    public static class MonteCarloResult {
        public List<Double> finalValues;
        public double mean;
        public double median;
        public double ciLower;
        public double ciUpper;
        public MonteCarloResult(List<Double> finalValues, double mean, double median, double ciLower, double ciUpper) {
            this.finalValues = finalValues;
            this.mean = mean;
            this.median = median;
            this.ciLower = ciLower;
            this.ciUpper = ciUpper;
        }
    }
}
