from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from math import inf

@dataclass
class ProviderMetrics:
    name : str
    healthy: bool
    avg_latency_ms : float
    cost_per_1k : float

class ModelRouter:
    # Pure provider selection logic

    LATENCY_WEIGHT = 0.6 # 60% latency priority
    COST_WEIGHT = 0.4    # 40% cost priority

    def __init__(self, providers: List[ProviderMetrics]):
        self.providers = providers 
    
    def select_provider(
        self,
        auto: bool = False,
        preferred: Optional[str] = None
    ) -> str:
        # select best provider by scoring

        # Preferred model 
        if preferred:
            healthy_pref = next((p for p in self.providers if p.name == preferred and p.healthy), None)
            if healthy_pref:
                return preferred
        
        if not auto: 
            raise ValueError("Must specify model or auto = True")

        # Auto: score healthy providers
        candidates = [p for p in self.providers if p.healthy] 
        if not candidates:
            raise ValueError("No healthy providers available")
        
        # Compute min/max for normalization
        avg_latencies = [p.avg_latency_ms for p in candidates]
        costs = [p.cost_per_1k for p in candidates]
        
        min_latency = min(avg_latencies)
        max_latency = max(avg_latencies)
        min_cost = min(costs)
        max_cost = max(costs)
        
        # Weighted score: apply min-max normalization
        scored = [] 
        for p in candidates:
            # Normalize latency and cost to 0..1 (inverted since lower is better)
            latency_range = max_latency - min_latency
            normalized_latency = 0.0
            if latency_range > 0:
                normalized_latency = (p.avg_latency_ms - min_latency) / latency_range
            
            cost_range = max_cost - min_cost
            normalized_cost = 0.0
            if cost_range > 0:
                normalized_cost = (p.cost_per_1k - min_cost) / cost_range
            
            total_score = normalized_latency * self.LATENCY_WEIGHT + normalized_cost * self.COST_WEIGHT
            scored.append((total_score, p.name))

        scored.sort() # Lowest score first
        return scored[0][1] # Best provider name
# Global singleton (config driven) 
PROVIDER_METRICS = [ 
    ProviderMetrics("openai", True, 250, 0.375),
    ProviderMetrics("gemini", True, 180, 0.1875),
]

router = ModelRouter(PROVIDER_METRICS)