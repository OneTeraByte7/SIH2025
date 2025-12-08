-- Supabase Database Schema for Drone Swarm Simulation

-- Create simulations table
CREATE TABLE IF NOT EXISTS simulations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    simulation_id TEXT UNIQUE NOT NULL,
    config JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'initializing',
    progress FLOAT DEFAULT 0,
    statistics JSONB,
    frames JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_simulations_simulation_id ON simulations(simulation_id);
CREATE INDEX IF NOT EXISTS idx_simulations_status ON simulations(status);
CREATE INDEX IF NOT EXISTS idx_simulations_created_at ON simulations(created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE simulations IS 'Stores all drone swarm simulation data including frames and statistics';
COMMENT ON COLUMN simulations.simulation_id IS 'Unique identifier for each simulation run';
COMMENT ON COLUMN simulations.config IS 'JSON configuration including algorithm, drone counts, etc';
COMMENT ON COLUMN simulations.status IS 'Current status: initializing, running, completed, failed';
COMMENT ON COLUMN simulations.statistics IS 'Final statistics: kill ratio, survival rate, etc';
COMMENT ON COLUMN simulations.frames IS 'Array of all simulation frames for replay';

-- Enable Row Level Security (RLS)
ALTER TABLE simulations ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (customize for production)
CREATE POLICY IF NOT EXISTS "Allow all operations" ON simulations
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Create analytics table for storing algorithm performance
CREATE TABLE IF NOT EXISTS algorithm_performance (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    simulation_id TEXT REFERENCES simulations(simulation_id),
    algorithm_name TEXT NOT NULL,
    avg_response_time FLOAT,
    target_accuracy FLOAT,
    formation_efficiency FLOAT,
    pso_iterations INTEGER,
    aco_pheromone_strength FLOAT,
    abc_scout_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_algorithm_performance_simulation ON algorithm_performance(simulation_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_performance_algorithm ON algorithm_performance(algorithm_name);

-- Enable RLS
ALTER TABLE algorithm_performance ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "Allow all operations on performance" ON algorithm_performance
    FOR ALL
    USING (true)
    WITH CHECK (true);
