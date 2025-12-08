@echo off
echo ========================================
echo DRONE SWARM - CLEAN START
echo ========================================
echo.

echo [1/3] Clearing Python cache...
python clear_cache.py

echo.
echo [2/3] Verifying changes...
python -c "from simulation import SuperSimulation; s = SuperSimulation({'max_time': 10, 'swarm_algorithm': 'adaptive-shield', 'assets': []}); print('✓ Simulation module loaded with new code')"

echo.
echo [3/3] Starting server...
echo ========================================
echo SERVER RUNNING - Watch for battle logs!
echo ========================================
python app.py
