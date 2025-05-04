from devices import MotorConf
from devices import ServoConf
from devices import DistanceSensorConf


spring_2025 = {
    'left_drive_motor': MotorConf(
        controller_id = '6_12971397673606281690',
        channel = 'b',
        invert = False,
        encoder_invert = False,
        internal_gearing = 30,
    ),
    'right_drive_motor': MotorConf(
        controller_id = '6_16448980913872547624',
        channel = 'a',
        invert = True,
        encoder_invert = False,
        internal_gearing = 30,
    ),
    'belt_motor_left': MotorConf(
        controller_id = '6_12971397673606281690',
        channel = 'a',
        invert = False,
        encoder_invert = False,
        internal_gearing = 70,
    ),
    'belt_motor_right': MotorConf(
        controller_id = '6_16448980913872547624',
        channel = 'b',
        invert = True,
        encoder_invert = False,
        internal_gearing = 70,
    ),
    'front_belt_motor': MotorConf(
        controller_id = '6_12678443877197942159',
        channel = 'b',
        invert = False,
        encoder_invert = False,
        internal_gearing = 70,
    ),
    'button_pusher_servo': ServoConf(
        controller_id = '4_4907772656414335786',
        channel = '1',
    ),
    'sensor': DistanceSensorConf(
        device_id = '8_15421340692729207283',
        noise_threshold = 2,
    ),
}

spring_2024 = {

}
