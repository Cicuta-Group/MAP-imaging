metadata = {
    'protocolName': 'Sample platform dilution series multipipette loading protocol',
    'author': 'Morten Kals <mk2018@cam.ac.uk>',
    'description': 'Protocol for loading sample platform with agarose pads containing concentrations gradients of constitents, such as antibiotic. Does not work for multiple constituents if their concentraion gradient does not match direction.',
    'apiLevel': '2.13',
}

from opentrons import protocol_api


''' 
Operation:
1. Load column 12 of sample platform with some of all required media for that row with p1000.
2. Add consituents.
3. Perform dilutions series.
4. Add rest of media to each row of column 12.
5. With p300, distribute from 12 to the other columns.
6. With p300, make dilution series for each column.

-> Ideal for 2d arrays.
-> Dilution series that stays in a single row.
-> Same media for a given row.
'''

TIP_300UL_STARTING_COL = '9'
MEDIA_SOURCE_COL = '1'
SAMPLE_PLATFORMS = [2,3,6]

# Group columns that can be pipetted together
TIP_COLS = [[12,11,10,9,8,7,6,5,4,3,2,1]] # all in one
# TIP_ROWS = [[12,11,10,9],[8,7,6,5],[4,3,2,1]] # new every fourth (3 changes)
# TIP_ROWS = [[1],[2],[3],[4],[5],[6],[7],[8],[9],[10],[11],[12]] # all with new tips
# TIP_ROWS = [[1,2,3,4,6,8], [5,7,9], [10,11,12]] # leakage test

HEATER_SHAKER_TEMPERATURE = 62
HEATER_TEMPERATURE = 85

SAMPLE_PLATFORM_NAME = 'MAP_96well_29ul'
VOLUME_PER_PAD = 32 # ul

LOAD_PLATFORM_ASPIRATE_VOLUME = 110
VOLUME_PER_MIXING_WELL = 140 # used to be 280
VOLUME_FOR_DILUTION_SERIES = VOLUME_PER_MIXING_WELL

MIXING_RATE = 10 # factor to multiply with aspirate/dispense rate during mixing operations
MIXING_REPETITIONS = 2
MIXING_VOLUME = 200


# check tips
ucol_column_groups = [[f'A{i}' for i in group] for group in TIP_COLS]
all_rows = [a for g in TIP_COLS for a in g] # make 1D
assert(len(all_rows) == 12 and all([i+1 in all_rows for i in range(12)]))


def run(protocol: protocol_api.ProtocolContext):
    protocol.comment(f'Picking up tips: p300 = A{TIP_300UL_STARTING_COL}')

    protocol.set_rail_lights(True)

    ucols = [protocol.load_labware(SAMPLE_PLATFORM_NAME, i) for i in SAMPLE_PLATFORMS]

    # can only have two pipettes loaded at the same time
    tiprack_300ul = protocol.load_labware('opentrons_96_tiprack_300ul', 11)

    temperature_module = protocol.load_module('temperature module gen2', 10)
    media_plate = temperature_module.load_labware('generic_48_wellplate_5000ul')
    
    heater_shaker_module = protocol.load_module('heaterShakerModuleV1', 4)
    mixing_rack = heater_shaker_module.load_labware('nest_96_wellplate_2ml_deep')
    heater_shaker_module.close_labware_latch()

    heater_shaker_module.set_target_temperature(HEATER_SHAKER_TEMPERATURE)
    temperature_module.start_set_temperature(HEATER_TEMPERATURE)

    p300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack_300ul])
    p300.starting_tip = tiprack_300ul.well(f'A{TIP_300UL_STARTING_COL}')

    # Load media from other sources
    mixing_well_all_rows = mixing_rack.rows()[0] # wells for row a
    mixing_well_dilution_series_rows = mixing_well_all_rows[:-1] # rows used for dilution series

    p300.flow_rate.blow_out = 2* 94 # µL/s

    media_source_well = media_plate[f'A{MEDIA_SOURCE_COL}']
    # 1) drop in source to wet tip, 2) double in first well for dilution series, 3..n) rest of wells
    media_destination_wells = [media_source_well] + mixing_well_all_rows[:1] + mixing_well_all_rows

    p300.pick_up_tip() # to make sure tip-setting is correct
    protocol.comment(f'Load media in {media_source_well}. Volume requred = {len(media_destination_wells)*VOLUME_PER_MIXING_WELL} uL')
    protocol.comment(f'Media in starting well for dilution series: {2*VOLUME_PER_MIXING_WELL} uL')
    protocol.pause()
    
    for dest in media_destination_wells: # drop in source to wet tip
        p300.aspirate(
            volume=VOLUME_PER_MIXING_WELL,
            location=media_source_well,
        )
        protocol.delay(seconds=1) # wait to enable liquid to fully flow into pipette

        p300.dispense(
            volume=VOLUME_PER_MIXING_WELL,
            location=dest,
            rate=MIXING_RATE,
        )
    p300.drop_tip() # make noise


    # Pause for manual loading of antibiotics
    p300.pick_up_tip()
    protocol.comment('Load antibiotics.')
    protocol.pause()
    
    # start by mixing antibiotic well / preping tip 
    for source, dest in zip(mixing_well_dilution_series_rows[:1] + mixing_well_dilution_series_rows, mixing_well_dilution_series_rows): # first is from 1 to 1 to prep tips
        p300.aspirate(
            volume=VOLUME_FOR_DILUTION_SERIES,
            location=source,
        )
        p300.dispense(
            volume=VOLUME_FOR_DILUTION_SERIES,
            location=dest,
            rate=MIXING_RATE,
        )
        p300.mix(
            repetitions=MIXING_REPETITIONS,
            volume=MIXING_VOLUME,
            location=dest,
            rate=MIXING_RATE,
        )
        p300.blow_out(dest)
    p300.drop_tip()


    # load platforms
    for column_group in ucol_column_groups:
        
        p300.pick_up_tip()

        # wet tip
        p300.aspirate(
            volume=LOAD_PLATFORM_ASPIRATE_VOLUME,
            location=mixing_rack[column_group[0]],
            rate=MIXING_RATE,
        )
        p300.dispense(
            volume=LOAD_PLATFORM_ASPIRATE_VOLUME,
            location=mixing_rack[column_group[0]],
            rate=MIXING_RATE,
        )

        for column in column_group:
            source = mixing_rack[column]
            destinations = [ucol[column] for ucol in ucols]

            p300.aspirate(
                volume=LOAD_PLATFORM_ASPIRATE_VOLUME, 
                location=source, 
            )
            
            protocol.delay(seconds=1) # wait to enable liquid to fully flow into pipette

            for dest in destinations: # distribute to all platforms
                p300.dispense(
                    volume=VOLUME_PER_PAD,
                    location=dest.top(),
                )
                
            p300.blow_out(location=source)
            p300.touch_tip(location=source)

        p300.drop_tip()


'''
Observations:
- Move up a bit on sample platform [done]
- Too much media removed during first step in dilution series [done]
- Try with less blow-out (especially for p300 pipette without filter)

128ug/ml antibiotic concentration.
Add x ul of 5mg/ml to get 300ul of 0.128ug/ml

'''

# opentrons_simulate opentrons/MAP_8x12_dilution_series.py -L opentrons/MAP_96well_29ul -L opentrons/generic_48_wellplate_5000ul -o nothing