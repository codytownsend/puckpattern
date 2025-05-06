// This file provides mock data for development and testing
// when the API is not available or for storybook development

import { ShotHeatmap } from '../store/slices/shotsSlice';

export const mockHeatmapData: ShotHeatmap = {
  points: [
    { x: 50, y: 30, value: 0.8 },
    { x: 70, y: 40, value: 0.6 },
    { x: 90, y: 45, value: 0.9 },
    { x: 110, y: 35, value: 0.7 },
    { x: 130, y: 25, value: 0.5 },
    { x: 150, y: 40, value: 0.4 },
    { x: 80, y: 50, value: 0.9 },
    { x: 100, y: 42, value: 1.0 },
    { x: 120, y: 38, value: 0.6 },
    { x: 85, y: 20, value: 0.3 },
    { x: 95, y: 30, value: 0.8 },
    { x: 105, y: 25, value: 0.7 },
    { x: 120, y: 45, value: 0.5 },
    { x: 140, y: 30, value: 0.3 },
    { x: 75, y: 35, value: 0.6 },
  ],
  max_value: 1.0,
  total_shots: 120,
  total_goals: 15,
  average_xg: 0.125,
  metadata: {
    filters: {
      team_id: null,
      player_id: null,
      season: "2024-2025",
      normalize: true
    },
    grid_size: 10
  }
};

export const mockTeams = [
  { id: '1', name: 'Toronto Maple Leafs', abbreviation: 'TOR' },
  { id: '2', name: 'Boston Bruins', abbreviation: 'BOS' },
  { id: '3', name: 'Tampa Bay Lightning', abbreviation: 'TBL' },
  { id: '4', name: 'New York Rangers', abbreviation: 'NYR' },
  { id: '5', name: 'Colorado Avalanche', abbreviation: 'COL' },
  { id: '6', name: 'Edmonton Oilers', abbreviation: 'EDM' },
  { id: '7', name: 'Vegas Golden Knights', abbreviation: 'VGK' },
  { id: '8', name: 'Florida Panthers', abbreviation: 'FLA' }
];

export const mockPlayers = [
  { id: '101', name: 'Auston Matthews', team_id: '1', position: 'C' },
  { id: '102', name: 'Mitch Marner', team_id: '1', position: 'RW' },
  { id: '103', name: 'William Nylander', team_id: '1', position: 'RW' },
  { id: '201', name: 'Patrice Bergeron', team_id: '2', position: 'C' },
  { id: '202', name: 'David Pastrnak', team_id: '2', position: 'RW' },
  { id: '203', name: 'Brad Marchand', team_id: '2', position: 'LW' },
  { id: '301', name: 'Nikita Kucherov', team_id: '3', position: 'RW' },
  { id: '302', name: 'Steven Stamkos', team_id: '3', position: 'C' },
  { id: '401', name: 'Artemi Panarin', team_id: '4', position: 'LW' },
  { id: '402', name: 'Mika Zibanejad', team_id: '4', position: 'C' },
  { id: '501', name: 'Nathan MacKinnon', team_id: '5', position: 'C' },
  { id: '502', name: 'Mikko Rantanen', team_id: '5', position: 'RW' },
  { id: '601', name: 'Connor McDavid', team_id: '6', position: 'C' },
  { id: '602', name: 'Leon Draisaitl', team_id: '6', position: 'C' },
  { id: '701', name: 'Jack Eichel', team_id: '7', position: 'C' },
  { id: '801', name: 'Aleksander Barkov', team_id: '8', position: 'C' },
];

export const mockTeamComparison = {
  team1: {
    id: '1',
    name: 'Toronto Maple Leafs',
    shots: 820,
    goals: 95,
    xg: 85.4,
    avg_xg_per_shot: 0.104,
    zone_distribution: {
      "slot": 0.42,
      "point": 0.15,
      "left_circle": 0.18,
      "right_circle": 0.16,
      "other": 0.09
    },
    shot_type_distribution: {
      "Wrist Shot": 0.55,
      "Slap Shot": 0.18,
      "Snap Shot": 0.12,
      "Backhand": 0.08,
      "Tip-In": 0.04,
      "Deflection": 0.03
    }
  },
  team2: {
    id: '2',
    name: 'Boston Bruins',
    shots: 780,
    goals: 88,
    xg: 80.6,
    avg_xg_per_shot: 0.103,
    zone_distribution: {
      "slot": 0.38,
      "point": 0.17,
      "left_circle": 0.19,
      "right_circle": 0.17,
      "other": 0.09
    },
    shot_type_distribution: {
      "Wrist Shot": 0.52,
      "Slap Shot": 0.20,
      "Snap Shot": 0.14,
      "Backhand": 0.06,
      "Tip-In": 0.05,
      "Deflection": 0.03
    }
  },
  comparison: {
    shot_volume_diff: 40,
    goal_diff: 7,
    xg_diff: 4.8,
    avg_xg_diff: 0.001,
    zone_diff: {
      "slot": 0.04,
      "point": -0.02,
      "left_circle": -0.01,
      "right_circle": -0.01,
      "other": 0.00
    },
    shot_type_diff: {
      "Wrist Shot": 0.03,
      "Slap Shot": -0.02,
      "Snap Shot": -0.02,
      "Backhand": 0.02,
      "Tip-In": -0.01,
      "Deflection": 0.00
    }
  }
};

export const mockXGBreakdown = {
  player_id: "101",
  player_name: "Auston Matthews",
  season: "2024-2025",
  total_shots: 245,
  total_xg: 32.5,
  actual_goals: 38,
  xg_per_shot: 0.133,
  shot_types: {
    "Wrist Shot": {
      "count": 158,
      "xg": 22.8,
      "goals": 28
    },
    "Slap Shot": {
      "count": 32,
      "xg": 3.5,
      "goals": 4
    },
    "Snap Shot": {
      "count": 29,
      "xg": 3.2,
      "goals": 3
    },
    "Backhand": {
      "count": 18,
      "xg": 1.8,
      "goals": 2
    },
    "Tip-In": {
      "count": 5,
      "xg": 0.7,
      "goals": 1
    },
    "Deflection": {
      "count": 3,
      "xg": 0.5,
      "goals": 0
    }
  },
  shot_zones: {
    "slot": {
      "count": 110,
      "xg": 18.5,
      "goals": 24
    },
    "point": {
      "count": 35,
      "xg": 2.8,
      "goals": 3
    },
    "left_circle": {
      "count": 42,
      "xg": 4.8,
      "goals": 5
    },
    "right_circle": {
      "count": 45,
      "xg": 5.2,
      "goals": 6
    },
    "other": {
      "count": 13,
      "xg": 1.2,
      "goals": 0
    }
  },
  xg_by_period: {
    "1": {
      "count": 82,
      "xg": 10.8,
      "goals": 12
    },
    "2": {
      "count": 75,
      "xg": 9.6,
      "goals": 11
    },
    "3": {
      "count": 88,
      "xg": 12.1,
      "goals": 15
    }
  }
};

export const mockPlayerDangerousZones = {
  player_id: "101",
  player_name: "Auston Matthews",
  season: "2024-2025",
  total_shots: 245,
  zones: [
    {
      zone: "slot",
      shots: 110,
      goals: 24,
      total_xg: 18.5,
      avg_xg: 0.168,
      shooting_pct: 21.8,
      danger_score: 18.5
    },
    {
      zone: "right_circle",
      shots: 45,
      goals: 6,
      total_xg: 5.2,
      avg_xg: 0.116,
      shooting_pct: 13.3,
      danger_score: 5.22
    },
    {
      zone: "left_circle",
      shots: 42,
      goals: 5,
      total_xg: 4.8,
      avg_xg: 0.114,
      shooting_pct: 11.9,
      danger_score: 4.78
    },
    {
      zone: "point",
      shots: 35,
      goals: 3,
      total_xg: 2.8,
      avg_xg: 0.08,
      shooting_pct: 8.6,
      danger_score: 2.8
    },
    {
      zone: "net_front",
      shots: 25,
      goals: 9,
      total_xg: 6.25,
      avg_xg: 0.25,
      shooting_pct: 36.0,
      danger_score: 6.25
    }
  ]
};