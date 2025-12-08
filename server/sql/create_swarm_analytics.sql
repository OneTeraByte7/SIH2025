CREATE TABLE IF NOT EXISTS swarm_analytics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    simulation_id TEXT REFERENCES simulations(simulation_id),
    algorithm_name TEXT,
    duration FLOAT,
    friendly_losses INTEGER,
    enemy_losses INTEGER,
    survival_rate FLOAT,
    kill_ratio FLOAT,
    assets_protected INTEGER,
    mission_success BOOLEAN,
    telemetry JSONB,
    statistics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_swarm_analytics_simulation ON swarm_analytics(simulation_id);
CREATE INDEX IF NOT EXISTS idx_swarm_analytics_algorithm ON swarm_analytics(algorithm_name);

-- Enable RLS to match project policy style
ALTER TABLE swarm_analytics ENABLE ROW LEVEL SECURITY;

-- Create policy allowing all operations (customize for production)
CREATE POLICY "Allow all operations on swarm_analytics" ON swarm_analytics
    FOR ALL
    USING (true)
    WITH CHECK (true);
