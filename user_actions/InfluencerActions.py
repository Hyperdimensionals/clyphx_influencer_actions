import Live
import re
from ClyphX_Pro.clyphx_pro.UserActionsBase import UserActionsBase
from _Framework.SubjectSlot import subject_slot, subject_slot_group

import datetime
import os.path

class InfluencerActions(UserActionsBase):
    """
    Actions by Digital Influencer. ADJBPM allows adjustment from scene tempo.
    """
    def __init__(self, *a, **k):
        super(InfluencerActions, self).__init__(*a, **k)
        self.scenes_listener.subject = self.song()
        self.scenes_listener()

    def disconnect(self):
        super(InfluencerActions, self).disconnect()

    def create_actions(self):
        self.action_name = "adjbpm"
        self.tempo_diff = -.1  # Stores amount song tempo differs from scene tempo setting
        self.bpm_adj_max = .25  # decimal, max adjustment limit.
        self.bpm_adj_active = True  # Stores whether tempo adjustment is active.
        self.last_triggered = None  # Stores object containing tempo and scene
                                    # at last scene trigger.
                                    # Last triggered scene is NOT the active 
                                    # scene when Follow Actions are enabled.
        self.scene_last_adjusted = None # Last scene to be tempo adjusted.
        self.prev_scene = None  # Stores previous scene, for when current
                                # triggered scene is not current scene.

        self.song_last_playing_state = False
        self.song_started_playing = False
        self.last_song_tempo = None

        self.add_global_action(self.action_name, self.adjust_bpm)

        song = self.song()
        song.add_tempo_listener(self.on_tempo_changed)
        song.add_is_playing_listener(self.on_is_playing_changed)

        self.debug = False
        if self.debug:
            self.logging_dir = self.get_logging_dir()

    def adjust_bpm(self, action_def, args):
        """
        Adjust a triggered scene's set tempo based on current song tempo.
        :action_def: dict, ClyphX puts content related to action type here.
        :args: str, contains args passed by user in Ableton.
        :return: None
        """        
        args = args.strip()
        args = args.split()
        if "max" in args:  # Adjust max percent change as decimal.
            self.set_max(args)
        if "addall" in args: # Add action str to xclip in all scenes with tempos.
            self.add_action_to_tempo_scenes(self.action_name)

        if "on" in args:
            self.bpm_adj_active = True
        elif "off" in args:  # Deactivates BPM adjustment, 
                             # Scene tempos will apply normally w/ no adjustment
            self.bpm_adj_active = False
            self.last_song_tempo = None
            return False

        if not self.bpm_adj_active:
            return False
        
        song = self.song()

        if (self.last_song_tempo is None):
            # Adj will be based on current tempo if no last tempo assigned.
            # last tempo is set to None when adjbpm is turned off.
            self.last_song_tempo = song.tempo

        xclip = action_def["xtrigger"]
        scene = self.get_scene_by_clip(xclip)

        if not self.is_active_scene(scene):
            return False

        pre_adj_tempo = self.last_song_tempo
        last_adj_scene = self.scene_last_adjusted

        if (scene) and (scene.tempo > 0):
            if last_adj_scene:
                last_scene_tempo = last_adj_scene.tempo
            else:
                last_scene_tempo = scene.tempo
            if not ((self.tempo_diff == 0) and (
                    last_scene_tempo == pre_adj_tempo)):
                # If last calculated tempo difference was 0, and the song 
                # tempo hasn't been changed since previous tempo adjustment,
                # don't do anything.
                self.tempo_diff = self.get_tempo_diff(
                    last_scene_tempo, pre_adj_tempo)
                song.tempo = self.get_adjusted_bpm(
                    scene.tempo, self.tempo_diff, self.bpm_adj_max)

            self.scene_last_adjusted = scene
    
        debug_str = self.debug_msg(
            last_adj_scene.name if last_adj_scene else None, 
            last_adj_scene.tempo if last_adj_scene else None,
            pre_adj_tempo, self.tempo_diff, 
            scene.name if scene else None, 
            scene.tempo if scene else None,
            song.tempo)

        # self.canonical_parent.show_message(debug_str)

    def get_adjusted_bpm(self, tempo_pre, adj, adj_max):
        """
        Adjust given tempo by current adjustment value, considering max adj
        :param tempo_pre: float, tempo to adjust.
        :param adj: decimal, represents percentage adjustment to apply.
                    Calculated using self.get_tempo_diff method.
        :param adj_max: decimal, represents maximum allowable adjustment as decimel.
        :return bpm_adjust: float, adjusted bpm
        """
        if not adj:
            return tempo_pre
        # Check adjustment against max adjustment
        if adj_max <= 0:
            pass
        else:
            adj_abs = min(abs(adj), abs(adj_max))
        percent_adjustment = adj_abs * (adj/abs(adj))
        # Must consider if adj is negative /\

        bpm_adjusted = round(tempo_pre * (1 + percent_adjustment), 2)

        return bpm_adjusted
    
    def any_scene_clips_playing(self, scene_clips):
        """
        Check if scene has at least one playing clip.
        :param scene_clips: scene_clips object,
        :return: bool
        """
        for clip in scene_clips:
            if clip.is_playing:
                return True
        return False
    
    def get_tempo_diff(self, last_scene_tempo, current_tempo):
        """
        Returns difference between two tempos.
        :param last_scene_tempo: float, tempo set by last scene.
        :param current_tempo: float, current tempo of set.
        :return tempo_diff: float, difference between two.
        """
        if last_scene_tempo == -1:
            return False
        tempo_diff = ((current_tempo - last_scene_tempo) / last_scene_tempo)
        return tempo_diff

    def is_active_scene(self, scene):
        """
        Checks if given scene is currently playing scene.
        Considers behavior when follow actions enabled.
        :param scene: Scene object, scene to check
        :return: bool, if given scene is active scene.
        """
        if scene._live_ptr == self.get_active_scene()._live_ptr:
            return True
        else:
            return False

    def get_active_scene(self):
        """
        Return currently playing scene at time of xclip trigger.
        Checks for if follow actions are enabled.
        :return: Scene object
        """
        song = self.song()
        song_started = self.song_just_started()
        if self.follow_actions_enabled():
            # is_triggered is always false if xclip 
            # activated when song is not playing
            if song_started:
                scene = song.view.selected_scene
                self.prev_scene = None
            else:
                scene = self.prev_scene if self.prev_scene else song.view.selected_scene
        else:
            scene = self.last_triggered.scene if self.last_triggered.scene else song.view.selected_scene
        return scene

    def get_scene_by_clip(self, clip):
        """
        Search for scene which holds given clip
        :param clip: Clip object
        :return: Scene object if present, else None
        """
        song = self.song()
        for scene in song.scenes:
            if clip._live_ptr in [
                c.clip._live_ptr for c in scene.clip_slots if c.clip is not None]:
                return scene
        return None
    
    def get_scene_index(self, scene_ptr):
        """
        Find index of scene within song scene list with specified _live_ptr
        """
        scene_ptrs = [s._live_ptr for s in self.song().scenes]
        return scene_ptrs.index(scene_ptr)
    
    def song_just_started(self):
        """
        Checks if song started playing since last check,
        self.song_started_playing updated via listener.
        :return song_started: bool
        """
        song_started = False
        if self.song_started_playing == True:
            song_started = True
        self.song_started_playing = False 
        return song_started

    def follow_actions_enabled(self):
        """
        Check if follow actions are enabled.
        This is a crude indirect check, checking if the stored last triggered
        scene is currently triggered, and if the last adjusted scene is
        directly above the last triggered scene.
        :return: bool, best guess of whether follow actions are enabled.
        """
        scene_last_adjusted_above = False
        scene_above_index = self.get_scene_index(self.last_triggered.scene._live_ptr) - 1
        if self.scene_last_adjusted:
            if (self.song().scenes[
                scene_above_index]._live_ptr == self.scene_last_adjusted._live_ptr
                ):
                scene_last_adjusted_above = True  
                # TODO: Not currently deemed necessary, but logic still
                # here for future consideration.      
        if (self.last_triggered.scene.is_triggered):
            return True
        else:
            return False
        
    def append_xclip_name(self, action_name, clips_list):
        """
        Add action to the first xclip found within given clips_list.
        This only checks the first xclip found, so may double up given action
        in lists with multiple xclips. (TODO)
        :param action_name: str, name of action to append to xclip name.
        :param clips_list: list, clips from scene.
        :return: scene obj, scene with appended xclip as name.
        """
        xclip_match = "^\[.*\]"
        action_end_match = ";\s*$"

        action_end_append = "; "
        action_append = " " + action_name + ";"
        for c in clips_list:
            name_lower = c.name.lower()
            if (re.search(xclip_match, name_lower) and
                (not re.search(action_name, name_lower))):
                name_l = []
                name_l.append(c.name)
                if not re.search(action_end_match, name_lower):
                    name_l.append(action_end_append)
                name_l.append(action_append)
                new_name = ''.join(name_l)
                c.name = new_name
                return c

    def add_action_to_all_scenes(self, action_name):
        """
        Add action to every scene where xclip is present.
        Action will not be added if it is already present in the found xclip.
        :param action_name: str, name of action to add to xclip
        :return: None
        """
        for scene in self.song().scenes:
            self.append_xclip_name(action_name,
                [c.clip for c in scene.clip_slots if c.clip is not None]
            )

    def set_max(self, args):
        """
        Set maximum adjustment.
        :param args: Action arguments 
        :return: True if max has been updated
        :rtype: bool
        """
        max_input_error = "MAX must be followed by decimal " \
                          "representing percentage max adjustment."
        
        max_val = self.get_arg_val_from_list(args, 'max', max_input_error)
        if max_val is not None:
            self.bpm_adj_max = max_val
            self.canonical_parent.show_message(
                "ADJBPM: Max tempo adjustment now " + str(
                    max_val * 100) + " %."
            )
            return True

    # Action Argument Funcs #
    #########################
    # Methods related to interpreting action args and executing their commands

    def get_arg_val_from_list(self, li, arg_str, input_error_msg=None):
        """
        Find numerical value in list which follows given argument name.
        :param li: List of args and values.
        :param arg_str: arg to find values for.
        :param input_error_msg: Error message to display if value == NAN.
        :return: float, value of argument
        """
        arg_str = arg_str.lower()
        arg_str_index = li.index(arg_str)
        arg_val = None

        if input_error_msg:
            input_error_msg = "ADJBPM: " + str(input_error_msg)
        else:
            input_error_msg = "ADJBPM: {0} argument must be followed by " \
                            "number.".format(arg_str)
        try:
            arg_val = float(li[arg_str_index + 1])
            # Arg value set by user should be next item in list.
        except IndexError:
            self.canonical_parent.show_message(input_error_msg)
            return None
        except ValueError:
            self.canonical_parent.show_message(input_error_msg)
            return None
        return arg_val

    def add_action_to_tempo_scenes(self, action_name):
        """
        Add action to every scene where an xclip is present and scene has tempo.
        Action will not be added if it is already present in the found xclip.
        :param action_name: str, name of action to add to xclip
        :return: None
        """
        for scene in self.song().scenes:
            if scene.tempo > 0:
                self.append_xclip_name(action_name,
                    [c.clip for c in scene.clip_slots if c.clip is not None]
                )

    # Listeners #
    #############

    @subject_slot('scenes')
    def scenes_listener(self):
        scenes = (list(self.song().scenes))
        self.is_triggered_listener.replace_subjects(scenes)

    @subject_slot_group('is_triggered')
    def is_triggered_listener(self, scene):
        """
        Listens for triggered scenes.
        When follow actions are off, song is playing, and there is quantization:
        when you 'play' a scene, scene triggers before it's playing,
        When scenes are triggered by follow actions and not user input,
        triggering of the next scene begins right before the current scene plays
        and this listener will see the NEXT scene to play.
        """
        self.prev_scene = self.last_triggered.scene if self.last_triggered else None
        self.last_triggered = Snapshot(scene, self.song().tempo)

    def on_tempo_changed(self):
        """
        Tempo change listener. 
        Updates self.last_song_tempo when song tempo changes.
        Ignores tempo change if scene and song tempo are the same
        since scene sets song tempo before adjustbpm can run,
        preventing proper adjustment.
        """
        if not self.bpm_adj_active:
            # Doesn't capture current tempo when action is deactivated
            # TODO: Turn off listener if possible?
            return False
        song = self.song()

        if self.follow_actions_enabled():
            scene = self.prev_scene
        else:
            scene = self.last_triggered.scene

        if scene and (scene.tempo == song.tempo):
            # Ignores tempo changes in this case becasue when follow actions
            # are enabled, song tempo is briefly set to actual scene tempo 
            # before adjustment can take place. So if tempo change was recorded
            # in this case, adjustment func would always see a tempo difference 
            # of 0.
            return False
        else:
            self.last_song_tempo = song.tempo
 
    def on_is_playing_changed(self):
        """
        is_playing listener func. Triggered when song play state changed.
        Assigns change state to variable when song is started.
        """
        # If play button in ableton GUI is pressed WHILE song
        # is already playing, song_started_playing will be set to true
        # probably because is_playing is briefly False any time play 
        # button is activated regardless of current play state
        song_playing = self.song().is_playing
        if (self.song_last_playing_state == False) and song_playing:
            self.song_started_playing = True
        else:
            self.song_started_playing = False

        self.song_last_playing_state = song_playing
            
    # Debugging and Testing #
    #########################
    def _debug_on_check(func):
        def inner(self, *args, **kwargs):
            if self.debug:
                return func(self, *args, **kwargs)
        return inner

    def get_obj_attr_list(self, obj):
        return [(str(attribute) + '\n') for attribute in dir(obj)]
    
    def debug_log_msg(self, text):
        with open(os.path.join(self.logging_dir, 'influenceractions_debug.txt'), 'a') as f:
            f.write(text)

    def debug_get_str(
        self, current_scene_name=None, current_scene_tempo=None,
        pre_adj_tempo=None, tempo_diff=None, scene_name=None,
        scene_tempo=None, song_tempo=None):
        """
        Format debug string listing relevent song and variable states.
        Non-strings are converted to strings explicitly
        :param current_scene_name: str, name of scene found by action to be playing
        :param current_scene_tempo: float, tempo of playing scene
        :param pre_adj_tempo: float, tempo before adjustment algo ran
        :param tempo_diff: float, amount song tempo differs from current scene
        :param scene_name: str, name of scene last xclip is on
        :param scene_tempo: float, tempo of scene last xclip is on
        :param song_tempo: float, current tempo of song
        :return: str, debug message in descriptive english prose.
        """
        return ("The last used scene was '{0}', With a set tempo of {1},"
            " and the last recorded tempo of {2} Deviated by this scene’s "
            "tempo by {3}. \nThe new adjusted scene is '{4}', with a set "
            "tempo of {5}\n Song tempo after adj: {6}\n\n").format(
                    str(current_scene_name), str(current_scene_tempo),
                    str(pre_adj_tempo), str(tempo_diff), str(scene_name),
                    str(scene_tempo), str(song_tempo))
    
    @_debug_on_check
    def debug_msg(
        self, current_scene_name=None, current_scene_tempo=None,
        pre_adj_tempo=None, tempo_diff=None, scene_name=None,
        scene_tempo=None, song_tempo=None):
        """
        Take given song variables, create readable str, and log them in file.
        :return: str, debug message created and logged
        """

        msg = self.debug_get_str(current_scene_name, current_scene_tempo,
            pre_adj_tempo, tempo_diff, scene_name, scene_tempo, song_tempo)

        self.debug_log_msg(msg)

        return msg

    def get_logging_dir(self):
        """
        Creates directory for logging files and returns directory.
        :return: str, directory of logging files.
        """
        fpath = os.path.dirname(os.path.abspath(__file__))
        fullpath = os.path.join(fpath,'InfluencerActions_logs')
        if not os.path.isdir(fullpath):
            os.makedirs(fullpath)
        return fullpath

    # TODO: Test Funcs below.
    def test_scene_tempo(self):
        """
        Compare current song tempo to a given BPM
        BPM may be given from action's TEST arg.
        """
        pass
    
    def test_output_result_on_clip(self, scene):
        """
        Display test result on clip, clip colored green if passed.
        :param scene: _description_
        :type scene: _type_
        """
        pass


class Snapshot():
    """
    Record states of given variables at time of instance creation
    :param scene: Current scene object.
    :param song_tempo: float, Current tempo of song.
    """
    def __init__(self, scene=None, song_tempo=None):
        """
        """
        self.scene = scene
        self.song_tempo = song_tempo