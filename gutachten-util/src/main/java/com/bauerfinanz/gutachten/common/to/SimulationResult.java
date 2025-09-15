package com.bauerfinanz.gutachten.common.to;

import java.util.List;
import java.util.Map;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SimulationResult {
	public List<Map<String, Object>> kostenLogs;
	public List<Map<String, Object>> rebalancingLogs;
	public List<Double> cashflows;
}