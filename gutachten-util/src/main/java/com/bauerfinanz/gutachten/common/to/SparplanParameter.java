package com.bauerfinanz.gutachten.common.to;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SparplanParameter {
    public String label;
    public boolean versicherungModus;
    public int eintrittsalter;
    public double initialInvestment;
    public double monthlyInvestment;
    public int laufzeit;
    public int beitragszahldauer;
    public double monthlyDynamikRate;
    public int dynamikTurnusMonate;
    public int sonderzahlungJahr;
    public double sonderzahlungBetrag;
    public double regelSonderzahlungBetrag;
    public int regelSonderzahlungTurnusJahre;
    public double annualWithdrawal;
    public double annualReturn;
    public double ausgabeaufschlag;
    public double ruecknahmeabschlag;
    public double ter;
    public double serviceentgelt;
    public double stueckkosten;
    public double abschlusskostenEinmaligProzent;
    public double abschlusskostenMonatlichProzent;
    public int verrechnungsdauerMonate;
    public double verwaltungskostenMonatlichProzent;
    public double abgeltungssteuerRate;
    public double soliZuschlagOnAbgeltungssteuer;
    public double kirchensteuerOnAbgeltungssteuer;
    public double persoenlicherSteuersatz;
    public double freistellungsauftragJahr;
    public double teilfreistellung;
    public double basiszins;
    public double rebalancingRate;
    public String entnahmeModus;
    public int bewertungsdauer;
    public double annualStdDev;
    public double monthlyReturn;
    public double fullTaxRate;

    public double getFullTaxRate() {
        return abgeltungssteuerRate * (1 + soliZuschlagOnAbgeltungssteuer + kirchensteuerOnAbgeltungssteuer);
    }
}
