# Influencer's ClyphX User Actions

## Installation

Go to your Ableton `User Library` folder, and navigate to ```Remote Scripts/ClyphX_Pro/clyphx_pro/user_actions```
Place the file `InfluencerActions.py` (located within its own 'user_actions' directory here) into this folder.  

## Action Usage - ADJBPM

```[EXAMPLE] ADJBPM;```

 When a scene that has a set tempo is triggered, when this action is active it adjusts the tempo the scene plays at based on how much the current tempo has deviated from the last played scene's tempo. 

This is useful if your set has scenes with different tempos, and you still want to have these relative tempo changes, but during a particular performance you want the entire set, or whenever you decide, to be faster or slower than usual. 

For example, in the middle of a section that is 100 BPM, you decide to up the BPM by 10% to 110 BPM. With `ADJBPM` active, any scenes with an xclip with the `adjbpm;` action present will now play 10% faster than their set tempo. So if you subsequently played a scene set to 50 BPM, it would now play at 55 BPM.

This action watches the song BPM all of the time, so whenever you change the tempo, it will adjust for these changes when the next scene with an assigned tempo is played.

## Commands and Variations

The commands below can be set simultaneously, so ```ADJBPM ON MAX .75 ADDALL;``` is a valid action.

### ON / OFF - Activating and Deactivating

This action can be activated and deactivated with `ADJBPM ON;` and `ADJBPM OFF;`. When off, bpm adjustments will not occur, though the commands below will still work.

### MAX - Maximum Adjustment Limits

You can set an upper or lower limit to adjustments by adding the `MAX` command to this action, followed by a decimal indicating the percentage of adjustment to allow (the 'decimal' can be larger than 1). For example:

```[EXAMPLE] ADJBPM MAX .5;```

Would set the maximum allowable tempo adjustment to 50%.

The default adjustment limit is 25%.

To bypass the adjustment limit, set `MAX` to `0`.

### ADDALL

```[EXAMPLE] ADJBPM ADDALL;```

To conveniently integrate this action into sets with already existing xclips, The `ADDALL` command adds the `ADJBPM;` action to the first xclip found on any and all scenes with an assigned tempo in its properties, if it is not already present.

### ADJBPM Limitations

<i><b>Adjustments of 0 are not possible.</b></i>

- Due to the mechanics of this code - I partially blame the limited Live/ClyphX API, as well as perhaps my coding skill limits - The adjustment cannot be set to zero, so if you try and move the tempo back to the same tempo as the current scene's tempo, you may notice the next scene's adjusted BPM is unexpected.

- In this case, it is better to either move the tempo to very close to the scene's tempo (Even a fraction of one BPM away), or simply turn off ADJBPM until it is needed again.

<i><b>Action must be present on an xclip on any scene where adjustment is desired.</b></i>

- If `ADJBPM;` is not present on a specific scene, this scene will not be adjusted. If adjustment to all scene tempos is desired, the `ADDALL` command is the current workaround. 

Suggestions or implementations addressing these limitations from others are always welcome. As well as detailed reports of when the BPM does not adjust properly.

## Compatability

Tested with:

<b>Ableton Live Standard - 11.3.26 </b>

<b>ClyphX Pro - 1.3.0 </b>

## License

`InfluencerActions` was created by Brendan Krueger. It is licensed under the terms
of the MIT license.

## Credits

The author and maintainer of this module is Brendan Krueger aka <a href="http://digitalinfluencermusic.com">Digital Influencer</a>.