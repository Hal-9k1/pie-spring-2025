from actuators import MotorConf
from actuators import SensorConf

spring_2025 = {
    'left_drive_motor': MotorConf(
        controller_id = '6_8847060420572259627',
        channel = 'a',
        invert = False,
        encoder_invert = False,
        internal_gearing = 30,
    ),
    'right_drive_motor': MotorConf(
        controller_id = '6_16448980913872547624',
        channel = 'b',
        invert = True,
        encoder_invert = False,
        internal_gearing = 30,
    ),
    'sensor': SensorConf(

    ),
}
