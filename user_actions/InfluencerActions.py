import Live
from ClyphX_Pro.clyphx_pro.UserActionsBase import UserActionsBase
from _Framework.SubjectSlot import subject_slot, subject_slot_group

class InfluencerActions(UserActionsBase):
    """ """
    def __init__(self, *a, **k):
        super(InfluencerActions, self).__init__(*a, **k)
        self.scenes_listener.subject = self.song()
        self.scenes_listener()

    def disconnect(self):
        super(InfluencerActions, self).disconnect()

    def create_actions(self):
        self.tempo_diff = -.1  # Stores amount song tempo differs from scene tempo setting
        self.bpm_adj_max = .25  # decimal, max adjustment limit
        self.bpm_adj_active = True  # Stores whether tempo adjustment is allowed
        self.last_triggered = None
        self.current_scene = None # Tracks last scene to be tempo adjusted
    
        self.song_last_playing_state = False
        self.song_started_playing = False
        self.last_song_tempo = 120
        self.last_triggered_scene = None
        self.prev_scene = None
        self.scene_last = None

        self.add_global_action("adjbpm", self.adjust_bpm)

        #with open('/Users/blaise/Documents/Programming/Ableton Extensions/ClyphX Influencer Actions/useractiondebug.txt', 'w') as f:
        #    f.writelines(str(self.song().scenes))
        song = self.song()
        song.add_tempo_listener(self.on_tempo_changed)
        song.add_is_playing_listener(self.on_is_playing_changed)
        # song.add_scenes_listener(self.on_scene_changed)

    def adjust_bpm(self, action_def, args):
        """
        Adjust song BPM based on difference between last song and scene tempo.
        """
        args = args.strip()
        # args = args.split()
        if args == "on":
            self.bpm_adj_active = True
            return True
        elif args == "off":
            self.bpm_adj_active = False
            return False
        if not self.bpm_adj_active:
            return False
        song = self.song()

        xclip = action_def["xtrigger"]

        clip_playing = 0

        scene = self.find_active_scene(xclip)
        pre_adj_tempo = self.last_song_tempo
        if (scene) and (scene.tempo > 0):
            if ((self.tempo_diff == 0) and (
                    self.current_scene.tempo == self.last_song_tempo)):
                # If last calculated tempo difference was 0, and the song 
                # tempo hasn't been changed since previous tempo adjustment,
                # don't do anything.
                self.canonical_parent.show_message("No Tempo Difference")

                return False
            #self.canonical_parent.show_message("%s: adjbpm test" % scene._live_ptr)
            
            #if (self.last_triggered.scene._live_ptr == scene._live_ptr):
            #    self.canonical_parent.show_message("Last Scene Triggered is this scene")
            #if (self.prev_scene._live_ptr == scene._live_ptr):
            #    self.canonical_parent.show_message("Prev scene triggered is this scene: {}, last: {}".format(self.prev_scene.name, self.last_triggered.scene.name))
            
            #self.canonical_parent.show_message("Test")
            if self.current_scene:
                self.tempo_diff = self.get_tempo_diff(
                    self.current_scene.tempo, self.last_song_tempo)

        #    self.any_scene_clips_playing(scene.clip_slots)
        #    if self.any_scene_clips_playing(scene.clip_slots):
            song.tempo = self.get_adjusted_bpm(
                scene.tempo, self.tempo_diff, self.bpm_adj_max)

            if (self.current_scene and scene):
                self.write_to_file(
                    "The last used scene was '{0}', With a set tempo of {1}, and the "
                    "last recorded tempo of {2} Deviated by this scene’s tempo"
                    " by {3}. \nThe new adjusted scene is '{4}', with a set "
                    "tempo of {5}\n"
                    "Song tempo after adj: {6}\n\n".format(
                        self.current_scene.name, self.current_scene.tempo, pre_adj_tempo, 
                        self.tempo_diff, scene.name, scene.tempo, song.tempo)
                )

            self.current_scene = scene

    def get_adjusted_bpm(self, pre_tempo, adj, adj_max):
        """
        Adjust given tempo with current adjustment value, w/ max
        :param pre_tempo: float, tempo to adjust.
        :param adj: decimal, represents percentage adjustment.
        :param adj_max: decimal, represents maximum allowable adjustment.
        :return bpm_adjust: float, adjusted bpm
        """
        # Check adjustment against max adjustment
        percent_adjustment = min(abs(adj), abs(adj_max)) * (adj/abs(adj))
        bpm_adjusted = round(pre_tempo * (1 + percent_adjustment), 2)

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
        if last_scene_tempo == -1:
            return False
        tempo_diff = ((current_tempo - last_scene_tempo) / last_scene_tempo)
        return tempo_diff

    def get_active_scene(self):
        """
        Return currently playing scene at time of xclip trigger
        DEPRECATED
        Checks if follow actions are enabled
        :return: Scene Object
        """
        song = self.song()
        song_started = self.check_song_just_started()
        if self.follow_actions_enabled():
            # is_triggered is always false if xclip activated when song is not playing
            # Since follow actions trigger next scene immediately, 
            # before playing clips, must find way to apply triggered scene to next time only
            # when scene is triggered at xclip play
            if song_started:
                scene = song.view.selected_scene
            else:
                scene = self.prev_scene if self.prev_scene else song.view.selected_scene
        else:
            scene = self.last_triggered.scene if self.last_triggered.scene else song.view.selected_scene
        return scene

    def find_active_scene(self, clip):
        """
        Search for scene in song which holds given clip
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
        scene_ptrs = [s._live_ptr for s in self.song().scenes]
        return scene_ptrs.index(scene_ptr)
    
    def check_song_just_started(self):
        """
        Checks if song just started playing based on listener assigned var.
        Resets song_started_playing var to false after checked
        """
        song_started = False
        if self.song_started_playing == True:
            song_started = True
        self.song_started_playing = False 
        return song_started

    def follow_actions_enabled(self):
        """
        Check if follow actions are enabled
        This is a crude indirect check, checking if the stored last triggered
        scene is currently triggered, and if the last adjusted scene is
        directly above the last triggered scene
        """
        current_scene_above = False
        scene_above_ptr = self.get_scene_index(self.last_triggered.scene._live_ptr) - 1
        if self.current_scene:
            if (self.song().scenes[
                scene_above_ptr]._live_ptr == self.current_scene._live_ptr
                ):
                current_scene_above = True
                self.canonical_parent.show_message("Scene Above: {}, Cur Scene: {}".format(self.song().scenes[scene_above_ptr]._live_ptr, self.current_scene._live_ptr))
        
        if (self.last_triggered.scene.is_triggered):
            return True
        else:
            return False


    # Listeners #
    #############

    @subject_slot('scenes')
    def scenes_listener(self):
        scenes = (list(self.song().scenes))
        self.is_triggered_listener.replace_subjects(scenes)

    @subject_slot_group('is_triggered')
    def is_triggered_listener(self, scene):
        """

        When follow actions are off, song is playing, and there is quantization,
        when you 'play' a scene, scene triggers once when it's triggered but
        not yet playing,
        When scenes are triggered by follow actions and not user input,
        triggering happens right before a scene plays and the 
        scene after the now playing scene is triggered.
        """
        self.prev_scene = self.last_triggered.scene if self.last_triggered else None
        self.last_triggered_scene = scene
        self.last_triggered = Snapshot(scene, self.song().tempo)
        #self.canonical_parent.show_message(
        #    'Scene {} is triggered, curradj: {}, lastsongbpm: {}'.format(self.last_triggered.scene.name, self.tempo_diff, self.last_song_tempo)) 

    def on_tempo_changed(self):
        """
        Update self.last_song_tempo when song tempo changes.
        Ignores tempo change if scene and song tempo are the same
        since scene sets song tempo before adjustbpm can run,
        preventing proper adjustment.
        """
        song = self.song()
        if not self.current_scene:
            self.last_song_tempo = song.tempo
            return
        elif self.follow_actions_enabled():
            scene = self.prev_scene
            # self.canonical_parent.show_message("Last Tempo: {}".format(str(self.last_song_tempo)))
        else:
            scene = self.last_triggered.scene

        if (scene.tempo == song.tempo):
            pass
        else:
            self.last_song_tempo = song.tempo
 
    def on_is_playing_changed(self):
        # If play button in ableton GUI is used to restart playing WHILE song
        # is already playing, song_start_playing will be set to true
        # probably because is_playing is briefly False any time play 
        # button is activated regardless of current play state
        song_playing = self.song().is_playing
        if (self.song_last_playing_state == False) and song_playing:
            self.song_started_playing = True
        else:
            self.song_started_playing = False

        self.song_last_playing_state = song_playing
        #self.song_last_playing_state = 
    def on_scene_changed(self):
            self.canonical_parent.show_message("Scene Changed")

    # Debugging #
    #############
    def get_obj_attr_list(self, obj):
        return [(str(attribute) + '\n') for attribute in dir(obj)]
    def write_to_file(self, text):
        with open('/Users/blaise/Documents/Programming/Ableton Extensions/clyphx_influencer_actions/useractiondebug.txt', 'a') as f:
            f.write(text)

class Snapshot():
    """"""
    def __init__(self, scene=None, song_tempo=None):
        self.scene = scene
        self.scene_id = scene._live_ptr
        self.song_tempo = song_tempo
