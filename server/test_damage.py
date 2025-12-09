"""
Test script to verify damage and loss tracking functionality
"""
from simulation import SuperSimulation
import json

def test_damage_tracking():
    print("=" * 60)
    print("Testing Damage and Loss Tracking System")
    print("=" * 60)
    
    # Create a simple test scenario
    config = {
        'swarm_algorithm': 'cbba-superiority',
        'friendly_count': 10,
        'enemy_count': 5,
        'ground_attack_ratio': 0.4,
        'max_time': 30.0,
        'max_speed': 70.0,
        'weapon_range': 150.0,
        'detection_range': 1500.0,
        'assets': [{'position': [0, 0, 0], 'value': 1.0}]
    }
    
    print("\nInitializing simulation...")
    sim = SuperSimulation(config)
    sim.initialize_scenario()
    
    print(f"Friendlies: {len(sim.friendlies)}")
    print(f"Enemies: {len(sim.enemies)}")
    print(f"Assets: {len(sim.assets)}")
    
    # Run simulation for a few steps
    print("\nRunning simulation...")
    step_count = 0
    max_steps = 500
    
    while not sim.is_complete() and step_count < max_steps:
        sim.step(record=True)
        step_count += 1
        
        if step_count % 100 == 0:
            print(f"Step {step_count}: Time={sim.time:.2f}s")
    
    print(f"\nSimulation completed in {sim.time:.2f}s ({step_count} steps)")
    
    # Get statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    stats = sim.get_statistics()
    
    print(f"\nBasic Stats:")
    print(f"  Duration: {stats['duration']:.2f}s")
    print(f"  Friendly Losses: {stats['friendly_losses']}/{len(sim.friendlies)}")
    print(f"  Enemy Losses: {stats['enemy_losses']}/{len(sim.enemies)}")
    print(f"  Survival Rate: {stats['survival_rate']*100:.1f}%")
    print(f"  Kill Ratio: {stats['kill_ratio']:.2f}")
    
    print(f"\nAsset Stats:")
    print(f"  Assets Protected: {stats['assets_protected']}/{len(sim.assets)}")
    print(f"  Assets Destroyed: {stats['assets_destroyed']}")
    print(f"  Assets Damaged: {stats['assets_damaged']}")
    print(f"  Total Asset Damage: {stats['total_asset_damage']:.1f}")
    
    print(f"\nDamage Stats:")
    print(f"  Friendly Damage Dealt: {stats['friendly_damage_dealt']:.1f}")
    print(f"  Friendly Damage Taken: {stats['friendly_damage_taken']:.1f}")
    print(f"  Enemy Damage Dealt: {stats['enemy_damage_dealt']:.1f}")
    print(f"  Enemy Damage Taken: {stats['enemy_damage_taken']:.1f}")
    print(f"  Damage Efficiency: {stats['damage_efficiency']:.2f}")
    
    print(f"\nKill Stats:")
    print(f"  Friendly Kills: {stats['friendly_kills']}")
    print(f"  Enemy Kills: {stats['enemy_kills']}")
    
    if stats['top_killer']:
        print(f"\nTop Killer:")
        print(f"  Drone ID: {stats['top_killer']['id']}")
        print(f"  Kills: {stats['top_killer']['kills']}")
        print(f"  Damage Dealt: {stats['top_killer']['damage_dealt']:.1f}")
    
    if stats['top_damage_dealer']:
        print(f"\nTop Damage Dealer:")
        print(f"  Drone ID: {stats['top_damage_dealer']['id']}")
        print(f"  Damage Dealt: {stats['top_damage_dealer']['damage_dealt']:.1f}")
        print(f"  Kills: {stats['top_damage_dealer']['kills']}")
    
    print(f"\nCasualty Breakdown:")
    print(f"  Weapon Casualties: {stats['weapon_casualties']}")
    print(f"  Collision Casualties: {stats['collision_casualties']}")
    
    print(f"\nCombat Events:")
    print(f"  Total Combat Events: {stats['total_combat_events']}")
    print(f"  Total Collision Events: {stats['total_collision_events']}")
    
    print(f"\nMission Success: {'✓ YES' if stats['mission_success'] else '✗ NO'}")
    
    # Get detailed damage report
    print("\n" + "=" * 60)
    print("DETAILED DAMAGE REPORT")
    print("=" * 60)
    
    damage_report = sim.get_damage_report()
    
    print(f"\nFriendly Casualties: {len(damage_report['friendly_casualties'])}")
    for casualty in damage_report['friendly_casualties'][:3]:  # Show first 3
        print(f"  Drone {casualty['id']}:")
        print(f"    Damage Taken: {casualty['damage_taken']:.1f}")
        print(f"    Damage Dealt: {casualty['damage_dealt']:.1f}")
        print(f"    Kills: {casualty['kills']}")
        print(f"    Destroyed By: {casualty['destroyed_by']}")
        print(f"    Destruction Time: {casualty['destruction_time']:.2f}s" if casualty['destruction_time'] else "")
        print(f"    Damage Events: {len(casualty['damage_history'])}")
    
    print(f"\nEnemy Casualties: {len(damage_report['enemy_casualties'])}")
    for casualty in damage_report['enemy_casualties'][:3]:  # Show first 3
        print(f"  Drone {casualty['id']} ({casualty['type']}):")
        print(f"    Damage Taken: {casualty['damage_taken']:.1f}")
        print(f"    Destroyed By: {casualty['destroyed_by']}")
        print(f"    Destruction Time: {casualty['destruction_time']:.2f}s" if casualty['destruction_time'] else "")
    
    print(f"\nAsset Damage: {len(damage_report['asset_damage'])} assets damaged")
    for asset in damage_report['asset_damage']:
        print(f"  Asset {asset['id']}:")
        print(f"    Damage Taken: {asset['damage_taken']:.1f}")
        print(f"    Destroyed: {asset['destroyed']}")
        print(f"    Final Health: {asset['final_health']:.1f}")
        print(f"    Damage Events: {len(asset['damage_history'])}")
    
    print(f"\nSurvivors:")
    print(f"  Friendly Survivors: {len(damage_report['survivors']['friendlies'])}")
    print(f"  Enemy Survivors: {len(damage_report['survivors']['enemies'])}")
    
    # Check that damage tracking data exists in frames
    print("\n" + "=" * 60)
    print("FRAME DATA VERIFICATION")
    print("=" * 60)
    
    if sim.history:
        last_frame = sim.history[-1]
        print(f"\nLast frame time: {last_frame['time']:.2f}s")
        
        if last_frame['friendlies']:
            sample_friendly = last_frame['friendlies'][0]
            print(f"\nSample friendly drone data:")
            print(f"  Health: {sample_friendly.get('health', 'N/A')}")
            print(f"  Max Health: {sample_friendly.get('max_health', 'N/A')}")
            print(f"  Damage Taken: {sample_friendly.get('damage_taken', 'N/A')}")
            print(f"  Damage Dealt: {sample_friendly.get('damage_dealt', 'N/A')}")
            print(f"  Kills: {sample_friendly.get('kills', 'N/A')}")
        
        if last_frame['assets']:
            sample_asset = last_frame['assets'][0]
            print(f"\nSample asset data:")
            print(f"  Health: {sample_asset.get('health', 'N/A')}")
            print(f"  Max Health: {sample_asset.get('max_health', 'N/A')}")
            print(f"  Damage Taken: {sample_asset.get('damage_taken', 'N/A')}")
            print(f"  Destroyed: {sample_asset.get('destroyed', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    return sim, stats, damage_report

if __name__ == '__main__':
    try:
        sim, stats, damage_report = test_damage_tracking()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
