# Represents logic for what to do when we are given an item from AP
import math
from enum import IntEnum

import random
from typing import List, Tuple

from apworld.toontown import ToontownItemName, get_item_def_from_id
from apworld.toontown.fish import LICENSE_TO_ACCESS_CODE
from otp.otpbase.OTPLocalizerEnglish import EmoteFuncDict
from toontown.archipelago.util import global_text_properties
from toontown.archipelago.util.global_text_properties import MinimalJsonMessagePart
from toontown.battle import BattleBase

from toontown.building import FADoorCodes
from toontown.coghq.CogDisguiseGlobals import PartsPerSuitBitmasks
from toontown.fishing import FishGlobals
from toontown.toonbase import ToontownBattleGlobals
from toontown.toonbase import ToontownGlobals
from toontown.toon import NPCToons
from toontown.chat import ResistanceChat

# Typing hack, can remove later
TYPING = False
if TYPING:
    from toontown.toon.DistributedToonAI import DistributedToonAI


class APReward:

    # Return a color formatted header to display in the on screen display, this should be overridden
    def formatted_header(self):
        return f"UNIMPLEMENTED REWARD STR:\n{self.__class__.__name__}"

    # Returns a color formatted footer so we don't have to call this ugly code a million times
    def _formatted_footer(self, player, isSelf=False):
        color = 'yellow' if not isSelf else 'magenta'
        name = player if not isSelf else "You"
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("\n\nFrom: "),
            MinimalJsonMessagePart(f"{name}", color=color)
        ])

    # Override to set an image path to show up on the display, assumes png and square shaped
    # If not overridden, will show the AP logo
    def get_image_path(self) -> str:
        return 'phase_14/maps/ap_icon.png'

    # Override to set the scale of an image you want to show up on the display
    def get_image_scale(self) -> float:
        return .08

    # Override to set the position of an image you want to show up on the display
    def get_image_pos(self):
        return (.12, 0, .1)

    # Returns a string to show on the display when received, should follow the basic format like so:
    # Your x is now y!\n\nFrom: {fromPlayer}
    def get_reward_string(self, fromPlayer: str, isSelf=False) -> str:
        return f"{self.formatted_header()}{self._formatted_footer(fromPlayer, isSelf)}"

    def apply(self, av: "DistributedToonAI"):
        raise NotImplementedError("Please implement the apply() method!")


class LaffBoostReward(APReward):
    def __init__(self, amount: int):
        self.amount = amount

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("Increased your\nmax laff by "),
            MinimalJsonMessagePart(f"+{self.amount}", color='green'),
            MinimalJsonMessagePart("!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        av.b_setMaxHp(av.maxHp + self.amount)
        av.toonUp(self.amount)


class GagCapacityReward(APReward):

    def __init__(self, amount: int):
        self.amount: int = amount

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("Increased your gag\npouch capacity by "),
            MinimalJsonMessagePart(f"+{self.amount}", color='green'),
            MinimalJsonMessagePart("!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        av.b_setMaxCarry(av.maxCarry + self.amount)


class JellybeanJarUpgradeReward(APReward):

    def __init__(self, amount: int):
        self.amount: int = amount

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("Increased your jellybean\njar capacity by "),
            MinimalJsonMessagePart(f"+{self.amount}", color='green'),
            MinimalJsonMessagePart("!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        av.b_setMaxMoney(av.maxMoney + self.amount)


class GagTrainingFrameReward(APReward):
    TOONUP = 0
    TRAP = 1
    LURE = 2
    SOUND = 3
    THROW = 4
    SQUIRT = 5
    DROP = 6

    TRACK_TO_NAME = {
        TOONUP: "Toon-Up",
        TRAP: "Trap",
        LURE: "Lure",
        SOUND: "Sound",
        THROW: "Throw",
        SQUIRT: "Squirt",
        DROP: "Drop",
    }

    TRACK_TO_COLOR = {
        TOONUP: 'slateblue',
        TRAP: 'yellow',
        LURE: 'green',
        SOUND: 'plum',
        THROW: 'yellow',  #  todo add a gold text property
        SQUIRT: 'slateblue',  # todo add a pinkish text property
        DROP: 'cyan'
    }

    TRACK_TO_ICON = {
        TOONUP: "toonup_%s",
        TRAP: "trap_%s",
        LURE: "lure_%s",
        SOUND: "sound_%s",
        THROW: "throw_%s",
        SQUIRT: "squirt_%s",
        DROP: "drop_%s",
    }

    def __init__(self, track):
        self.track = track

    # todo: find a way to show dynamic info based on what this reward did for us exactly
    # todo: new system was two steps forward one step back in this regard
    def formatted_header(self) -> str:
        track_name_color = self.TRACK_TO_COLOR.get(self.track)
        level = base.localAvatar.getTrackAccessLevel(self.track)
        # Check for organic text popup first
        if base.localAvatar.getTrackBonusLevel()[self.track] == 7:
            return global_text_properties.get_raw_formatted_string([
                MinimalJsonMessagePart("Received a training frame!\nYour "),
                MinimalJsonMessagePart(f"{self.TRACK_TO_NAME[self.track]}".upper(), color=track_name_color),
                MinimalJsonMessagePart(" Gags are now organic!"),
            ])
        # Check for new levels
        if level <= 7:
            return global_text_properties.get_raw_formatted_string([
                MinimalJsonMessagePart("Received a training frame!\nYour "),
                MinimalJsonMessagePart(f"{self.TRACK_TO_NAME[self.track]}".upper(), color=track_name_color),
                MinimalJsonMessagePart(" Gags have more potential!"),
                ])
        else:
            return global_text_properties.get_raw_formatted_string([
                MinimalJsonMessagePart("Received a training frame!\nYour "),
                MinimalJsonMessagePart(f"{self.TRACK_TO_NAME[self.track]}".upper(), color=track_name_color),
                MinimalJsonMessagePart(" experience can now overflow!"),
            ])

    def get_image_path(self) -> str:
        level = base.localAvatar.getTrackAccessLevel(self.track)
        ap_icon = self.TRACK_TO_ICON[(self.track)] % str(min(level, 7))
        return f'phase_14/maps/gags/{ap_icon}.png'

    def apply(self, av: "DistributedToonAI"):

        # Increment track access level by 1
        oldLevel = av.getTrackAccessLevel(self.track)
        newLevel = oldLevel + 1

        bonusArray = av.getTrackBonusLevel()

        # If we get a frame when we already maxed and can overflow, make the track organic. No need to do anything else
        if newLevel > 8:
            bonusArray[self.track] = 7
            av.b_setTrackBonusLevel(bonusArray)
            return

        # Before we do anything, we need to see if they were capped before this so we can award them gags later
        wasCapped = av.experience.getExp(self.track) == av.experience.getExperienceCapForTrack(self.track)
        # Edge case, we were not technically capped if we are unlocking the "overflow xp" mechanic
        if newLevel == 8:
            wasCapped = False

        # Otherwise increment the gag level allowed and make sure it is not organic
        av.setTrackAccessLevel(self.track, newLevel)
        bonusArray[self.track] = -1
        av.b_setTrackBonusLevel(bonusArray)

        # Consider the case where we just learned a new gag track, we should give them as many of them as possible
        if newLevel == 1:
            av.inventory.addItemsWithListMax([(self.track, 0)])
            av.b_setInventory(av.inventory.makeNetString())
        # Now consider the case where we were maxed previously and want to upgrade by giving 1 xp and giving new gags
        # This will also trigger the new gag check to unlock :3
        elif wasCapped:
            av.experience.addExp(track=self.track, amount=1)  # Give them enough xp to learn the gag :)
            av.b_setExperience(av.experience.getCurrentExperience())
            av.inventory.addItemsWithListMax([(self.track, newLevel-1)])  # Give the new gags!!
            av.b_setInventory(av.inventory.makeNetString())


class GagTrainingMultiplierReward(APReward):

    def __init__(self, amount: int):
        self.amount: int = amount

    # todo, again nice to have this tell us WHAT it is, not what we got
    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("Increased your global XP\nmultiplier by "),
            MinimalJsonMessagePart(f"+{self.amount}", color='green'),
            MinimalJsonMessagePart("!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        oldMultiplier = av.getBaseGagSkillMultiplier()
        newMultiplier = oldMultiplier + self.amount
        av.b_setBaseGagSkillMultiplier(newMultiplier)


class FishingRodUpgradeReward(APReward):

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("Your "),
            MinimalJsonMessagePart(f"Fishing Rod", color='plum'),
            MinimalJsonMessagePart("\nhas been upgraded!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        nextRodID = min(av.fishingRod + 1, FishGlobals.MaxRodId)

        av.b_setFishingRod(nextRodID)


class TeleportAccessUpgradeReward(APReward):
    TOONTOWN_CENTRAL = ToontownGlobals.ToontownCentral
    DONALDS_DOCK = ToontownGlobals.DonaldsDock
    DAISYS_GARDENS = ToontownGlobals.DaisyGardens
    MINNIES_MELODYLAND = ToontownGlobals.MinniesMelodyland
    THE_BRRRGH = ToontownGlobals.TheBrrrgh
    DONALDS_DREAMLAND = ToontownGlobals.DonaldsDreamland

    SELLBOT_HQ = ToontownGlobals.SellbotHQ
    CASHBOT_HQ = ToontownGlobals.CashbotHQ
    LAWBOT_HQ = ToontownGlobals.LawbotHQ
    BOSSBOT_HQ = ToontownGlobals.BossbotHQ

    ACORN_ACRES = ToontownGlobals.OutdoorZone
    GOOFY_SPEEDWAY = ToontownGlobals.GoofySpeedway

    LINKED_PGS = {ACORN_ACRES: [ToontownGlobals.GolfZone]}

    ZONE_TO_DISPLAY_NAME = {
        TOONTOWN_CENTRAL: "Toontown Central",
        DONALDS_DOCK: "Donald's Dock",
        DAISYS_GARDENS: "Daisy Gardens",
        MINNIES_MELODYLAND: "Minnie's Melodyland",
        THE_BRRRGH: "The Brrrgh",
        DONALDS_DREAMLAND: "Donald's Dreamland",
        SELLBOT_HQ: "Sellbot HQ",
        CASHBOT_HQ: "Cashbot HQ",
        LAWBOT_HQ: "Lawbot HQ",
        BOSSBOT_HQ: "Bossbot HQ",
        ACORN_ACRES: "Acorn Acres",
        GOOFY_SPEEDWAY: "Goofy Speedway",
    }

    def __init__(self, playground: int):
        self.playground: int = playground

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("You can now teleport\nto "),
            MinimalJsonMessagePart(f"{self.ZONE_TO_DISPLAY_NAME.get(self.playground, 'unknown zone: ' + str(self.playground))}", color='green'),
            MinimalJsonMessagePart("!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        av.addTeleportAccess(self.playground)
        for pg in self.LINKED_PGS.get(self.playground, []):
            av.addTeleportAccess(pg)


class TaskAccessReward(APReward):
    TOONTOWN_CENTRAL = ToontownGlobals.ToontownCentral
    DONALDS_DOCK = ToontownGlobals.DonaldsDock
    DAISYS_GARDENS = ToontownGlobals.DaisyGardens
    MINNIES_MELODYLAND = ToontownGlobals.MinniesMelodyland
    THE_BRRRGH = ToontownGlobals.TheBrrrgh
    DONALDS_DREAMLAND = ToontownGlobals.DonaldsDreamland

    ZONE_TO_DISPLAY_NAME = {
        TOONTOWN_CENTRAL: "Toontown Central",
        DONALDS_DOCK: "Donald's Dock",
        DAISYS_GARDENS: "Daisy Gardens",
        MINNIES_MELODYLAND: "Minnie's Melodyland",
        THE_BRRRGH: "The Brrrgh",
        DONALDS_DREAMLAND: "Donald's Dreamland",
    }

    def __init__(self, playground: int):
        self.playground: int = playground

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("You may now complete ToonTasks\nin "),
            MinimalJsonMessagePart(f"{self.ZONE_TO_DISPLAY_NAME.get(self.playground, 'unknown zone: ' + str(self.playground))}", color='green'),
            MinimalJsonMessagePart("!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        # Get the key ID for this playground
        key = FADoorCodes.ZONE_TO_ACCESS_CODE[self.playground]
        av.addAccessKey(key)


class FishingLicenseReward(APReward):
    TOONTOWN_CENTRAL = ToontownGlobals.ToontownCentral
    DONALDS_DOCK = ToontownGlobals.DonaldsDock
    DAISYS_GARDENS = ToontownGlobals.DaisyGardens
    MINNIES_MELODYLAND = ToontownGlobals.MinniesMelodyland
    THE_BRRRGH = ToontownGlobals.TheBrrrgh
    DONALDS_DREAMLAND = ToontownGlobals.DonaldsDreamland

    ZONE_TO_DISPLAY_NAME = {
        TOONTOWN_CENTRAL: "Toontown Central",
        DONALDS_DOCK: "Donald's Dock",
        DAISYS_GARDENS: "Daisy Gardens",
        MINNIES_MELODYLAND: "Minnie's Melodyland",
        THE_BRRRGH: "The Brrrgh",
        DONALDS_DREAMLAND: "Donald's Dreamland",
    }

    def __init__(self, playground: int):
        self.playground: int = playground

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("You may now Fish\nin "),
            MinimalJsonMessagePart(f"{self.ZONE_TO_DISPLAY_NAME.get(self.playground, 'unknown zone: ' + str(self.playground))}", color='green'),
            MinimalJsonMessagePart("!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        # Get the key ID for this playground
        key = LICENSE_TO_ACCESS_CODE[self.playground]
        av.addAccessKey(key)


class FacilityAccessReward(APReward):
    FACILITY_ID_TO_DISPLAY = {
        FADoorCodes.FRONT_FACTORY_ACCESS_MISSING: "Front Factory",
        FADoorCodes.SIDE_FACTORY_ACCESS_MISSING: "Side Factory",

        FADoorCodes.COIN_MINT_ACCESS_MISSING: "Coin Mint",
        FADoorCodes.DOLLAR_MINT_ACCESS_MISSING: "Dollar Mint",
        FADoorCodes.BULLION_MINT_ACCESS_MISSING: "Bullion Mint",

        FADoorCodes.OFFICE_A_ACCESS_MISSING: "Office A",
        FADoorCodes.OFFICE_B_ACCESS_MISSING: "Office B",
        FADoorCodes.OFFICE_C_ACCESS_MISSING: "Office C",
        FADoorCodes.OFFICE_D_ACCESS_MISSING: "Office D",

        FADoorCodes.FRONT_THREE_ACCESS_MISSING: "Front One",
        FADoorCodes.MIDDLE_SIX_ACCESS_MISSING: "Middle Two",
        FADoorCodes.BACK_NINE_ACCESS_MISSING: "Back Three",
    }

    def __init__(self, key):
        self.key = key

    def formatted_header(self) -> str:
        key_name = self.FACILITY_ID_TO_DISPLAY.get(self.key, f"UNKNOWN-KEY[{self.key}]")
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("You may now infiltrate\nthe "),
            MinimalJsonMessagePart(f"{key_name}", color='salmon'),
            MinimalJsonMessagePart(" facility!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        # Get the key ID for this playground
        av.addAccessKey(self.key)


class CogDisguiseReward(APReward):
    BOSSBOT = 0
    LAWBOT = 1
    CASHBOT = 2
    SELLBOT = 3

    ENUM_TO_NAME = {
        BOSSBOT: "Bossbot",
        LAWBOT: "Lawbot",
        CASHBOT: "Cashbot",
        SELLBOT: "Sellbot",
    }

    # When instantiating this, use the attributes defined above, i'm not here to fix shit toontown code
    def __init__(self, dept: int):
        self.dept: int = dept

    def formatted_header(self) -> str:
        dept = self.ENUM_TO_NAME[self.dept]
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("You were given\nyour "),
            MinimalJsonMessagePart(f"{dept} Disguise", color='plum'),
            MinimalJsonMessagePart("!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        parts = av.getCogParts()
        parts[self.dept] = PartsPerSuitBitmasks[self.dept]
        av.b_setCogParts(parts)


class JellybeanReward(APReward):

    def __init__(self, amount: int):
        self.amount: int = amount

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("You were given\n"),
            MinimalJsonMessagePart(f"+{self.amount} jellybeans", color='cyan'),
            MinimalJsonMessagePart("!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        av.addMoney(self.amount)


class UberTrapAward(APReward):

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("UBER TRAP\n", color='salmon'),
            MinimalJsonMessagePart(f"Don't get hit!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        newHp = 15 if av.getHp() > 15 else 1
        damage = av.getHp() - newHp
        if av.getHp() > 0:
            av.takeDamage(damage)
        av.inventory.maxInventory()
        av.b_setInventory(av.inventory.makeNetString())

        av.d_broadcastHpString("UBERFIED!", (.35, .7, .35))
        av.d_playEmote(EmoteFuncDict['Cry'], 1)


class DripTrapAward(APReward):

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("DRIP TRAP\n", color='salmon'),
            MinimalJsonMessagePart(f"Did someone say the door to drip?"),
        ])

    def apply(self, av: "DistributedToonAI"):
        av.playSound('phase_4/audio/sfx/avatar_emotion_drip.ogg')
        av.b_setShoes(1, random.randint(1, 48), 0)
        av.b_setBackpack(random.randint(1, 24), 0, 0)
        av.b_setGlasses(random.randint(1, 21), 0, 0)
        av.b_setHat(random.randint(1, 56), 0, 0)

        av.d_broadcastHpString("FASHION STATEMENT!", (.9, .8, .2))
        av.d_playEmote(EmoteFuncDict['Surprise'], 1)


class GagShuffleAward(APReward):

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("GAG SHUFFLE TRAP\n", color='salmon'),
            MinimalJsonMessagePart(f"Got gags?")
        ])

    def apply(self, av: "DistributedToonAI"):

        # Clear inventory, randomly choose gags and add them until we fill up
        av.inventory.calcTotalProps()  # Might not be necessary, but just to be safe
        target = av.inventory.totalProps
        av.inventory.clearInventory()  # Wipe inventory
        # Get allowed track level pairs
        allowedGags: List[Tuple[int, int]] = av.experience.getAllowedGagsAndLevels()
        # Only do enough attempts to fill us back up to what we were
        for _ in range(target):
            # Randomly select a gag and attempt to add it
            gag: Tuple[int, int] = random.choice(allowedGags)
            track, level = gag
            gagsAdded = av.inventory.addItem(track, level)

            # If this gag failed to add, we can no longer query for this gag. Remove it.
            if gagsAdded <= 0:
                allowedGags.remove(gag)

            # Edge case, if we are out of gags we need to stop (in theory this should never happen but let's be safe :p)
            if len(allowedGags) <= 0:
                break

        av.b_setInventory(av.inventory.makeNetString())
        av.d_broadcastHpString("GAG SHUFFLE!", (.3, .5, .8))
        av.d_playEmote(EmoteFuncDict['Confused'], 1)


class GagExpBundleAward(APReward):

    def __init__(self, amount: int):
        self.amount: int = amount

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("You were given a fill of\n"),
            MinimalJsonMessagePart(f"{self.amount}% experience", color='cyan'),
            MinimalJsonMessagePart(" in each Gag Track!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        for index, _ in enumerate(ToontownBattleGlobals.Tracks):
            currentCap = min(av.experience.getExperienceCapForTrack(index), ToontownBattleGlobals.regMaxSkill)
            exptoAdd = math.ceil(currentCap * (self.amount/100))
            av.experience.addExp(index, exptoAdd)
        av.b_setExperience(av.experience.getCurrentExperience())


class BossRewardAward(APReward):
    SOS = 0
    UNITE = 1
    PINK_SLIP = 2

    REWARD_TO_DISPLAY_STR = {
        SOS: "SOS Card",
        UNITE: "Unite",
        PINK_SLIP: "amount of Pink Slips",
    }

    def __init__(self, reward: int):
        self.reward: int = reward

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("You were given a\nrandom "),
            MinimalJsonMessagePart(f"{self.REWARD_TO_DISPLAY_STR[self.reward]}", color='cyan'),
            MinimalJsonMessagePart("!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        if self.reward == BossRewardAward.SOS:
            av.attemptAddNPCFriend(random.choice(NPCToons.npcFriendsMinMaxStars(3, 4)))
        elif self.reward == BossRewardAward.UNITE:
            uniteType = random.choice([ResistanceChat.RESISTANCE_TOONUP, ResistanceChat.RESISTANCE_RESTOCK])
            uniteChoice = random.choice(ResistanceChat.getItems(uniteType))
            av.addResistanceMessage(ResistanceChat.encodeId(uniteType, uniteChoice))
        elif self.reward == BossRewardAward.PINK_SLIP:
            slipAmount = random.randint(1, 2)
            av.addPinkSlips(slipAmount)


class ProofReward(APReward):
    class ProofType(IntEnum):
        SellbotBossFirstTime = 0
        CashbotBossFirstTime = 1
        LawbotBossFirstTime = 2
        BossbotBossFirstTime = 3

        def to_display(self):
            return {
                self.SellbotBossFirstTime: "First VP Defeated",
                self.CashbotBossFirstTime: "First CFO Defeated",
                self.LawbotBossFirstTime: "First CJ Defeated",
                self.BossbotBossFirstTime: "First CEO Defeated"
            }.get(self, f"Unknown Proof ({self.value})")

    def __init__(self, proofType: ProofType):
        self.proofType: ProofReward.ProofType = proofType

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("Proof Obtained!\n", color='green'),
            MinimalJsonMessagePart(f"{self.proofType.to_display()}"),
        ])

    def apply(self, av: "DistributedToonAI"):
        # todo keep track of these
        pass


class VictoryReward(APReward):

    def formatted_header(self) -> str:
        return global_text_properties.get_raw_formatted_string([
            MinimalJsonMessagePart("VICTORY!\n", color='green'),
            MinimalJsonMessagePart(f"You have completed your goal!"),
        ])

    def apply(self, av: "DistributedToonAI"):
        av.APVictory()


class UndefinedReward(APReward):

    def __init__(self, desc):
        self.desc = desc

    def apply(self, av: "DistributedToonAI"):
        av.d_setSystemMessage(0, f"Unknown AP reward: {self.desc}")


class IgnoreReward(APReward):

    def apply(self, av: "DistributedToonAI"):
        pass


ITEM_NAME_TO_AP_REWARD: [str, APReward] = {
    ToontownItemName.LAFF_BOOST_1.value: LaffBoostReward(1),
    ToontownItemName.LAFF_BOOST_2.value: LaffBoostReward(2),
    ToontownItemName.LAFF_BOOST_3.value: LaffBoostReward(3),
    ToontownItemName.LAFF_BOOST_4.value: LaffBoostReward(4),
    ToontownItemName.LAFF_BOOST_5.value: LaffBoostReward(5),
    ToontownItemName.GAG_CAPACITY_5.value: GagCapacityReward(5),
    ToontownItemName.GAG_CAPACITY_10.value: GagCapacityReward(10),
    ToontownItemName.GAG_CAPACITY_15.value: GagCapacityReward(15),
    ToontownItemName.MONEY_CAP_750.value: JellybeanJarUpgradeReward(750),
    ToontownItemName.MONEY_CAP_1000.value: JellybeanJarUpgradeReward(1000),
    ToontownItemName.MONEY_CAP_1250.value: JellybeanJarUpgradeReward(1250),
    ToontownItemName.MONEY_CAP_1500.value: JellybeanJarUpgradeReward(1500),
    ToontownItemName.MONEY_CAP_2000.value: JellybeanJarUpgradeReward(2000),
    ToontownItemName.MONEY_CAP_2500.value: JellybeanJarUpgradeReward(2500),
    ToontownItemName.TOONUP_FRAME.value: GagTrainingFrameReward(GagTrainingFrameReward.TOONUP),
    ToontownItemName.TRAP_FRAME.value: GagTrainingFrameReward(GagTrainingFrameReward.TRAP),
    ToontownItemName.LURE_FRAME.value: GagTrainingFrameReward(GagTrainingFrameReward.LURE),
    ToontownItemName.SOUND_FRAME.value: GagTrainingFrameReward(GagTrainingFrameReward.SOUND),
    ToontownItemName.THROW_FRAME.value: GagTrainingFrameReward(GagTrainingFrameReward.THROW),
    ToontownItemName.SQUIRT_FRAME.value: GagTrainingFrameReward(GagTrainingFrameReward.SQUIRT),
    ToontownItemName.DROP_FRAME.value: GagTrainingFrameReward(GagTrainingFrameReward.DROP),
    ToontownItemName.GAG_MULTIPLIER_1.value: GagTrainingMultiplierReward(1),
    ToontownItemName.GAG_MULTIPLIER_2.value: GagTrainingMultiplierReward(2),
    ToontownItemName.FISHING_ROD_UPGRADE.value: FishingRodUpgradeReward(),
    ToontownItemName.TTC_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.TOONTOWN_CENTRAL),
    ToontownItemName.DD_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.DONALDS_DOCK),
    ToontownItemName.DG_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.DAISYS_GARDENS),
    ToontownItemName.MML_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.MINNIES_MELODYLAND),
    ToontownItemName.TB_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.THE_BRRRGH),
    ToontownItemName.DDL_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.DONALDS_DREAMLAND),
    ToontownItemName.SBHQ_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.SELLBOT_HQ),
    ToontownItemName.CBHQ_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.CASHBOT_HQ),
    ToontownItemName.LBHQ_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.LAWBOT_HQ),
    ToontownItemName.BBHQ_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.BOSSBOT_HQ),
    ToontownItemName.AA_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.ACORN_ACRES),
    ToontownItemName.GS_TELEPORT.value: TeleportAccessUpgradeReward(TeleportAccessUpgradeReward.GOOFY_SPEEDWAY),
    ToontownItemName.TTC_HQ_ACCESS.value: TaskAccessReward(TaskAccessReward.TOONTOWN_CENTRAL),
    ToontownItemName.DD_HQ_ACCESS.value: TaskAccessReward(TaskAccessReward.DONALDS_DOCK),
    ToontownItemName.DG_HQ_ACCESS.value: TaskAccessReward(TaskAccessReward.DAISYS_GARDENS),
    ToontownItemName.MML_HQ_ACCESS.value: TaskAccessReward(TaskAccessReward.MINNIES_MELODYLAND),
    ToontownItemName.TB_HQ_ACCESS.value: TaskAccessReward(TaskAccessReward.THE_BRRRGH),
    ToontownItemName.DDL_HQ_ACCESS.value: TaskAccessReward(TaskAccessReward.DONALDS_DREAMLAND),
    ToontownItemName.TTC_FISHING.value: FishingLicenseReward(FishingLicenseReward.TOONTOWN_CENTRAL),
    ToontownItemName.DD_FISHING.value: FishingLicenseReward(FishingLicenseReward.DONALDS_DOCK),
    ToontownItemName.DG_FISHING.value: FishingLicenseReward(FishingLicenseReward.DAISYS_GARDENS),
    ToontownItemName.MML_FISHING.value: FishingLicenseReward(FishingLicenseReward.MINNIES_MELODYLAND),
    ToontownItemName.TB_FISHING.value: FishingLicenseReward(FishingLicenseReward.THE_BRRRGH),
    ToontownItemName.DDL_FISHING.value: FishingLicenseReward(FishingLicenseReward.DONALDS_DREAMLAND),
    ToontownItemName.FISH.value: IgnoreReward(),
    ToontownItemName.FRONT_FACTORY_ACCESS.value: FacilityAccessReward(FADoorCodes.FRONT_FACTORY_ACCESS_MISSING),
    ToontownItemName.SIDE_FACTORY_ACCESS.value: FacilityAccessReward(FADoorCodes.SIDE_FACTORY_ACCESS_MISSING),
    ToontownItemName.COIN_MINT_ACCESS.value: FacilityAccessReward(FADoorCodes.COIN_MINT_ACCESS_MISSING),
    ToontownItemName.DOLLAR_MINT_ACCESS.value: FacilityAccessReward(FADoorCodes.DOLLAR_MINT_ACCESS_MISSING),
    ToontownItemName.BULLION_MINT_ACCESS.value: FacilityAccessReward(FADoorCodes.BULLION_MINT_ACCESS_MISSING),
    ToontownItemName.A_OFFICE_ACCESS.value: FacilityAccessReward(FADoorCodes.OFFICE_A_ACCESS_MISSING),
    ToontownItemName.B_OFFICE_ACCESS.value: FacilityAccessReward(FADoorCodes.OFFICE_B_ACCESS_MISSING),
    ToontownItemName.C_OFFICE_ACCESS.value: FacilityAccessReward(FADoorCodes.OFFICE_C_ACCESS_MISSING),
    ToontownItemName.D_OFFICE_ACCESS.value: FacilityAccessReward(FADoorCodes.OFFICE_D_ACCESS_MISSING),
    ToontownItemName.FRONT_ONE_ACCESS.value: FacilityAccessReward(FADoorCodes.FRONT_THREE_ACCESS_MISSING),
    ToontownItemName.MIDDLE_TWO_ACCESS.value: FacilityAccessReward(FADoorCodes.MIDDLE_SIX_ACCESS_MISSING),
    ToontownItemName.BACK_THREE_ACCESS.value: FacilityAccessReward(FADoorCodes.BACK_NINE_ACCESS_MISSING),
    ToontownItemName.SELLBOT_DISGUISE.value: CogDisguiseReward(CogDisguiseReward.SELLBOT),
    ToontownItemName.CASHBOT_DISGUISE.value: CogDisguiseReward(CogDisguiseReward.CASHBOT),
    ToontownItemName.LAWBOT_DISGUISE.value: CogDisguiseReward(CogDisguiseReward.LAWBOT),
    ToontownItemName.BOSSBOT_DISGUISE.value: CogDisguiseReward(CogDisguiseReward.BOSSBOT),
    ToontownItemName.MONEY_250.value: JellybeanReward(250),
    ToontownItemName.MONEY_500.value: JellybeanReward(500),
    ToontownItemName.MONEY_1000.value: JellybeanReward(1000),
    ToontownItemName.MONEY_2000.value: JellybeanReward(2000),
    ToontownItemName.XP_10.value: GagExpBundleAward(10),
    ToontownItemName.XP_15.value: GagExpBundleAward(15),
    ToontownItemName.XP_20.value: GagExpBundleAward(20),
    ToontownItemName.SOS_REWARD.value: BossRewardAward(BossRewardAward.SOS),
    ToontownItemName.UNITE_REWARD.value: BossRewardAward(BossRewardAward.UNITE),
    ToontownItemName.PINK_SLIP_REWARD.value: BossRewardAward(BossRewardAward.PINK_SLIP),
    ToontownItemName.UBER_TRAP.value: UberTrapAward(),
    ToontownItemName.DRIP_TRAP.value: DripTrapAward(),
    ToontownItemName.GAG_SHUFFLE_TRAP.value: GagShuffleAward(),
}


def get_ap_reward_from_name(name: str) -> APReward:
    return ITEM_NAME_TO_AP_REWARD.get(name, UndefinedReward(name))


# The id we are given from a packet from archipelago
def get_ap_reward_from_id(_id: int) -> APReward:
    definition = get_item_def_from_id(_id)

    if not definition:
        return UndefinedReward(_id)

    ap_reward: APReward = ITEM_NAME_TO_AP_REWARD.get(definition.name.value)

    if not ap_reward:
        ap_reward = UndefinedReward(definition.name.value)

    return ap_reward


# Wrapper class for APReward that holds not only the APReward, but also additional attributes such as:
# - index reward was received
# - item ID of the Archipelago item
# - Name of the player who got this reward for us
class EarnedAPReward:

    def __init__(self, av, reward: APReward, rewardIndex: int, itemId: int, fromName: str, isLocal: bool):
        self.av = av
        self.reward = reward
        self.rewardIndex = rewardIndex
        self.itemId = itemId
        self.fromName = fromName
        self.isLocal = isLocal

    def apply(self):
        self.reward.apply(self.av)  # Actually give the effects
        self.av.d_showReward(self.itemId, self.fromName, self.isLocal)  # Display the popup to the client
