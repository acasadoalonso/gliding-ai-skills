PRAGMA application_id = 1668637560;
PRAGMA user_version = 3;

CREATE TABLE aircraft_type (id_aircraft_type INTEGER NOT NULL, category VARCHAR(16) NOT NULL, type VARCHAR(20) NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_aircraft_type));
CREATE TABLE class (id_class BIGINT NOT NULL, ref_warning BIGINT DEFAULT NULL, ref_aircraft_type INTEGER DEFAULT NULL, ref_contest BIGINT DEFAULT NULL, name VARCHAR(128) DEFAULT NULL, takeoff_altitude DOUBLE PRECISION NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_class));
CREATE TABLE class_meta (id_class_meta BIGINT NOT NULL, ref_class BIGINT DEFAULT NULL, "key" VARCHAR(255) NOT NULL, value CLOB NOT NULL, PRIMARY KEY(id_class_meta));
CREATE TABLE class_start (ref_class BIGINT NOT NULL, ref_point BIGINT NOT NULL, PRIMARY KEY(ref_class, ref_point));
CREATE TABLE contest (id_contest BIGINT NOT NULL, ref_location BIGINT DEFAULT NULL, name VARCHAR(255) NOT NULL, start_date DATE NOT NULL, end_date DATE NOT NULL, domain VARCHAR(255) DEFAULT NULL, country VARCHAR(2) NOT NULL, time_zone VARCHAR(64) NOT NULL, category VARCHAR(16) NOT NULL, live_track_type VARCHAR(16) NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_contest));
CREATE TABLE contest_file (id_contest_file BIGINT NOT NULL, ref_contest BIGINT DEFAULT NULL, ref_contest_file BIGINT DEFAULT NULL, name VARCHAR(255) NOT NULL, hash VARCHAR(48) NOT NULL, size INTEGER NOT NULL, active BOOLEAN NOT NULL, format VARCHAR(32) NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_contest_file));
CREATE TABLE contestant (id_contestant BIGINT NOT NULL, ref_class BIGINT DEFAULT NULL, version INTEGER NOT NULL, name VARCHAR(255) NOT NULL, club VARCHAR(255) DEFAULT NULL, team VARCHAR(255) DEFAULT NULL, aircraft_model VARCHAR(255) NOT NULL, contestant_number VARCHAR(8) DEFAULT NULL, aircraft_registration VARCHAR(32) DEFAULT NULL, handicap DOUBLE PRECISION DEFAULT NULL, pure_glider BOOLEAN NOT NULL, flight_recorders CLOB DEFAULT NULL, tag VARCHAR(255) DEFAULT NULL, not_competing BOOLEAN NOT NULL, status VARCHAR(19) DEFAULT NULL, sponsors CLOB DEFAULT NULL, cloud_id CLOB DEFAULT NULL, live_track_id VARCHAR(32) DEFAULT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_contestant));
CREATE TABLE contestant2category (ref_contestant BIGINT NOT NULL, ref_contestant_category BIGINT NOT NULL, PRIMARY KEY(ref_contestant, ref_contestant_category));
CREATE TABLE contestant_category (id_contestant_category BIGINT NOT NULL, ref_contest BIGINT DEFAULT NULL, name VARCHAR(255) NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_contestant_category));
CREATE TABLE leg (id_leg BIGINT NOT NULL, ref_result BIGINT DEFAULT NULL, leg_index INTEGER NOT NULL, start DATETIME NOT NULL, finish DATETIME NOT NULL, course DOUBLE PRECISION NOT NULL, distance DOUBLE PRECISION NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_leg));
CREATE TABLE leg_timeout (id_leg_timeout BIGINT NOT NULL, ref_result BIGINT DEFAULT NULL, leg_index INTEGER NOT NULL, start DATETIME NOT NULL, finish DATETIME NOT NULL, course DOUBLE PRECISION NOT NULL, distance DOUBLE PRECISION NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_leg_timeout));
CREATE TABLE location (id_location BIGINT NOT NULL, country VARCHAR(2) NOT NULL, continent VARCHAR(2) NOT NULL, state VARCHAR(8) DEFAULT NULL, code VARCHAR(4) DEFAULT NULL, name VARCHAR(255) NOT NULL, time_zone VARCHAR(64) NOT NULL, latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL, altitude DOUBLE PRECISION NOT NULL, runway_direction INTEGER DEFAULT NULL, runway_length INTEGER DEFAULT NULL, runway_width INTEGER DEFAULT NULL, frequency DOUBLE PRECISION DEFAULT NULL, runway_type VARCHAR(16) DEFAULT NULL, description CLOB DEFAULT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_location));
CREATE TABLE pilot (id_pilot BIGINT NOT NULL, ref_contestant BIGINT DEFAULT NULL, version INTEGER NOT NULL, first_name VARCHAR(255) NOT NULL, last_name VARCHAR(255) NOT NULL, birth_date DATETIME DEFAULT NULL, email VARCHAR(255) DEFAULT NULL, nationality VARCHAR(2) DEFAULT NULL, civl_id INTEGER DEFAULT NULL, igc_id INTEGER DEFAULT NULL, phone VARCHAR(64) DEFAULT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_pilot));
CREATE TABLE point (id_point BIGINT NOT NULL, name VARCHAR(255) NOT NULL, latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL, type VARCHAR(16) NOT NULL, elevation DOUBLE PRECISION NOT NULL, distance DOUBLE PRECISION NOT NULL, course_in DOUBLE PRECISION NOT NULL, course_out DOUBLE PRECISION NOT NULL, oz_type VARCHAR(16) NOT NULL, oz_max_altitude DOUBLE PRECISION DEFAULT NULL, oz_radius1 INTEGER NOT NULL, oz_radius2 INTEGER DEFAULT NULL, oz_angle1 DOUBLE PRECISION NOT NULL, oz_angle2 DOUBLE PRECISION DEFAULT NULL, oz_angle12 DOUBLE PRECISION DEFAULT NULL, oz_move BOOLEAN NOT NULL, oz_line BOOLEAN NOT NULL, oz_reduce BOOLEAN NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_point));
CREATE TABLE result (id_result BIGINT NOT NULL, ref_contestant BIGINT DEFAULT NULL, ref_task BIGINT DEFAULT NULL, igc_file VARCHAR(255) DEFAULT NULL, igc_hash VARCHAR(48) DEFAULT NULL, igc_public_show BOOLEAN NOT NULL, points DOUBLE PRECISION DEFAULT NULL, points_total DOUBLE PRECISION DEFAULT NULL, rank SMALLINT DEFAULT NULL, rank_total SMALLINT DEFAULT NULL, takeoff DATETIME DEFAULT NULL, soaring_begin DATETIME DEFAULT NULL, soaring_end DATETIME DEFAULT NULL, landing DATETIME DEFAULT NULL, penalty DOUBLE PRECISION DEFAULT NULL, calculated_finish DATETIME DEFAULT NULL, calculated_distance DOUBLE PRECISION DEFAULT NULL, calculated_speed DOUBLE PRECISION DEFAULT NULL, calculated_start DATETIME DEFAULT NULL, timeout_finish DATETIME DEFAULT NULL, timeout_distance DOUBLE PRECISION DEFAULT NULL, timeout_speed DOUBLE PRECISION DEFAULT NULL, timeout_start DATETIME DEFAULT NULL, scored_finish DATETIME DEFAULT NULL, scored_distance DOUBLE PRECISION DEFAULT NULL, scored_speed DOUBLE PRECISION DEFAULT NULL, scored_start DATETIME DEFAULT NULL, status_evaluated BOOLEAN NOT NULL, status_airspace_violation BOOLEAN NOT NULL, status_high_enl BOOLEAN NOT NULL, status_manual BOOLEAN NOT NULL, status_turnpoint_missed BOOLEAN NOT NULL, status_fixed_points BOOLEAN NOT NULL, w_integrity VARCHAR(16) DEFAULT NULL, w_high_enl BOOLEAN NOT NULL, w_no_enl BOOLEAN NOT NULL, w_gps_fix_rate BOOLEAN NOT NULL, w_max_altitude BOOLEAN NOT NULL, w_finish_altitude BOOLEAN NOT NULL, w_finish_altitude_value DOUBLE PRECISION DEFAULT NULL, w_start_altitude BOOLEAN NOT NULL, w_start_altitude_value DOUBLE PRECISION DEFAULT NULL, w_max_ground_speed BOOLEAN NOT NULL, w_max_ground_speed_value DOUBLE PRECISION DEFAULT NULL, w_altitude_timeout BOOLEAN NOT NULL, w_takeoff_altitude BOOLEAN NOT NULL, w_altitude_correction DOUBLE PRECISION DEFAULT NULL, w_waypoint CLOB DEFAULT NULL, w_airspace CLOB DEFAULT NULL, w_user CLOB DEFAULT NULL, comment CLOB DEFAULT NULL, tag VARCHAR(255) DEFAULT NULL, ext_params CLOB DEFAULT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_result));
CREATE TABLE result_start (ref_result BIGINT NOT NULL, ref_task_point BIGINT NOT NULL, PRIMARY KEY(ref_result, ref_task_point));
CREATE TABLE script (id_script BIGINT NOT NULL, ref_class BIGINT DEFAULT NULL, name VARCHAR(255) NOT NULL, category VARCHAR(16) NOT NULL, content CLOB NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_script));
CREATE TABLE task (id_task BIGINT NOT NULL, ref_warning BIGINT DEFAULT NULL, ref_class BIGINT DEFAULT NULL, ref_script BIGINT DEFAULT NULL, task_date DATE NOT NULL, task_number SMALLINT NOT NULL, result_status VARCHAR(16) NOT NULL, takeoff_altitude DOUBLE PRECISION NOT NULL, qnh DOUBLE PRECISION DEFAULT NULL, notes CLOB DEFAULT NULL, info CLOB DEFAULT NULL, footnote VARCHAR(255) DEFAULT NULL, tag VARCHAR(255) DEFAULT NULL, task_type VARCHAR(17) NOT NULL, task_value INTEGER DEFAULT NULL, task_name VARCHAR(255) DEFAULT NULL, task_distance DOUBLE PRECISION DEFAULT NULL, task_distance_min DOUBLE PRECISION DEFAULT NULL, task_distance_max DOUBLE PRECISION DEFAULT NULL, task_duration INTEGER DEFAULT NULL, no_start DATETIME DEFAULT NULL, start_on_entry BOOLEAN NOT NULL, distance_calculation VARCHAR(16) NOT NULL, uncompleted_calculation VARCHAR(16) NOT NULL, distance_tolerance DOUBLE PRECISION NOT NULL, altitude_tolerance DOUBLE PRECISION NOT NULL, min_altitude DOUBLE PRECISION NOT NULL, multiple_starts BOOLEAN NOT NULL, random_waypoints BOOLEAN DEFAULT NULL, max_points INTEGER DEFAULT NULL, start_points INTEGER DEFAULT NULL, end_points INTEGER DEFAULT NULL, bonus DOUBLE PRECISION DEFAULT NULL, excluded_airspaces CLOB DEFAULT NULL, task_version INTEGER NOT NULL, start_time_interval INTEGER DEFAULT NULL, start_time_interval_count INTEGER DEFAULT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_task));
CREATE TABLE task_changelog (id_task_changelog BIGINT NOT NULL, ref_task BIGINT DEFAULT NULL, version INTEGER NOT NULL, notes CLOB NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_task_changelog));
CREATE TABLE task_image (id_task_image BIGINT NOT NULL, ref_task BIGINT DEFAULT NULL, name VARCHAR(255) NOT NULL, hash VARCHAR(48) NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_task_image));
CREATE TABLE task_point (id_task_point BIGINT NOT NULL, ref_task BIGINT DEFAULT NULL, ref_point BIGINT DEFAULT NULL, point_index SMALLINT NOT NULL, multiple_start BOOLEAN NOT NULL, PRIMARY KEY(id_task_point));
CREATE TABLE warning (id_warning BIGINT NOT NULL, airspace_violation BOOLEAN NOT NULL, failed_validation BOOLEAN NOT NULL, high_enl INTEGER NOT NULL, max_altitude DOUBLE PRECISION NOT NULL, min_finish_altitude DOUBLE PRECISION NOT NULL, max_finish_altitude DOUBLE PRECISION NOT NULL, altitude_timeout INTEGER NOT NULL, start_altitude DOUBLE PRECISION NOT NULL, start_ground_speed DOUBLE PRECISION NOT NULL, gps_fix_rate INTEGER NOT NULL, altitude_correction DOUBLE PRECISION NOT NULL, created_at DATETIME DEFAULT NULL, updated_at DATETIME DEFAULT NULL, PRIMARY KEY(id_warning));

INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (1, 'any', 'unknown', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (2, 'glider', 'world', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (3, 'glider', 'club', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (4, 'glider', 'standard', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (5, 'glider', '13_5_meter', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (6, 'glider', '15_meter', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (7, 'glider', '18_meter', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (8, 'glider', 'double_seater', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (9, 'glider', 'open', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (10, 'hang_glider', 'hang_glider_flexible', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (11, 'hang_glider', 'hang_glider_rigid', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (12, 'paraglider', 'paraglider', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (13, 'paraglider', 'paraglider_open', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (14, 'paraglider', 'paraglider_sport', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO aircraft_type (id_aircraft_type, category, type, created_at, updated_at) VALUES (15, 'paraglider', 'paraglider_tandem', '2015-05-21 05:17:01', '2015-05-21 05:17:01');
INSERT INTO script (id_script, ref_class, name, category, content, created_at, updated_at) VALUES (2, NULL, 'Sailplane_Grand_Prix (default)', 'glider', 'Program Sailplane_Grand_Prix;
// v1.00 = Initial release by Philippe de Pechy
// v2.00 = June 12, 2006 by Andrej Kolar
//       Corrected:
//       . Removed all references to time scoring
//       . SFinish := -1; by default which prevents printing of finsih times for nonfinishers
//       . SStart := -1; by default which prevents printing of start times for nonstarters
//       . Solved problem with unscored pilots
//       Known issues:
//       . HC functionality not supported
// v3.00 = May 9, 2010 by Wojciech Scigala
//       Changes:
//       . False start penalty no longer calculated automatically, but an user warning is generated
//       . Task time is always calculated from Start line opening, even in case of false start (FAI rules)
//       . Penalties (in seconds) are to be entered in the performance dialog,
//           they will be deducted from marking time before ranking the pilots.
//           All times and speeds on results does not take penalties into account - only ranking and points do
//       . HC is supported, but my way to score it may be disputable
//           (it is impossible to introduce fully transparent HC pilots in GP formula)
//       . Start line time should be entered in DayTag as "Ts=14:10:00"
//         Do not use "No start before" in day properties dialog!
//       . Bonus turnpoints are supported. It should be entered in DayTag as "BP=2", meaning second _turnpoint_ of the task is chosen
//         "Need task legs..." in contest properties need to be enabled for bonus turnpoint feature to work
//       . some code cleanup
//       Known issues:
//       . Bonus point calculation might go wrong if a pilot recrosses start line!
// v4.00 = June 20, 2015 by Wojciech Scigala
//       Changes:
//       . Bonus turnpoint feature removed (as removed from GP rules)
//       . Added support for extra point for winner of last designated competition day
//         This day should be marked by word "LASTDAY" placed anywhere in the DayTag

 
const ONEDAY = 24*60*60; // One day in seconds

var

  // Day variables
  LastDay : Integer;  // if day is last designated competition day
  TsPos : Integer;  // position of Ts in DayTag

  Ts : Double; //  The Regatta Start Time of the day
  IsDayValid : Boolean; // true if the day is valid
  Nf : Integer;// Number of finishers
  R : Integer; // Pilot''s daily rank
  P : Integer; // Points according F1 rules

  // Competitor variables
  D : Double; // Competitors Marking Distance  (expressed in km)
  T : Double; //  Finishers Marking Time= Pilots[i].finish - Ts + penalty
  PenEarlyStart : Double; // penalty for starting before Ts
  RStart : Double; // the real start time
  SStart : Double; // the scoring start time
  SFinish : Double; // the scoring finish time
  SDis : Double; // the scoring distance
  SSpeed : Double; // the scoring speed

  // Others variable
  i : Integer;
  j : Integer;

Function MinValue( a,b,c : double ) : double;
var m : double;
begin
  m := a;
  If b < m Then m := b;
  If c < m Then m := c;

  MinValue := m;
end;


function GetPilotTPTime (var Pilot : TPilot; tp : integer) : double;
var    x : integer;
    time : double;
begin
  time := ONEDAY;

  // this checking loop is needed in case pilot didn''t reach TP
  for x:= low(Pilot.Leg) to high(Pilot.Leg) do
  begin
    If (x = (tp-1)) then
    begin
      If (high(Pilot.Leg) >= tp) then   // check if pilot really completed the bonus leg
        time := Pilot.Leg[x].finish;
    end;    
  end;

  Result := time;  
end;



begin
  
  // Initial setup

  LastDay := Pos(''LASTDAY'',DayTag);

  TsPos := Pos(''Ts='',DayTag);

  Ts := StrToFloat( Copy( DayTag, TsPos+3,2 ) )*3600 + StrToFloat( Copy( DayTag, TsPos+6,2 ) )*60 + StrToFloat( Copy( DayTag, TsPos+9,2 ) );
  Nf :=0;



  // Calculation of basic parameters
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    // The pilot has competed
    If not Pilots[i].isHC Then
    begin
      // compute of Nf = number of finishers
      if (Pilots[i].finish>0) then
      begin
        Nf := Nf + 1;
      end;  // end finisher 
    end  //end isHC
  end;  // end loop

  // Check if the day is valid
  IsDayValid := (Nf>=0);

  // Compute the pilot''s score
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
     // init
     SStart :=-1;
     SFinish :=-1;
     SDis := Pilots[i].dis;
     SSpeed := 0;

     T := ONEDAY;

     // Case the pilot has started
     if (Pilots[i].start>0) Then
     begin
        RStart := Pilots[i].start;	// real start time, only used to detect false start
	SStart := Ts;

        // computes the start penalty
        PenEarlyStart := Ts - RStart;
        if (PenEarlyStart>0)
        then
           Pilots[i].Warning := ''False start: '' + FloatToStr(PenEarlyStart) + ''s'';

        // Case the pilot completes the task
        if  (Pilots[i].finish>0) then
        begin
           SFinish := Pilots[i].finish;
           T := SFinish - SStart;
           SSpeed := SDis / T;  // Speed calculation not affected by penalties
           T := T + Pilots[i].penalty;
        end
        // Case the pilot lands out
        else
        begin
             T := ONEDAY;
        end  // end the pilot lands out
     end // end the pilot started
     
     // The pilot does not started
     else
     begin
       T := ONEDAY;
     end;

     if (IsDayValid) then
     begin
       Pilots[i].Points := - T;
     end
     else
     begin
       Pilots[i].Points := 0;
     end

     // other displayed data
     Pilots[i].sstart:= SStart;
     Pilots[i].sfinish:=SFinish;
     Pilots[i].sdis:=SDis;
     Pilots[i].sspeed:=SSpeed;
     Pilots[i].td2 := Pilots[i].Points;
  end; // loop  


  // Compute the pilot''s day rank and store in td1;
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    R := 1;
    for j:=0 to GetArrayLength(Pilots)-1 do
    begin   
      if ( ((Pilots[j].Points) > (Pilots[i].Points)) and (not Pilots[j].isHC))
      then
          begin
             R := R+1;
          end
       else
          begin
          end;
    end;
    Pilots[i].td1 := R;

   end; // end loop pilot''s day rank

  // Compute the pilot''s day score;
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin   
    R := Round(Pilots[i].td1);
    // the winner
    if ((R=1) and (IsDayValid))
    then 
      begin
        if (Nf<9) then P := Nf-R+2
        else           P := 10-R+1;

        if (LastDay > 0) then P := P + 1;

      end;

    // a finisher (but not the winner)
    if ((R>1) and (IsDayValid) and (Pilots[i].finish>0))
    then 
      begin
        if (Nf<9) then P := Nf-R+1
        else           P := 10-R
      end;
  
    // an outlander
    if (Pilots[i].finish<=0)
    then 
      begin
        P := 0;
      end;
  

    // check non negative score
    if (P<0) then P:=0;
        
    // Score
    if (IsDayValid) then
    begin
      Pilots[i].Points := P;
    end
    else
    begin
      Pilots[i].Points := 0;
    end;

  end; // end loop Compute the pilot''s day score;


   
  // Info fields, also presented on the Score Sheets
  If not (TsPos = 0) then
  begin
    Info1 := ''Regatta start time :  ''+Copy( DayTag, TsPos+3,8 ) ;
      If (LastDay > 0) then
      begin
        Info1 := Info1 + '', Last day bonus active'';    
      end;
  end;

end.
', '2015-05-21 05:17:01', '2019-06-21 11:21:38');
INSERT INTO script (id_script, ref_class, name, category, content, created_at, updated_at) VALUES (3, NULL, 'IGC_Annex_A_scoring_2022 (default)', 'glider', 'Program IGC_Annex_A_scoring_2022;
// Collaborate on writing scripts at Github:
// https://github.com/naviter/seeyou_competition_scripts/
//
// Version 9.02, Date 17.07.2022 by Andrej Kolar
//   . Reintroduced Hmin parameter to be able to calculate results for Handicaps between 80-130
// Version 9.01, Date 08.07.2022 by Andrej Kolar
//   . Removed reference to Hmin in all calculations to be compliant with the latest version of Annex A
// Version 9.00, Date 07.02.2022 by Lothar Dittmer
//   . support for PEV start scoring 
//   . enter "PEVWaitTime=10" in DayTag to have PEV gate opening 10 min after PEV.
//   . enter "PEVStartWindow=10" in DayTag to have 10 min long startwindows after PEV. 
//   . separate Tags with Blank '' '' (required)
//   . example: DayTag: "PEVWaitTime=10 PEVStartWindow=10" allows 3 possible start windows with length 10min starting 10 min after PEV 1,2 or 3
//   . if "AllUserWrng" in DayTag is set to 0 user warning with PEVs is only shown if penalty should be necessary otherwise PEVs are displayed
//   . buffer zone as a script parameter
//   . added start speed interpolation according to DAEC SWO 7.3.5
//   . enter "MaxStSpd=130" in DayTag to have interpolation and userwarnings if average start speed is higher than 130km/h 
// Version 8.01, Date 20.04.2021
//   . added ReadDayTagParameter() function to read any DayTag parameter
//   . parameters in DayTag now have to be separated by space (only)
//   . example: "PEVWaitTime=10 PEVStartWindow=10"
// Version 8.00, Date 26.06.2019
//   . merged all scripts into one
//   . by default UseHandicaps is in auto mode
//   . new n3 and n4 parameters (currently unused)
//   . redesigned Info fields
//   . renamed V0 to Vo
// Version 7.01
//   . D1 is set to a default value. Previously it did not work with unknown class
// Version 7.00
//   . Support for new Annex A rules for minimum distance & 1000 points allocation per class
// Version 5.02, Date 25.04.2018
//   . Bugfix in Fcr formula
// Version 5.01, Date 03.04.2018
//   . Bugfix division by zero
// Version 5.00, Date 23.03.2018
//   . Task Completion Ratio factor added according to SC03 2017 Edition valid from 1 October 2017, updated 4 January 2018
// Version 3.30, Date 10.01.2013
//   . BugFix: Td exchanged with Task.TaskTime - This fix is critical for all versions of SeeYou later than SeeYou 4.2
// Version 3.20, Date 04.07.2008
// Version 3.0
//   . Added Hmin instead of H0. Score is now calculated using minimum handicap as opposed to maximum handicap as before
// Version 3.01
//   . Changed if Pilots[i].takeoff > 0 to if Pilots[i].takeoff >= 0. It is theoretically possible that one takes off at 00:00:00 UTC
//   . Changed if Pilots[i].start > 0 to if Pilots[i].start >= 0. It is theoretically possible that one starts at 00:00:00 UTC
// Version 3.10
//   . removed line because it doesn''t exist in Annex A 2006:
// 			if Pilots[i].dis*Hmin/Pilots[i].Hcap < (2.0/3.0*D0) Then Pd := Pdm*Pilots[i].dis*Hmin/Pilots[i].Hcap/(2.0/3.0*D0);
// Version 3.20
//   . added warnings when Exit 

const UseHandicaps = 2;   // set to: 0 to disable handicapping, 1 to use handicaps, 2 is auto (handicaps only for club and multi-seat)
      PevStartTimeBuffer = 30; // PEV which is less than PevStartTimeBuffer seconds later than last PEV will be ignored and not counted
   
var
  Dm, D1,
  Dt, n1, n2, n3, n4, N, D0, Vo, T0, Hmin,
  Pm, Pdm, Pvm, Pn, F, Fcr, Day: Double;

  D, H, Dh, M, T, Dc, Pd, V, Vh, Pv, S : double;
  
  PmaxDistance, PmaxTime : double;
  
  i,j : integer;
  PevWaitTime,PEVStartWindow,AllUserWrng, PilotStartInterval, PilotStartTime, PilotPEVStartTime,StartTimeBuffer,MaxStartSpeed : Integer;
  AAT : boolean;
  Auto_Hcaps_on : boolean;
  
  // Starttime calculation and PEV Warnings
  PilotStartSpeed, PilotStartSpeedSum, PilotStartSpeedFixes : double;
  ActMarker  : TMarker; 
  PevWarning : String;
  Ignore_PEV,PEVStartNotValid : boolean;  
  Pevcount, LastPev  : Integer; 

Function MinValue( a,b,c : double ) : double;
var m : double;
begin
  m := a;
  if b < m Then m := b;
  if c < m Then m := c;

  MinValue := m;
end;

Function GetTimeString (time: integer) : string;    // converts integer time in seconds to "hh:mm:ss" string
var
  h,min,sec: Integer;
  sth,stmin,stsec:String; 
begin
  h:=Trunc(time/3600);
  min:=Trunc((time-h*3600)/60);
  sec:=time-h*3600-min*60;
  sth:=IntToStr(h);
  if Length(sth)=1 Then sth:=''0''+sth;   
  stmin:=IntToStr(min);
  if Length(stmin)=1 Then stmin:=''0''+stmin;   
  stsec:=IntToStr(sec); 
  if Length(stsec)=1 Then stsec:=''0''+stsec;    
  GetTimeString :=sth+'':''+stmin+'':''+stsec;           
end;

Function ReadDayTagParameter ( name : string; default : double ) : double;
var
  sp, tp : Integer;
  sub : string;
begin
  sp := Pos(UpperCase(name) + ''='',UpperCase(DayTag));

  if (sp > 0) then
  begin
    sub:= Copy(DayTag,sp + Length(name) + 1,Length(DayTag));

    tp := Pos('' '',sub);
    if (tp > 0) then
      sub:= Copy(sub,0,tp-1);

    tp := Pos('','',sub);
    if (tp > 0) then
      sub := Copy (sub,0,tp-1) + ''.'' + Copy (sub,tp+1,Length(sub));
    ReadDayTagParameter := StrToFloat(sub);
  end
  else
    ReadDayTagParameter := default;            // string not found
end;


begin

  // initial checks
  if GetArrayLength(Pilots) <= 1 then
    exit;

  if (UseHandicaps < 0) OR (UseHandicaps > 2) then
  begin
    Info1 := '''';
    Info2 := ''ERROR: constant UseHandicaps is set wrong'';
    exit;
  end;

  if Task.TaskTime = 0 then
    AAT := false
  else
    AAT := true;

  if (AAT = true) AND (Task.TaskTime < 1800) then
  begin
    Info1 := '''';
    Info2 := ''ERROR: Incorrect Task Time'';
    exit;
  end;


  // Minimum Distance to validate the Day, depending on the class [meters]
  Dm := 100000;
  if Task.ClassID = ''club'' Then Dm := 100000;
  if Task.ClassID = ''13_5_meter'' Then Dm := 100000;
  if Task.ClassID = ''standard'' Then Dm := 120000;
  if Task.ClassID = ''15_meter'' Then Dm := 120000;
  if Task.ClassID = ''double_seater'' Then Dm := 120000;
  if Task.ClassID = ''18_meter'' Then Dm := 140000;
  if Task.ClassID = ''open'' Then Dm := 140000;
  
  // Minimum distance for 1000 points, depending on the class [meters]
  D1 := 250000;
  if Task.ClassID = ''club'' Then D1 := 250000;
  if Task.ClassID = ''13_5_meter'' Then D1 := 250000;
  if Task.ClassID = ''standard'' Then D1 := 300000;
  if Task.ClassID = ''15_meter'' Then D1 := 300000;
  if Task.ClassID = ''double_seater'' Then D1 := 300000;
  if Task.ClassID = ''18_meter'' Then D1 := 350000;
  if Task.ClassID = ''open'' Then D1 := 350000;

  // Handicaps for club and 20m multi-seat class
  Auto_Hcaps_on := false;
  if Task.ClassID = ''club'' Then Auto_Hcaps_on := true;
  if Task.ClassID = ''double_seater'' Then Auto_Hcaps_on := true;

  // PEV Start PROCEDURE
  // Read PEV Gate Parameters from DayTag. Return zero PEVWaitTime or PEVStartWindow are unparsable or missing
  
  StartTimeBuffer:=30; // Start time buffer zone. if one starts 30 seconds too early he is scored by his actual start time
  PEVWaitTime := Trunc(ReadDayTagParameter(''PEVWAITTIME'',0)) * 60;	// WaitTime in seconds 
  PEVStartWindow := Trunc(ReadDayTagParameter(''PEVSTARTWINDOW'',0))* 60; // StartWindow open in seconds
  MaxStartSpeed := Trunc(ReadDayTagParameter(''MAXSTSPD'',0));		// Startspeed interpolation done if MaxStartSpeed (in km/h) >0
  AllUserWrng := Trunc(ReadDayTagParameter(''ALLUSERWRNG'',1));		// Output of All UserWarnings with PEVs: ON=1(for debugging and testing) OFF=0  

  // if DayTag variables PEVWaitTime and PEVStartWindow are set (>0) then PEV Marker Start Warnings are shown 
  if (PEVWaitTime > 0) and (PEVStartWindow> 0) then																					// Only display number of intervals if it is not zero
    begin
    Info3 :=''PEVWaitTime: ''+IntToStr(PevWaitTime div 60)+''min, PEVStartWindow: ''+IntToStr(PevStartWindow div 60)+''min, '';
    end
  else 
    begin
    Info3:=''PEVStarts: OFF, '';
    PEVWaitTime:=0;
    PEVStartWindow:=0;
    end;  

  // Calculation of basic parameters
  N := 0;  // Number of pilots having had a competition launch
  n1 := 0;  // Number of pilots with Marking distance greater than Dm - normally 100km
  n4 := 0;  // Number of competitors who achieve a Handicapped Distance (Dh) of at least Dm/2
  Hmin := 100000;  // Lowest Handicap of all competitors in the class
  
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    if UseHandicaps = 0 Then Pilots[i].Hcap := 1;
    if (UseHandicaps = 2) and (Auto_Hcaps_on = false) Then Pilots[i].Hcap := 1;

    if not Pilots[i].isHC Then
    begin
      if Pilots[i].Hcap < Hmin Then Hmin := Pilots[i].Hcap; // Lowest Handicap of all competitors in the class
    end;
  end;
  
  // Annex A version 2022 has removed the capability of Hmin in the results. Simply removing Hmin doesn''t work for comps where Handicaps are given as 108, 125 etc. Hence this addition.
  if Hmin >= 500 then Hmin = 1000;                   // Not sure if there are any comps that uses Annex A rules with Handicaps over 10000?
  if (Hmin >= 50) and (Hmin < 500) then Hmin := 100; // For comps that use Handicaps typically between 70 and 130
  if (Hmin >= 5) and (Hmin < 50) then Hmin := 10;    // Just in case
  if (Hmin >= 0.5) and (Hmin < 5) then Hmin := 1;    // Typical IGC Annex A comps with handicaps around 1.000
  if (Hmin >= 0) and (Hmin < 0.5) then Hmin := Hmin; // Just in case

  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    if not Pilots[i].isHC Then
    begin
      if Pilots[i].dis*Hmin/Pilots[i].Hcap >= Dm Then n1 := n1+1;  // Competitors who have achieved at least Dm
      if Pilots[i].dis*Hmin/Pilots[i].Hcap >= ( Dm / 2.0) Then n4 := n4+1;  // Number of competitors who achieve a Handicapped Distance (Dh) of at least Dm/2
      if Pilots[i].takeoff >= 0 Then N := N+1;    // Number of competitors in the class having had a competition launch that Day
    end;
  end;
  if N=0 Then begin
          Info1 := '''';
	  Info2 := ''Warning: Number of competition pilots launched is zero'';
  	Exit;
  end;
  
  D0 := 0;
  T0 := 0;
  Vo := 0;
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    if not Pilots[i].isHC Then
    begin
      // Find the highest Corrected distance
      if Pilots[i].dis*Hmin/Pilots[i].Hcap > D0 Then D0 := Pilots[i].dis*Hmin/Pilots[i].Hcap;
      
      // Find the highest finisher''s speed of the day
      // and corresponding Task Time
      if Pilots[i].speed*Hmin/Pilots[i].Hcap = Vo Then // in case of a tie, lowest Task Time applies
      begin
        if (Pilots[i].finish-Pilots[i].start) < T0 Then
        begin
          Vo := Pilots[i].speed*Hmin/Pilots[i].Hcap;
          T0 := Pilots[i].finish-Pilots[i].start;
        end;
      end
      else
      begin
        if Pilots[i].speed*Hmin/Pilots[i].Hcap > Vo Then
        begin
          Vo := Pilots[i].speed*Hmin/Pilots[i].Hcap;
          T0 := Pilots[i].finish-Pilots[i].start;
          if (AAT = true) and (T0 < Task.TaskTime) Then       // if marking time is shorter than Task time, Task time must be used for computations
            T0 := Task.TaskTime;
        end;
      end;
    end;
  end;

  if D0=0 Then begin
	  Info1 := '''';
          Info2 := ''Warning: Longest handicapped distance is zero'';
  	Exit;
  end;
  
  // Maximum available points for the Day
  PmaxDistance := 1250 * (D0/D1) - 250;
  PmaxTime := (400*T0/3600.0)-200;
  if T0 <= 0 Then PmaxTime := 1000;
  Pm := MinValue( PmaxDistance, PmaxTime, 1000.0 );
  
  // Day Factor
  F := 1.25* n1/N;
  if F>1 Then F := 1;
  
  // Number of competitors who have achieved at least 2/3 of best speed for the day Vo
  n2 := 0;
  // Number of finishers, regardless of speed
  n3 := 0;

  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    if not Pilots[i].isHC Then
    begin
      n3 := n3+1;
      if Pilots[i].speed*Hmin/Pilots[i].Hcap > (2.0/3.0*Vo) Then
      begin
        n2 := n2+1;
      end;
    end;
  end;
  
  // Completion Ratio Factor
  Fcr := 1;
  if n1 > 0 then
    Fcr := 1.2*(n2/n1)+0.6;
  if Fcr>1 Then Fcr := 1;

  Pvm := 2.0/3.0 * (n2/N) * Pm;  // maximum available Speed Points for the Day
  Pdm := Pm-Pvm;                 // maximum available Distance Points for the Day
  
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    // For any finisher
    if Pilots[i].finish > 0 Then
    begin
      Pv := Pvm * (Pilots[i].speed*Hmin/Pilots[i].Hcap - 2.0/3.0*Vo)/(1.0/3.0*Vo);
      if Pilots[i].speed*Hmin/Pilots[i].Hcap < (2.0/3.0*Vo) Then Pv := 0;
      Pd := Pdm;
    end
    else
    //For any non-finisher
    begin
      Pv := 0;
      Pd := Pdm * (Pilots[i].dis*Hmin/Pilots[i].Hcap/D0);
    end;
    
    // Pilot''s score
    Pilots[i].Points := Round( F*Fcr*(Pd+Pv) - Pilots[i].Penalty );
  end;
  
  // Data which is presented in the score-sheets
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    Pilots[i].sstart:=Pilots[i].start;
    Pilots[i].sfinish:=Pilots[i].finish;
    Pilots[i].sdis:=Pilots[i].dis;
    Pilots[i].sspeed:=Pilots[i].speed;
  end;
  
  // Info fields, also presented on the Score Sheets
  if AAT = true Then
    Info1 := ''Assigned Area Task, ''
  else
    Info1 := ''Racing Task, '';

  Info1 := Info1 + ''Maximum Points: ''+IntToStr(Round(Pm));
  Info1 := Info1 + '', F = ''+FormatFloat(''0.000'',F);
  Info1 := Info1 + '', Fcr = ''+FormatFloat(''0.000'',Fcr);
  Info1 := Info1 + '', Max speed pts: ''+IntToStr(Round(Pvm));

  if (n1/N) <= 0.25 then
    Info1 := ''Day not valid - rule 8.2.1b'';

  Info2 := ''Dm = '' + IntToStr(Round(Dm/1000.0)) + ''km'';
  Info2 := Info2 + '', D1 = '' + IntToStr(Round(D1/1000.0)) + ''km'';
  if (UseHandicaps = 0) or ((UseHandicaps = 2) and (Auto_Hcaps_on = false)) Then
    Info2 := Info2 + '', no handicaps''
  else
    Info2 := Info2 + '', handicapping enabled'';

  // for debugging:
  Info3 := Info3 +'' N: '' + IntToStr(Round(N));
  Info3 := Info3 + '', n1: '' + IntToStr(Round(n1));
  Info3 := Info3 + '', n2: '' + IntToStr(Round(n2));
  Info3 := Info3 + '', Do: '' + FormatFloat(''0.00'',D0/1000.0) + ''km'';
  Info3 := Info3 + '', Vo: '' + FormatFloat(''0.00'',Vo*3.6) + ''km/h'';
  
// Give out PEV as Warnings
// PevStartTimeBuffer is set to 30

  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    Pilots[i].Warning := ''''; 
    if (Pilots[i].start > 0) Then
    begin	
      if (PEVWaitTime>0) and (PEVStartWindow>0) then   
      begin
        PevWarning:='''';
        PevCount:=0; LastPev:=0;
        Ignore_PEV:=false;

        for j:=0 to GetArrayLength(Pilots[i].Markers)-1 do
        begin
          Ignore_Pev:= ((Pilots[i].Markers[j].Tsec-LastPev<=PevStartTimeBuffer) and (Lastpev>0)) or (Pevcount=3); // TODO: Also ignore PEV if PEV time is greater than start time.
          if Ignore_Pev Then
             begin
               if (ALLUserWrng>=1)Then PevWarning := PevWarning + '' (PEV ignored=''+ GetTimestring(Pilots[i].Markers[j].Tsec) +''!), ''
             end
          else
             begin
               PevCount:=PevCount+1;
               LastPev:= Pilots[i].Markers[j].Tsec;
               if (AllUserWrng>=1) Then PevWarning := PevWarning + ''PEV''+IntTostr(Pevcount)+''=''+ GetTimestring(Pilots[i].Markers[j].Tsec)+'', '';
             end;
        end;
        
        if PEVCount>0 Then 
        begin
          PevStartNotValid:=(Trunc(Pilots[i].Start)<(LastPEV+PEVWaitTime)) or (Trunc(Pilots[i].Start)>(LastPEV+PEVWaitTime+PEVStartWindow));
          if PevStartNotValid Then
            PEVWarning:=PevWarning+'' Start=''+GetTimestring(Trunc(Pilots[i].Start))+'' PEVGate not open!''+'', '' 
          else
            if (Pilots[i].start>=Task.NoStartBeforeTime) and (AllUserWrng>=1) Then
              PEVWarning:=PevWarning+'' Start=''+GetTimestring(Trunc(Pilots[i].Start))+'' OK''+'', ''; 
          Pilots[i].Warning:= PevWarning;
        end
        else
           PEVWarning:=''PEV not found!''+'', '';

        Pilots[i].Warning:= PevWarning;   
      end;
      if Pilots[i].start<Task.NoStartBeforeTime then Pilots[i].Warning :=Pilots[i].Warning+'' Start=''+GetTimestring(Trunc(Pilots[i].start))+'' before gate opens!''+'', '';     
    end;
  end;
 
// +/- 10 sec start speed interpolation if variable MaxStartSpeed is set by daytag "MaxStSpd= " to values >0
  if MaxStartSpeed>0 Then 
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    PilotStartSpeed := 0;
	PilotStartSpeedSum := 0;
	PilotStartSpeedFixes := 0;	
	if (Pilots[i].start > 0) Then
	begin
	  for j := 0 to GetArrayLength(Pilots[i].Fixes)-1 do
	  begin
	    if (Pilots[i].Fixes[j].Tsec >= Pilots[i].start-9) and (Pilots[i].Fixes[j].Tsec <= Pilots[i].start+10) Then
		begin
		  PilotStartSpeedSum := PilotStartSpeedSum + Pilots[i].Fixes[j].Gsp;
		  PilotStartSpeedFixes := PilotStartSpeedFixes + 1;
	    end;
	  end;

      if PilotStartSpeedfixes>0 then 
	    PilotStartSpeed := PilotStartSpeedSum / PilotStartSpeedFixes;
      if (Round(PilotStartSpeed*3.6) > MaxStartSpeed) Then
	    Pilots[i].Warning := Pilots[i].Warning+ '' Startspeed='' + FloatToStr(Round(PilotStartSpeed*3.6)) + '' km/h-> '' + FloatToStr(Round(PilotStartSpeed*3.6)- MaxStartSpeed) + '' km/h too fast'' ;
    end;
  end;
end.
', '2015-05-21 05:17:01', '2019-06-21 11:21:55');
INSERT INTO script (id_script, ref_class, name, category, content, created_at, updated_at) VALUES (1, NULL, 'FFVP_2023 (default)', 'glider', 'Program FFVP_2023;

const FFVPScript=''FFVP Script 2023-100''; // Version du script

// https://www.ffvp.fr/kb/organiser-une-competition/
// commission.sport@ffvp.fr
//
// - Testé avec SeeYou 10 :
// http://www.naviter.com
//
// - Support
// Ecrivez à commission.sport@ffvp.fr en ayant préalablement attribuer les droits admin dans SoaringSpot
//
// - Réglements de référence : Note Permanente FFVV 4.1 Edition 2023 publiée en février 2023
// A LIRE IMPERATIVEMENT : le guide de l''organisateur FFVP disponible sur :
// https://www.ffvp.fr/kb/organiser-une-competition/ 
// 
// - Documentation de SeeYou :
// https://www.naviter.com/products/seeyou-competition/ 
// 
// - Utilisation du kit
// Importer le fichier dans les propriétés de votre compétition dans SeeYou.
// Le script déterminera automatiquement la classe et en déterminera les paramètres à appliquer (Dm et D1)
// Si vous organisez une classe Multiclasse, dans SoaringSpot choisissez de préférence la classe unknown puis renommez la en ''Multiclasse'' 
// Si vous organisez une classe Standard+15m+Biplace20m, dans SoaringSpot choisissez de préférence la classe 15m puis renommez la en ''Standard+15m+Biplace20m'' 
// 
// - Remarque sur les handicaps :
// * si la classe de compétition ne comporte pas de handicap, saisissez manuellement un handicap de 100 pour tous les concurrents
// * sinon saisissez le handicap de chaque concurrent en suivant les valeurs définies dans la NP4.1.d
// 
// - Historique des versions
// ==================================================
// Version  | Date     | Auteur       | Modification
// ==================================================
// 2023-1.00| 01/01/23 | Ph. de Péchy | Conforme NP4.1 2023 (inchangée par rapport à 2022)
// 2022-1.00| 07/01/22 | Ph. de Péchy | Conforme NP4.1 2022 (inchangée par rapport à 2021)
// 2021-1.00| 06/02/21 | Ph. de Péchy | Conforme NP4.1 2021 (inchangée par rapport à 2020)
// 2020-1.00| 03/02/20 | Ph. de Péchy | Conforme NP4.1 2020, détermination automatique de la classe
// 2019-1.00| 13/03/19 | Ph. de Péchy | Conforme NP4.1 2019
// 2018-1.00| 11/02/18 | Ph. de Péchy | Renommage du script année 2018
// 2017-1.00| 02/02/17 | Ph. de Péchy | Renommage du script année 2017
// 2016-1.00| 17/01/16 | Ph. de Péchy | Renommage du script année 2016
// 2015-1.01| 17/01/15 | Ph. de Péchy | Fichier lisez_moi.txt : changement des URL vers les manuels SeeYou
// 2015-1.00| 17/01/15 | Ph. de Péchy | Renommage du script année 2015
// 2014-1.00| 22/01/14 | Ph. de Péchy | Renommage du script année 2014
// 2013-1.00| 22/01/13 | Ph. de Péchy | Renommage du script année 2013
// 2013-1.00| 12/02/13 | Ph. de Péchy | N1 ne tient plus compte des handicaps
// 2012-1.00| 28/01/12 | Ph. de Péchy | Aucune modification du script FFVV, retrait des scripts obsolète, compatibilité NP4.1 édition 2012 et SeeYou4
// 2011-1.00| 26/01/11 | Ph. de Péchy | Modification scripts : script de scoring unique pour course sur circuit et épreuve de vitesse sur secteur, compatibilité NP4.1 édition 2011
// 2008-1.01| 27/04/08 | Ph. de Péchy | Modification scripts : les pilotes hors concours influent sur les scores mais pas sur les places
// 2008-1.00| 14/03/08 | Ph. de Péchy | Modification calcul épreuve de vitesse : tous les pilotes rentrés marquent le maximum de points distance
// 2007-2.00| 01/05/07 | Ph. de Péchy | Fiches de style XSL compatible avec SeeYou 3.7 (refonte du document XML)
// 2007-1.00| 22/02/07 | Ph. de Péchy | Le reglement des championnats 2006 étant étendu à toutes les compétitions fédérales, le kit 2006-1.00 est renommé en 2007-1.00.
//          |          |              | Puisqu''il n''existe plus beaucoup de compétitions sans handicap machine, seuls le kit avec handicap est proposé
//          |          |              | * ATTENTION : pour les championnats sans handicap machine (ex : champ. de France Standard et 18 mètres), appliquer un coefficient identique pour tous les planeurs - par exemple : 100.
// 2006-1.00| 01/05/06 | Ph. de Péchy | Prise en compte des modifications du reglement FFVV 2006 pour les championnats de France :
//          |          |              | * Dm = 50km (au lieu de 100km) - spécificité FFVV
//          |          |              | * H0 = plus petit handicap (et non le plus grand) - modif IGC 2005
//          |          |              | * Epreuve valide si un pilote marque plus de 50km et non plus 25% plus de 100km - spécificité FFVV
//          |          |              | Ajout de la version du kit dans daily.xsl
// 1.06     | 29/05/05 | Ph. de Péchy | Modification des fichiers daily.xsl et total.xsl :
//          |          |              | Prise en compte des scores ex-aequo
// 1.05     | 26/06/03 | Ph. de Péchy | Correction des scripts de distance et de vitesse :
//          |          |              | Application de la penalité vache facultative, mais formule imposée
// 1.04     | 29/05/03 | Ph. de Péchy | Correction de tous les scripts :
//          |          |              | 25% des concourrents ayant décollé doivent marquer 100km
// 1.03     | 27/05/03 | Ph. de Péchy | Correction des scripts des épreuves de vitesse  :
//          |          |              | dis=>tdis ; penalité de vache
// 1.02     | 27/05/03 | Ph. de Péchy | Correction des scripts des épreuves de distance :
//          |          |              | dis=>tdis ; penalité de vache
// 1.01     | 23/05/03 | Ph. de Péchy | Correction des scripts avec handicap (HO, TD)
// 1.00     | 22/05/03 | Ph. de Péchy | Création
//  

var
  // Déclaration des paramètres de lépreuve
  D1,   // Distance minimale pour marquer 1000 points (en mètres)
  Dm,   // Distance minimale de validation d''épreuve (en mètres)
  Td,   // Durée minimum si épreuve de vitesse (0 sinon),
  n1, 	// Nombre des concurrents crédités d''une distance Dc (sans handicap) supérieure à Dm
  n2, 	// Nombre des concurrents rentrés avec une Vc supérieure à 2*V0/3
  n3,   // Nombre de concurrents ayant complété l''épreuve
  n4,   // Nombre de concurrents ayant marqué une distance avec handicap (Dh) d''au moins Dm/2
  n,  	// Nombre des concurrents mis en l''air pour effectuer l''épreuve.
  D0, 	// Distance corrigée Dc la plus élevée de l''épreuve.
  V0, 	// Vitesse corrigée (du handicap) Vc la plus élevée de l''épreuve
  T0, 	// Durée réelle de l''épreuve du concurrent ayant réussi la meilleure Vc (=V0). Si aucun ne réussi a terminé l''épreuve, T0 = 3 heures
  H0,	// Handicap le plus faible des concurrents de la classe
  Pm, 	// Maximum (possible) des points pour l''épreuve
  PdM, 	// Maximum (possible) des points de distance pour l''épreuve
  PvM, 	// Maximum (possible) des points de vitesse pour l''épreuve
  F, 	// Facteur journalier
  Fcr 	// Facteur d''achèvement
  : double;
  
  // Déclaration des paramètres du concurrent
  D,	// Distance créditée au concurrent
  H,	// Handicap du concurrent, s''il est appliqué (sinon, H = 100 pour tous les concurrents)
  T, 	// Durée du parcours d''un planeur rentré (=Td quand le planeur rentre avant la fin du créneau)
  Dh,	// Distance créditée corrigée du handicap : Dh = D.H0/H 
  Pd, 	// Points de distance du concurrent
  V, 	// Vitesse créditée du concurrent V = D/T
  Vh,	// Vitesse créditée corrigée du handicap Vh = V.H0/H
  Pv, 	// Points de vitesse du concurrent
  S 	// Score obtenu par le concurrent dans l''épreuve (en points)	
  : double;
  
  // déclaration de variables de commodité
  PmaxDistance, PmaxTime : double;
  i : integer;
  ClasseCourante : string;

// fonction interne retournant le minimum parmi trois réels
function MinValue( a,b,c : double ) : double;
var m : double;
begin
  m := a;
  if b < m then m := b;
  if c < m then m := c;
  MinValue := m;
end;

// fonction test classe Multiclasse
function EstClasseMulticlasse() : boolean;
var EstValue : boolean;
begin
  EstValue := False;
  if Uppercase(Task.ClassName) = ''MULTICLASSE''	Then EstValue := true;
  if Uppercase(Task.ClassName) = ''MULTI-CLASSE''	Then EstValue := true;
  if EstValue Then ClasseCourante := ''Multiclasse'' ;
  EstClasseMulticlasse := EstValue ;
end;

// fonction test classe Std+15m+Bi20m
function EstClasseStd15mBi20m() : boolean;
var EstValue : boolean;
begin
  EstValue := False;
  if Task.ClassID = ''standard'' 		Then EstValue := True;
  if Task.ClassID = ''15_meter'' 		Then EstValue := True ;
  if Task.ClassID = ''double_seater''	Then EstValue := True ;
  if Uppercase(Task.ClassName) = ''STANDARD+15M+BIPLACE20M''	Then EstValue := True;
  if Uppercase(Task.ClassName) = ''STANDARD+15M+BIPLACES20M''	Then EstValue := True;
  if Uppercase(Task.ClassName) = ''STD+15M+BIPLACE20M''		Then EstValue := True;
  if Uppercase(Task.ClassName) = ''STD+15M+BIPLACES20M''		Then EstValue := True;
  if Uppercase(Task.ClassName) = ''STD+15M+BI20M''			Then EstValue := True;
  if EstValue Then ClasseCourante := ''Standard+15m+Biplace20m'' ;  
  EstClasseStd15mBi20m := EstValue ;
end;

// fonction test classe Club
function EstClasseClub() : boolean;
var EstValue : boolean;
begin
  EstValue := False;
  if Task.ClassID = ''club'' then EstValue := True;
  if Uppercase(Task.ClassName) = ''CLUB''	Then EstValue := True;
  if EstValue Then ClasseCourante := ''Club'' ;
  EstClasseClub := EstValue ;
end;

// fonction test classe 18m
function EstClasse18m() : boolean;
var EstValue : boolean;
begin
  EstValue := False;
  if Task.ClassID = ''18_meter'' then EstValue := True;
  if Uppercase(Task.ClassName) = ''18M''	Then EstValue := True;
  if Uppercase(Task.ClassName) = ''18 M''	Then EstValue := True;
  if Uppercase(Task.ClassName) = ''18METRES''	Then EstValue := True;
  if Uppercase(Task.ClassName) = ''18 METRES''	Then EstValue := True;
  if EstValue Then ClasseCourante := ''18m'' ;
  EstClasse18m := EstValue ;
end;

// fonction test classe Libre
function EstClasseLibre() : boolean;
var EstValue : boolean;
begin
  EstValue := False;
  if Task.ClassID = ''open'' then EstValue := True;
  if Uppercase(Task.ClassName) = ''OPEN''	Then EstValue := True;
  if Uppercase(Task.ClassName) = ''LIBRE''	Then EstValue := True;
  if Uppercase(Task.ClassName) = ''LIBRES''	Then EstValue := True;
  if EstValue Then ClasseCourante := ''Libre'' ;
  EstClasseLibre := EstValue ;
end;

begin
  // Calcul des parametres de l''épreuve
  ClasseCourante := ''par défaut'' ;

  // Distance minimale de validation d''épreuve (en mètres)
  // Attention : garder l''ordre pour maintenir les priotités d''identification de classe
  Dm := 100000.0; // valeur par défaut
  if EstClasseClub() 		Then Dm := 100000.0;
  if EstClasse18m()			Then Dm := 140000.0;
  if EstClasseLibre()		Then Dm := 140000.0;
  if EstClasseStd15mBi20m()	Then Dm := 120000.0;
  if EstClasseMulticlasse()	Then Dm := 100000.0;
  
  // Distance minimale pour marquer 1000 points (en mètres)
  // Attention : garder l''ordre pour maintenir les priotités d''identification de classe
  D1 := 250000; // valeur par défaut
  if EstClasseClub()			Then D1 := 250000.0;
  if EstClasse18m()				Then D1 := 350000.0;
  if EstClasseLibre()			Then D1 := 350000.0;
  if EstClasseStd15mBi20m()		Then D1 := 300000.0;
  if EstClasseMulticlasse()		Then D1 := 250000.0;

  // Calcul du handicap le plus faible (H0)
  H0 := 0;
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    if (i=0) then H0 := Pilots[i].Hcap;
    if Pilots[i].Hcap < H0 then H0 := Pilots[i].Hcap;
  end;
  if H0<=0 then Exit; // cas d''erreur
  
  // Calcul du nombre de concurrents décollés (N), du nombre ayant réalisé la distance minimale sans handicap (n1) et nombre ayant réalisé la distance après handicap de Dm/2 (N4).
  n  := 0;  
  n1 := 0;
  n4 := 0;
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
      D := Pilots[i].dis;
      Dh := Pilots[i].dis*H0/Pilots[i].Hcap ;
      if D >= Dm then n1 := n1+1;  // Competitors who have achieved at least Dm (sans handicap)
      if Dh >= Dm/2 then n4 := n4+1;  // Competitors who have achieved at least Dm/2 (avec handicap)
      if Pilots[i].takeoff > 0 then n := n+1;    // Number of competitors in the class having had a competition launch that Day
  end;
  if N=0 then Exit; // cas d''erreur

  // Calcul de la meilleure distance corrigée (D0), de la meilleure vitesse corrigée (V0), du temps d''épreuve du meilleure (T0) et du nombre de finishers (n3)
  D0 := 0;
  T0 := 0;
  V0 := 0;
  n3 := 0;
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
      // Calcul de la meilleure distance corrigée (D0)
      Dh := Pilots[i].dis*H0/Pilots[i].Hcap;
      if Dh > D0 then D0 := Dh;     
      // Calcul de la meilleure vitesse corrigée (V0), du temps d''épreuve du meilleure (T0)
      Vh := Pilots[i].speed*H0/Pilots[i].Hcap; // Vitesse du concurrent (dans le cas d''une épreuve de vitesse, si le concurrent est rentré avant le temps minimum, Pilots[i].speed en tient compte
      T  := Pilots[i].finish-Pilots[i].start;
      if Pilots[i].finish >= 0 then // uniquement pour les rentrés
      begin
        if Vh > V0 then
        begin
          n3 := n3 +1 ;
          V0 := Vh;
          T0 := T;
        end;
      end;
  end;
  // cas aucun rentré; T0=3 heures=3*3600 secondes
  if (T0=0) then T0 := 3.0*3600.0;
  // cas d''erreur, aucune distance marquée
  if (D0=0) then Exit;
  
  // Calcul la durée du créneau (Td en secondes)
  // Sert uniquement pour affichage d''information car Pilots[i].speed en tient compte
  Td := Task.Tasktime; // vaut 0 si course sur circuit imposé
  
  // Calcul du nombre de point maximum de l''épreuve (Pm)
  PmaxDistance := 1250.0*D0/D1-250.0;
  PmaxTime := (400.0*T0/3600.0)-200.0;
  Pm := MinValue( 1000.0 , PmaxDistance , PmaxTime);
  
 
  // Nombre des concurrents rentrés avec une Vh supérieure à 2*V0/3.
  n2 := 0;
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
      Vh := Pilots[i].speed*H0/Pilots[i].Hcap ;
      if Vh > (2.0/3.0*V0) then
      begin
        n2 := n2+1;
      end;
  end;

  // Calcul du facteur journalier (F)
  F := MinValue ( 1, 1 , 1.25*n1/n );

  // Calcul du facteur d''achevement (Fcr)
  Fcr := MinValue ( 1, 1 , 1.2*n2/N+0.6 );
  
  // Calcul des points vitesse max (PvM) et des points distance max (PdM)
  PvM := 2.0/3.0 * Pm * (n2/n);  
  PdM := Pm-PvM;
  
  // Calcul des points vitesse (Pv) et distance (Pd) pour chaque concurrent
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    Vh := Pilots[i].speed*H0/Pilots[i].Hcap;
    Dh := Pilots[i].dis*H0/Pilots[i].Hcap;
    // Cas d''un pilote ayant bouclé l''épreuve
    if Pilots[i].finish > 0 then
      begin
         Pv := PvM * (Vh-2.0/3.0*V0)/(1.0/3.0*V0) ;
         if Pv < 0 then Pv := 0; // Pv ne peut être négatif
         Pd := PdM; // un concurrent rentré marque tous les points distance
      end
    else
    //Cas d''un pilote n''ayant pas bouclé l''épreuve
      begin
        Pv := 0;
        Pd := PdM * (Dh/D0);
      end;
   
    // score journalier du pilote (S) arrondi avec application des pénalités
    S := Round( F*Fcr*(Pd+Pv) - Pilots[i].Penalty );
    Pilots[i].Points := S; // stockage
  end;
  
  // Stockage d''informations utiles à l''affichage
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    Pilots[i].sstart:=Pilots[i].start; // heure de départ
    Pilots[i].sfinish:=Pilots[i].finish; // heure d''arrivée
    Pilots[i].sdis:=Pilots[i].dis; // distance marquée
    Pilots[i].sspeed:=Pilots[i].speed; // vitesse marquée sans handicap
  end;
  
  // Informations présentées dans les résultats.
  Info1 := FFVPScript+'' - '';
  if Td=0 then Info1 := Info1+''Course sur circuit imposé''
          else Info1 := Info1+''Epreuve de vitesse sur secteurs'';
  Info1 := Info1 + '' - N=''+IntToStr(Round(N));
  Info1 := Info1 + '' - n1=''+IntToStr(Round(n1));
  Info1 := Info1 + '' - n2=''+IntToStr(Round(n2));
  Info1 := Info1 + '' - n3=''+IntToStr(Round(n3));
  Info1 := Info1 + '' - n4=''+IntToStr(Round(n4));
  Info1 := Info1 + '' - Facteur journalier (F)=''+FormatFloat(''0.000'',F);
  Info1 := Info1 + '' - Facteur achèvement (Fcr)=''+FormatFloat(''0.000'',Fcr);  

  Info2 := ''Param. Classe '';
  Info2 := Info2 + ClasseCourante;
  Info2 := Info2 + '' - Dist. min. valid. (Dm)=''+FormatFloat(''0'',Dm/1000)+''km'';
  Info2 := Info2 + '' - Dist. min. 1000pts (D1)=''+FormatFloat(''0'',D1/1000)+''km''; 
  Info2 := Info2 + '' - Points maximum (Pm)=''+IntToStr(Round(Pm));
  Info2 := Info2 + '' - Points vitesse (PvM)=''+FormatFloat(''0'',PvM);
  Info2 := Info2 + '' - Points distance (PdM)=''+FormatFloat(''0'',PdM);

end.

////////////// FIN /////////////////
', '2015-05-21 05:17:01', '2015-08-11 11:46:01');
INSERT INTO script (id_script, ref_class, name, category, content, created_at, updated_at) VALUES (4, NULL, ' eGlide_Elapsed_time_scoring (default)', 'glider', '﻿Program eGlide_Elapsed_time_scoring;

const 
  UseHandicaps = 2;   // set to: 0 to disable handicapping, 1 to use handicaps, 2 is auto (handicaps only for club and multi-seat)
  PowerTreshold = 20; // In Watts [W]. If Current*Voltage is less than that, it won''t count towards consumed energy.
  RefVoltage = 110;   // Fallback if nothing else is known about voltage used when engine is running
  RefCurrent = 200;   // Fallback if nothing is known about current consumption
  FreeAllowance = 2000; // Watt-hours. No penalty if less power was consumed
  EnginePenaltyPerSec = 1000/15/60;    // Penalty in seconds per Watt-hour consumed over Free Allowance. 1000 Wh of energy allows you to cruise for 15 minutes.
  Fa = 1.2;           // Amount of time penalty for next finisher / outlander

var
  Dm, D1,
  Dt, n1, n2, n3, n4, N, D0, Vo, T0, Tm, Hmin,
  Pm, Pdm, Pvm, Pn, F, Fcr, Day: Double;

  D, H, Dh, M, T, Dc, Pd, V, Vh, Pv, S : double;
  
  PmaxDistance, PmaxTime, PilotEnergyConsumption, CurrentPower, PilotEngineTime, EnginePenalty  : double;
  
  i,j, minIdx : integer;
  str : String;
  Interval, NumIntervals, GateIntervalPos, NumIntervalsPos, PilotStartInterval, PilotStartTime, PilotPEVStartTime, StartTimeBuffer : Integer;
  AAT : boolean;
  Auto_Hcaps_on : boolean;


begin
  // initial checks
  if GetArrayLength(Pilots) <= 1 then
    exit;

  Hmin := 100000;  // Lowest Handicap of all competitors in the class
  T0 := 10000000;
  Tm := 0; // slowest finisher time
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    Pilots[i].start := Task.NoStartBeforeTime;
	if Pilots[i].finish > 0 Then
	begin
	  Pilots[i].speed := Pilots[i].dis / (Pilots[i].finish-Pilots[i].start);
	end;
    If not Pilots[i].isHC Then
    begin
      If Pilots[i].Hcap < Hmin Then Hmin := Pilots[i].Hcap; // Lowest Handicap of all competitors in the class
	end;
  end;
  If Hmin=0 Then begin
          Info1 := '''';
	  Info2 := ''Error: Lowest handicap is zero!'';
  	Exit;
  end;

  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    If not Pilots[i].isHC Then
	begin
      // Find the lowest task time
      T := (Pilots[i].finish-Pilots[i].start) * Pilots[i].Hcap/Hmin;
      If (T < T0) and (Pilots[i].finish > 0) Then
      begin
        T0 := T;
		minIdx := i;
      end;

      // Find the slowest finisher
	  if T > Tm Then
	  begin
	    Tm := T;
	  end;
    end;
  end;
  
  // Energy Consumption by pilot on task
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    Pilots[i].Warning := '''';
    PilotEnergyConsumption := 0;
	PilotEngineTime := 0;

	for j := 0 to GetArrayLength(Pilots[i].Fixes)-1 do
	begin
	  if (Pilots[i].Fixes[j].Tsec > Pilots[i].start) and (Pilots[i].Fixes[j].Tsec < Pilots[i].finish) Then
	  begin
	    // If pilot has Cur and Vol
		if Pilots[i].HasCur then
		begin
			if not Pilots[i].HasVol Then
				Pilots[i].Fixes[j].Vol := RefVoltage;
			if (Pilots[i].Fixes[j].Cur > 0) and (Pilots[i].Fixes[j].Vol > 0) then
			begin
				CurrentPower := Pilots[i].Fixes[j].Cur * Pilots[i].Fixes[j].Vol;
				If CurrentPower > PowerTreshold then
				begin
					PilotEngineTime := PilotEngineTime + Pilots[i].Fixes[j+1].Tsec - Pilots[i].Fixes[j].Tsec;
	//				Pilots[i].Warning := Pilots[i].Warning + IntToStr(Round(Pilots[i].Fixes[j].Cur))+ '' * '' + IntToStr(Round(Pilots[i].Fixes[j].Vol)) + '' * '' + IntToStr(Pilots[i].Fixes[j+1].Tsec - Pilots[i].Fixes[j].Tsec) + #10;
					PilotEnergyConsumption := PilotEnergyConsumption + CurrentPower * (Pilots[i].Fixes[j+1].Tsec - Pilots[i].Fixes[j].Tsec) / 3600;
					Pilots[i].td1 := PilotEnergyConsumption;
				end;
			end;
		end
		else
		begin
			If Pilots[i].Fixes[j].EngineOn Then
			begin
				CurrentPower := RefCurrent * RefVoltage;
				PilotEngineTime := PilotEngineTime + Pilots[i].Fixes[j+1].Tsec - Pilots[i].Fixes[j].Tsec;
//				Pilots[i].Warning := Pilots[i].Warning + IntToStr(Round(Pilots[i].Fixes[j].Cur))+ '' * '' + IntToStr(Round(Pilots[i].Fixes[j].Vol)) + '' * '' + IntToStr(Pilots[i].Fixes[j+1].Tsec - Pilots[i].Fixes[j].Tsec) + #10;
				PilotEnergyConsumption := PilotEnergyConsumption + CurrentPower * (Pilots[i].Fixes[j+1].Tsec - Pilots[i].Fixes[j].Tsec) / 3600;
				Pilots[i].td1 := PilotEnergyConsumption;
			end;
		end;
	  end;
	end;

//	// Debug output
//	if Pilots[i].HasCur Then 
//      Pilots[i].Warning := Pilots[i].Warning + ''HasCur = 1''+#10
//	else
//      Pilots[i].Warning := Pilots[i].Warning + ''HasCur = 0''+#10;
//	if Pilots[i].HasVol Then 
//      Pilots[i].Warning := Pilots[i].Warning + ''HasVol = 1''+#10
//	else
//      Pilots[i].Warning := Pilots[i].Warning + ''HasVol = 0''+#10;
//	if Pilots[i].HasEnl Then 
//      Pilots[i].Warning := Pilots[i].Warning + ''HasEnl = 1''+#10
//	else
//      Pilots[i].Warning := Pilots[i].Warning + ''HasEnl = 0''+#10;
//	if Pilots[i].HasMop Then 
//      Pilots[i].Warning := Pilots[i].Warning + ''HasMop = 1''+#10
//	else
//      Pilots[i].Warning := Pilots[i].Warning + ''HasMop = 0''+#10;
	Pilots[i].Warning := Pilots[i].Warning + ''EngineTime = '' + IntToStr(Round(PilotEngineTime)) + '' s'' + #10;
	Pilots[i].Warning := Pilots[i].Warning + ''PowerConsumption = '' + IntToStr(Round(PilotEnergyConsumption)) + '' Wh'' +#10;
	if PilotEnergyConsumption > FreeAllowance then
	  Pilots[i].Warning := Pilots[i].Warning 
	    + ''Engine Penalty = '' + IntToStr(Round(PilotEnergyConsumption-FreeAllowance)) + '' Wh = '' 
	    + FormatFloat(''0.00'',((PilotEnergyConsumption - FreeAllowance) * EnginePenaltyPerSec / 60)) + '' minutes'' 
		+#10;
  end;

  
  // ELAPSED TIME SCORING
  for i:=0 to GetArrayLength(Pilots)-1 do 
  begin
    if Pilots[i].finish > 0 then
	begin
      Pilots[i].Points := -1.0*((Pilots[i].finish - Pilots[i].start)*Pilots[i].Hcap/Hmin - T0)/60;
	end
	else
	begin
	  // Outlanders get 1.2 x the slowest finisher
      Pilots[i].Points := (-1.0*Tm*Fa + T0)/60;
	end;

    // Engine penalty
    PilotEnergyConsumption := Pilots[i].td1;
    if PilotEnergyConsumption > FreeAllowance then
	begin
	  EnginePenalty := (PilotEnergyConsumption - FreeAllowance) * EnginePenaltyPerSec / 60; // Penalty in minutes
	  Pilots[i].Points := Pilots[i].Points - EnginePenalty;
	end;
	
	//Worst score a pilot can get is 1.2 times the last finisher''s time.
	if Pilots[i].Points < (-1.0*Tm*Fa+T0)/60 Then
	  Pilots[i].Points := (-1.0*Tm*Fa+T0)/60;
	  
	Pilots[i].Points := Round((Pilots[i].Points- Pilots[i].Penalty/60)*100)/100; // Expected penalty is in seconds
  end;
  
  // Data which is presented in the score-sheets
  for i:=0 to GetArrayLength(Pilots)-1 do
  begin
    Pilots[i].sstart:=Pilots[i].start;
    Pilots[i].sfinish:=Pilots[i].finish;
    Pilots[i].sdis:=Pilots[i].dis;
    Pilots[i].sspeed:=Pilots[i].speed;
  end;
//  Pilots[minIdx].Points := Round(T0/60*100)/100;
  
  // Info fields, also presented on the Score Sheets
  Info1 := ''Elapsed time race'';
  Info1 := Info1 + '', results in minutes behind leader, handicapped''; 

end.
', '2015-05-21 05:17:01', '2019-06-21 11:22:51');
