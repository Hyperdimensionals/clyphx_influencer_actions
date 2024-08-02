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
        self.last_scene_id = None
        self.last_scene_tempo = -1
        self.last_song_tempo = 120
        self.last_triggered_scene = None
        self.next_scene = None
    
        self.add_global_action("adjbpm", self.adjust_bpm)

        with open('/Users/blaise/Documents/Programming/Ableton Extensions/ClyphX Influencer Actions/useractiondebug.txt', 'w') as f:
            f.writelines(str(self.song().scenes))
        song = self.song()
        song.add_tempo_listener(self.on_tempo_changed)
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
        if self.last_triggered_scene.is_triggered:
            # Since follow actions trigger next scene immediately, 
            # before playing clips, must find way to apply triggered scene to next time only
            # when scene is triggered at xclip play
            scene = self.next_scene if self.next_scene else song.view.selected_scene
            self.next_scene = self.last_triggered_scene
        else:
            scene = self.last_triggered_scene  # was song.view.selected_scene

        xclip = action_def["xtrigger"]

        scene_clips = [
            c.clip._live_ptr for c in scene.clip_slots if c.clip is not None]

        clip_playing = 0
    
        if (scene.tempo > 0) and (xclip._live_ptr in scene_clips):
            if ((self.tempo_diff == 0) and (
                    self.last_scene_tempo == self.last_song_tempo)):
                # If last calculated tempo difference was 0, and the song 
                # tempo hasn't been changed since previous tempo adjustment,
                # don't do anything.
                return False
            #self.canonical_parent.show_message("%s: adjbpm test" % scene._live_ptr)
            if (self.last_scene_id != None):
                self.tempo_diff = self.get_tempo_diff(
                    self.last_scene_tempo, self.last_song_tempo)
            self.last_scene_id = scene._live_ptr
            self.last_scene_tempo = scene.tempo

        #    self.any_scene_clips_playing(scene.clip_slots)
        #    if self.any_scene_clips_playing(scene.clip_slots):
            song.tempo = self.get_adjusted_bpm(
                scene.tempo, self.tempo_diff, self.bpm_adj_max)
        self.canonical_parent.show_message("scene tempo: {}, last scene tempo: {}, lasttempo: {}".format(scene.tempo, self.last_scene_tempo, self.last_song_tempo))

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

    # Listeners #
    #############

    @subject_slot('scenes')
    def scenes_listener(self):
        scenes = (list(self.song().scenes))
        self.is_triggered_listener.replace_subjects(scenes)

    @subject_slot_group('is_triggered')
    def is_triggered_listener(self, scene):
        self.last_triggered_scene = scene
        #self.canonical_parent.show_message('Scene {} is triggered'.format(scene.name)) 

    def on_tempo_changed(self):
        """
        Update self.last_song_tempo when song tempo changes.
        Ignores tempo change if scene and song tempo are the same
        since scene sets song tempo before adjustbpm can run,
        preventing proper adjustment.
        """
        song = self.song()
        scene = self.last_triggered_scene
        if scene.is_triggered: #delete if found unecessary
            self.last_song_tempo = song.tempo
        #    self.tempo_at_scene_trigger = song.tempo
        elif (scene.tempo == song.tempo):
            pass
        else:
            self.last_song_tempo = song.tempo

        #if scene.tempo == self.last_scene_tempo:
            #self.canonical_parent.show_message("{}, {}: Scenes tempos same".format(scene.tempo, self.last_scene_tempo))
    
    def on_scene_changed(self):
            self.canonical_parent.show_message("Scene Changed")
    

    def get_obj_attr_list(self, obj):
        return [(str(attribute) + '\n') for attribute in dir(obj)]
    def write_to_file(self, text):
        with open('/Users/blaise/Documents/Programming/Ableton Extensions/ClyphX Influencer Actions/useractiondebug.txt', 'a') as f:
            f.write(text)

class SceneSettings():
    """"""
    def __init__(self, scene=None, scene_tempo=None, song_tempo=None):
        self.scene = scene
        self.tempo = scene_tempo
        self.song_tempo = song_tempo
        