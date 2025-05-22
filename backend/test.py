#!/usr/bin/env python3
"""
Proper Roster Import - handle players and rosters correctly
"""
import sys
import os
import requests
from datetime import date
import time
from sqlalchemy.exc import IntegrityError

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models import Season, Team, Player, TeamRoster

def convert_season_to_api_format(season_id):
    """Convert season like '2015-16' to '20152016'"""
    start_year, end_year = season_id.split('-')
    if len(end_year) == 2:
        if int(end_year) < 50:
            end_year = "20" + end_year
        else:
            end_year = "19" + end_year
    return start_year + end_year

def add_player_if_not_exists(db, player_data):
    """Add player to database if they don't exist. Returns True if added."""
    player_id = str(player_data.get("id", ""))
    if not player_id:
        return False
    
    # Check if player already exists
    existing_player = db.query(Player).filter(Player.player_id == player_id).first()
    if existing_player:
        return False
    
    # Create new player
    first_name = player_data.get('firstName', {}).get('default', '')
    last_name = player_data.get('lastName', {}).get('default', '')
    full_name = f"{first_name} {last_name}".strip()
    
    player = Player(
        player_id=player_id,
        name=full_name,
        position=player_data.get("positionCode", ""),
        active=True
    )
    
    try:
        db.add(player)
        db.commit()  # Commit immediately to avoid batch duplicates
        return True
    except IntegrityError:
        # Player was added by another process/transaction - ignore
        db.rollback()
        return False

def add_roster_entry_if_not_exists(db, team_id, player_id, season_id, player_data):
    """Add roster entry if it doesn't exist. Returns True if added."""
    # Check if roster entry already exists
    existing_roster = db.query(TeamRoster).filter(
        TeamRoster.team_id == team_id,
        TeamRoster.player_id == player_id,
        TeamRoster.season_id == season_id
    ).first()
    
    if existing_roster:
        return False
    
    # Create new roster entry
    roster_entry = TeamRoster(
        team_id=team_id,
        player_id=player_id,
        season_id=season_id,
        jersey_number=str(player_data.get("sweaterNumber", "")),
        position=player_data.get("positionCode", "")
    )
    
    try:
        db.add(roster_entry)
        db.commit()  # Commit immediately
        return True
    except IntegrityError:
        # Roster entry was added by another process - ignore
        db.rollback()
        return False

def import_historical_data():
    """Import historical data with proper player/roster separation"""
    print("📅 Importing Historical Data (Proper Structure)...")
    
    seasons = [
        "2015-16", "2016-17", "2017-18", "2018-19", "2019-20",
        "2020-21", "2021-22", "2022-23", "2023-24", "2024-25"
    ]
    
    db = SessionLocal()
    try:
        # Create all seasons first
        for season_id in seasons:
            if not db.query(Season).filter(Season.season_id == season_id).first():
                start_year = int(season_id.split('-')[0])
                season = Season(
                    season_id=season_id,
                    start_date=date(start_year, 10, 1),
                    end_date=date(start_year + 1, 6, 30),
                    is_current=(season_id == "2024-25")
                )
                db.add(season)
        db.commit()
        print(f"✅ Created {len(seasons)} seasons")
        
        # Get teams
        teams = db.query(Team).order_by(Team.abbreviation).all()
        print(f"📋 Processing {len(teams)} teams...\n")
        
        grand_total_players = 0
        grand_total_roster = 0
        
        for team_idx, team in enumerate(teams, 1):
            print(f"[{team_idx:2d}/{len(teams)}] {team.abbreviation}:")
            
            team_total_players = 0
            team_total_roster = 0
            
            for season_id in seasons:
                api_season = convert_season_to_api_format(season_id)
                url = f"https://api-web.nhle.com/v1/roster/{team.abbreviation}/{api_season}"
                
                print(f"  {season_id}: ", end="")
                
                try:
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 404:
                        print("404")
                        continue
                    elif response.status_code != 200:
                        print(f"Error {response.status_code}")
                        continue
                    
                    data = response.json()
                    forwards = data.get("forwards", [])
                    defensemen = data.get("defensemen", [])
                    goalies = data.get("goalies", [])
                    
                    total_api_players = len(forwards) + len(defensemen) + len(goalies)
                    print(f"{total_api_players} players -> ", end="")
                    
                    season_players = 0
                    season_roster = 0
                    
                    # Process ALL player groups
                    for position_group in ["forwards", "defensemen", "goalies"]:
                        players = data.get(position_group, [])
                        
                        for player_data in players:
                            player_id = str(player_data.get("id", ""))
                            if not player_id:
                                continue
                            
                            # Add player if doesn't exist (commits immediately)
                            if add_player_if_not_exists(db, player_data):
                                season_players += 1
                            
                            # Add roster entry if doesn't exist (commits immediately)
                            if add_roster_entry_if_not_exists(db, team.team_id, player_id, season_id, player_data):
                                season_roster += 1
                    
                    print(f"+{season_players}p, +{season_roster}r")
                    team_total_players += season_players
                    team_total_roster += season_roster
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"ERROR: {e}")
                    continue
            
            print(f"  ✅ Team Total: {team_total_players}p, {team_total_roster}r")
            grand_total_players += team_total_players
            grand_total_roster += team_total_roster
        
        # Final statistics
        final_players = db.query(Player).count()
        final_roster_entries = db.query(TeamRoster).count()
        
        print(f"\n🎉 COMPLETE!")
        print(f"   Added this run: {grand_total_players} players, {grand_total_roster} roster entries")
        print(f"   Database totals: {final_players} players, {final_roster_entries} roster entries")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if import_historical_data():
        print("🚀 Step 4 COMPLETE")
    else:
        print("🛑 Step 4 FAILED")